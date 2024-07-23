import json
from channels.generic.websocket import AsyncWebsocketConsumer
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

# 전역적으로 모델 로드
model = hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4")

class PostureConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            frame_data = json.loads(text_data)
            frame = np.array(frame_data['frame'], dtype=np.uint8).reshape(frame_data['shape'])

            
            keypoints = await self.detect_pose(frame)
            posture_status = self.check_posture(keypoints)

            await self.send(text_data=json.dumps({
                'posture': posture_status,
                'keypoints': keypoints.tolist()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def detect_pose(self, image):
        input_image = tf.image.resize_with_pad(image, 192, 192)
        input_image = tf.expand_dims(input_image, axis=0)
        input_image = tf.cast(input_image, dtype=tf.int32)

        outputs = model(input_image)
        keypoints = outputs['output_0'].numpy()
        if len(keypoints.shape) == 3:
            keypoints = keypoints[0]
        return keypoints

    def check_posture(self, keypoints, confidence_threshold=0.3):
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
