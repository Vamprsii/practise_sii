from ultralytics import YOLO
import cv2
from PIL import Image
import time
from typing import NamedTuple
import os


class ImageDetectionResult(NamedTuple):
    image: Image.Image
    count: int
    processing_time: float


class VideoDetectionResult(NamedTuple):
    video_path: str
    count: int
    processing_time: float


# Загрузка модели
model = YOLO('yolov8n.pt')


def detect_giraffes(image_path: str) -> ImageDetectionResult:
    start_time = time.time()
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read image")

    results = model(img)
    giraffe_count = 0

    for result in results:
        for box in result.boxes:
            if model.names[int(box.cls)] == 'giraffe':
                giraffe_count += 1

    plotted_img = results[0].plot()
    plotted_img_rgb = cv2.cvtColor(plotted_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(plotted_img_rgb)

    return ImageDetectionResult(
        image=pil_img,
        count=giraffe_count,
        processing_time=round(time.time() - start_time, 2)
    )


def process_video(video_path: str) -> VideoDetectionResult:
    start_time = time.time()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Could not open video file")

    # Получаем параметры видео
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Создаём VideoWriter с правильными параметрами
    output_filename = f"result_{os.path.basename(video_path)}"
    output_path = os.path.join("static/results", output_filename)

    fourcc = cv2.VideoWriter_fourcc(*'avc1')

    out = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (frame_width, frame_height),
        isColor=True
    )

    total_giraffes = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Детекция объектов
        results = model(frame)

        # Подсчёт жирафов
        frame_giraffes = sum(1 for result in results
                             for box in result.boxes
                             if model.names[int(box.cls)] == 'giraffe')

        if frame_giraffes > total_giraffes:
            total_giraffes = frame_giraffes

        # Визуализация результатов
        plotted_frame = results[0].plot()
        out.write(plotted_frame)

    cap.release()
    out.release()

    if not is_video_playable(output_path):
        convert_video(output_path)

    return VideoDetectionResult(
        video_path=output_path,
        count=total_giraffes,
        processing_time=round(time.time() - start_time, 2)
    )


def is_video_playable(video_path: str) -> bool:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False
    cap.release()
    return True


def convert_video(input_path: str):
    output_path = input_path.replace('.mp4', '_converted.mp4')
    os.system(f'ffmpeg -i {input_path} -c:v libx264 -profile:v high -pix_fmt yuv420p -c:a aac {output_path}')
    os.replace(output_path, input_path)