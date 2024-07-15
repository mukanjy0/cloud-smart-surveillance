import cv2

def save_frames(video_path, frames_path):
    video_capture = cv2.VideoCapture(video_path)
    
    if not video_capture.isOpened():
      raise ValueError(f"Could not open video {video_path}")
    
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    for frame_number in range(total_frames):
      video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
      success, frame = video_capture.read()
      image_path = f'{frames_path}/{frame_number}.jpg'
      cv2.imwrite(image_path, frame)

    video_capture.release()
    
    if not success:
      raise ValueError(f"Could not read frame {frame_number}")
    
    return frame

video_path = './video'
frames_path = './images'
save_frames(video_path, frames_path)