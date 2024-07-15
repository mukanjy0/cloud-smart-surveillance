import os
import cv2
import shutil

def save_frames(video_path, frames_path):
    video_capture = cv2.VideoCapture(video_path)
    
    if not video_capture.isOpened():
      raise ValueError(f"Could not open video {video_path}")
    
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if os.path.exists(frames_path):
        shutil.rmtree(frames_path)
    
    os.makedirs(frames_path)

    i = 0
    for frame_number in range(0, 12001, 50):
      video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
      success, frame = video_capture.read()
      image_path = f'{frames_path}/{i}.jpg'
      cv2.imwrite(image_path, frame)
      i += 1

    video_capture.release()
    
    if not success:
      raise ValueError(f"Could not read frame {frame_number}")
    
    return frame

video_path = 'video.mp4'
frames_path = 'frames'
save_frames(video_path, frames_path)