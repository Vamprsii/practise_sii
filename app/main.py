import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uuid
from pathlib import Path

from app.detection import detect_giraffes, process_video
from .database import save_to_history, get_history, generate_report, clear_history
from .models import DetectionResult

app = FastAPI(title="Giraffe Tracker System")

# Настройка статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Создание директорий
Path("static/uploads").mkdir(parents=True, exist_ok=True)
Path("static/results").mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    history_data = get_history(limit=5)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history_data
    })


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{file_ext}"

        is_video = file_ext in ['mp4', 'avi', 'mov', 'mkv']
        file_path = f"static/uploads/{filename}"

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Обработка файла
        if is_video:
            result = process_video(file_path)
            result_filename = os.path.basename(result.video_path)
        else:
            result = detect_giraffes(file_path)
            result_filename = f"result_{filename}"
            result.image.save(f"static/results/{result_filename}")

        detection_result = DetectionResult(
            original_image=filename,
            processed_image=result_filename,
            giraffe_count=result.count,
            processing_time=result.processing_time,
            is_video=is_video
        )
        save_to_history(detection_result)

        return JSONResponse({
            "status": "success",
            "original": filename,
            "processed": result_filename,
            "count": result.count,
            "processing_time": result.processing_time,
            "is_video": is_video
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/history")
async def history(request: Request, partial: bool = False):
    history_data = get_history()
    if partial:
        return templates.TemplateResponse("_history_partial.html", {
            "request": request,
            "history": history_data,
            "show_full_history": True
        })
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history_data,
        "show_full_history": True
    })


@app.post("/clear_history")
async def clear_history_endpoint():
    try:
        clear_history()
        return JSONResponse({"status": "success", "message": "History cleared"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/report/{report_type}")
async def generate_report_endpoint(report_type: str):
    report_path = generate_report(report_type)
    if report_path:
        return FileResponse(
            report_path,
            media_type="application/octet-stream",
            filename=os.path.basename(report_path)
        )
    return JSONResponse({"status": "error", "message": "Report generation failed"})