from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import base64
from django.core.files.base import ContentFile
import os
import glob
from PIL import Image as PILImage
from io import BytesIO

import pandas as pd
from .forms import AttendeeForm
from core.models import Event, Image, Attendees, FaceRecognition
import mediapipe as mp
from deepface import DeepFace
import cv2
import numpy as np

def enter_name(request):
    if request.method == 'POST':
        form = AttendeeForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['username']
            form.save()
            return redirect(reverse('camera_capture') + f'?name={name}')
    else:
        form = AttendeeForm()
    return render(request, 'UserLogin.html', {'form': form})

@csrf_exempt
def camera_capture(request):
    name = request.GET.get('name')
    if request.method == 'POST':
        frame_data = request.POST.get('frame')
        format, imgstr = frame_data.split(';base64,')
        ext = format.split('/')[-1]
        imgdata = base64.b64decode(imgstr)
        frame = np.frombuffer(imgdata, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        left_tilt_detected = leftConfirmation(frame)
        right_tilt_detected = rightConfirmation(frame)

        if left_tilt_detected and right_tilt_detected:
            image_instance = Image.objects.create(image=ContentFile(imgdata, name=f'{name}.{ext}'))
            attendee = Attendees.objects.get(username=name)
            FaceRecognition.objects.create(user=attendee, image=image_instance)
            return redirect('capture_face', name=name)
        else:
            return JsonResponse({'left_tilt': left_tilt_detected, 'right_tilt': right_tilt_detected})

    return render(request, 'captureCamera.html', {'name': name})

def capture_face(request, name):
    # Retrieve the Attendees instance based on the provided name
    attendee = get_object_or_404(Attendees, username=name)
    
    if request.method == 'POST':
        # Process captured face and save to database
        image_data = request.POST.get('image')
        
        # Decode base64 image data
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        imgdata = base64.b64decode(imgstr)
        
        # Create PIL image from decoded data
        pil_image = PILImage.open(BytesIO(imgdata))
        
        # Save PIL image to Django's ContentFile
        image_file = ContentFile(imgdata, name=f'{name}.{ext}')
        
        # Retrieve the associated event based on the provided PIN code
        pin_code = request.POST.get('pin_code')
        event = get_object_or_404(Event, pin_code=pin_code)
        
        # Create Image instance and save to database
        image_instance = Image.objects.create(image=image_file, event=event)
        
        # Create FaceRecognition instance and save to database
        face_recognition = FaceRecognition(user=attendee, image=image_instance)
        face_recognition.save()
        
        # Redirect to process_face view with query parameters
        return redirect(reverse('process_face') + f'?image={image_instance.id}&pin_code={pin_code}')
    
    # Render the capture_face HTML template
    return render(request, 'capture_face.html')


def get_event_photo_paths(pin_code):
    try:
        # Retrieve the event associated with the provided PIN code
        event = Event.objects.get(pin_code=pin_code)
    except Event.DoesNotExist:
        # Handle the case where no event is found for the provided PIN code
        return []

    # Construct the file path for event photos
    event_photo_path = os.path.join('eventImages', str(event.id))

    # Query the Image model to retrieve file paths of event photos
    event_photo_paths = Image.objects.filter(event=event).values_list('image', flat=True)

    # Append the event photo path to each image file path
    full_event_photo_paths = [os.path.join(event_photo_path, image_path) for image_path in event_photo_paths]

    return full_event_photo_paths


def process_face(request):
    if request.method == 'POST':
        img_path = request.POST.get('image')
        pin_code = request.POST.get('pin_code')

        if not img_path or not pin_code:
            return JsonResponse({'error': 'Missing image or pin_code'}, status=400)

        db_path = get_event_photo_paths(pin_code)
        if not db_path:
            return JsonResponse({'error': 'Event not found for the provided pin_code'}, status=404)

        try:
            matched_images = perform_face_recognition(img_path, db_path)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        request.session['matched_images'] = matched_images
        return redirect('matched_images')

    elif request.method == 'GET':
        img_path = request.GET.get('image')
        pin_code = request.GET.get('pin_code')

        if not img_path or not pin_code:
            return JsonResponse({'error': 'Missing image or pin_code'}, status=400)

        db_path = get_event_photo_paths(pin_code)
        if not db_path:
            return JsonResponse({'error': 'Event not found for the provided pin_code'}, status=404)

        try:
            matched_images = perform_face_recognition(img_path, db_path)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        request.session['matched_images'] = matched_images
        return redirect('matched_images')

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def perform_face_recognition(img_path, db_paths):
    for file in glob.glob(os.path.join(db_paths, 'ds_model*')):
        os.remove(file)
    dfs = DeepFace.find(img_path=img_path, db_path=db_paths, model_name='VGG-Face', enforce_detection=False, detector_backend='mtcnn')
    if isinstance(dfs, list):
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    elif isinstance(dfs, pd.DataFrame):
        df = dfs
    else:
        raise ValueError("The object returned by DeepFace.find is neither a DataFrame nor a list of DataFrames.")

    # Filter matches based on a distance threshold
    threshold = 0.5
    matches = df[df['distance'] <= threshold].drop_duplicates(subset='identity')

    # Function to process image with bounding boxes for identified faces
    def process_image_with_identified_faces(image_path, target_feature):
        img = cv2.imread(image_path)
        faces = DeepFace.extract_faces(img_path=image_path, detector_backend='mtcnn', enforce_detection=False, align=False)

        for face_info in faces:
            if isinstance(face_info, dict) and 'embedding' in face_info and 'facial_area' in face_info:
                face_feature = np.array(face_info['embedding'])
                distance = np.linalg.norm(face_feature - target_feature)
                if distance <= threshold:
                    face_location = face_info['facial_area']
                    left = face_location['x']
                    top = face_location['y']
                    right = left + face_location['w']
                    bottom = top + face_location['h']
                    cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 0), 2)

        return img

    # Extract the feature of the target image
    target_feature = DeepFace.represent(img_path=img_path, model_name='VGG-Face', enforce_detection=False)[0]['embedding']
    target_feature = np.array(target_feature)

    # List to store processed images
    processed_images = []

    # Iterate through the matched images and process them with bounding boxes
    for index, row in matches.iterrows():
        image_path = row['identity']
        processed_image = process_image_with_identified_faces(image_path, target_feature)
        processed_images.append(processed_image)

    return processed_images


def matched_images_view(request):
    matched_images = request.session.get('matched_images', [])
    return render(request, 'matched_images.html', {'matched_images': matched_images})


def confirmation(frame):
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)
    rightEar, noseMid, leftEar = 323, 4, 93
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            if noseMid < len(face_landmarks.landmark):
                rightEarX = int(face_landmarks.landmark[rightEar].x * frame.shape[1])
                leftEarX = int(face_landmarks.landmark[leftEar].x * frame.shape[1])
                noseX = int(face_landmarks.landmark[noseMid].x * frame.shape[1])
                return noseX, leftEarX, rightEarX
    return None, None, None

def leftConfirmation(frame):
    noseX, leftEarX, _ = confirmation(frame)
    return noseX < leftEarX if noseX is not None and leftEarX is not None else False

def rightConfirmation(frame):
    noseX, _, rightEarX = confirmation(frame)
    return noseX > rightEarX if noseX is not None and rightEarX is not None else False

def process_face(request):
    pass