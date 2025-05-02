from pydantic import BaseModel

class DetectionResult(BaseModel):
    original_image: str
    processed_image: str
    giraffe_count: int
    processing_time: float

class VideoDetectionResult(BaseModel):
    original_video: str
    processed_video: str
    total_giraffes: int
    processing_time: float
    avg_giraffes_per_frame: float
    max_giraffes_in_frame: int

class DetectionInput(BaseModel):
    image_path: str
    camera_mode: bool = False

class DetectionResponse(BaseModel):
    status: str
    original: str
    processed: str
    count: int
    processing_time: float
    file_type: str = "image"
    avg_giraffes_per_frame: float = None
    max_giraffes_in_frame: int = None