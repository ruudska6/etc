from django.shortcuts import render
from django.http import StreamingHttpResponse, HttpResponse
import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

model = hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4")

def detect_pose(image):
    input_image = tf.image.resize_with_pad(image, 192, 192)
    input_image = tf.expand_dims(input_image, axis=0)
    input_image = tf.cast(input_image, dtype=tf.int32)
    outputs = model.signatures['serving_default'](input_image)
    keypoints = outputs['output_0'][0].numpy()
    if len(keypoints.shape) == 3:
        keypoints = keypoints[0]
    return keypoints

def draw_keypoints(image, keypoints, confidence_threshold=0.3):
    y, x, _ = image.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))
    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > confidence_threshold:
            cv2.circle(image, (int(kx), int(ky)), 6, (0, 255, 0), -1)
    return image

def check_posture(keypoints, confidence_threshold=0.3):
    if keypoints.shape[0] != 17:
        return "Error: Unexpected keypoints shape"
    left_shoulder = keypoints[5]
    right_shoulder = keypoints[6]
    nose = keypoints[0]
    if (left_shoulder[2] > confidence_threshold and 
        right_shoulder[2] > confidence_threshold and 
        nose[2] > confidence_threshold):
        shoulder_center_x = (left_shoulder[1] + right_shoulder[1]) / 2
        if nose[1] < shoulder_center_x:
            return "자세를 고쳐 앉으세요"
    return "좋은 자세입니다"

latest_frame = None

def gen():
    global latest_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break
        latest_frame = frame.copy()
        keypoints = detect_pose(frame)
        annotated_frame = draw_keypoints(frame, keypoints)
        
        _, jpeg = cv2.imencode('.jpg', annotated_frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    cap.release()

def get_latest_frame():
    global latest_frame
    return latest_frame

def get_posture_status(request):
    frame = get_latest_frame()
    if frame is not None:
        keypoints = detect_pose(frame)
        posture_status = check_posture(keypoints)
        return HttpResponse(posture_status)
    return HttpResponse("Error: No frame available")

def video_feed(request):
    return StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    return render(request, 'webcam/index.html')
