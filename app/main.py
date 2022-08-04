import io
import pathlib
import uuid
import pytesseract
from functools import lru_cache
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile,
)
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings
from PIL import Image


class Settings(BaseSettings):
    debug: bool = False
    echo_active: bool = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
DEBUG = settings.debug

BASE_DIR = pathlib.Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def home_view(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse("home.html", {"request": request, "data": 123})


@app.post("/")
async def ocr_prediction_view(file: UploadFile = File(...)):
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original": preds}


@app.post("/img-view/", response_class=FileResponse)
async def img_view(file: UploadFile = File(...),
                   settings: Settings = Depends(get_settings)):
    if not settings.echo_active:
        raise HTTPException(detail="Invalid endpoint", status_code=400)
    UPLOADS_DIR.mkdir(exist_ok=True)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    f_name = pathlib.Path(file.filename)
    f_ext = f_name.suffix
    f_dest = UPLOADS_DIR / f"{uuid.uuid1()}{f_ext}"
    img.save(f_dest)
    return f_dest
