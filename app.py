# app.py (simple + stable + fast)

import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import shutil
from PIL import Image
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.getenv("STABILITY_KEY")  # You will set this


def extract_dominant_color(image_path):
    img = Image.open(image_path).convert("RGB").resize((50,50))
    colors = img.getcolors(50*50)
    colors.sort(key=lambda x: x[0], reverse=True)
    return colors[0][1]  # RGB tuple


@app.post("/generate")
async def generate(
    prompt: str = Form(...),
    style_images: list[UploadFile] = File(None),
):
    if not style_images:
        return {"error": "Upload at least one style image"}

    saved_paths = []
    for f in style_images:
        name = f"{uuid.uuid4().hex}.jpg"
        path = f"uploads/{name}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        saved_paths.append(path)

    # pick first style image
    main_style = saved_paths[0]
    r, g, b = extract_dominant_color(main_style)

    # modify prompt to add color condition
    style_prompt = f"{prompt}, color tones of rgb({r},{g},{b}), artistic, aesthetic, cinematic"

    url = "https://api.stability.ai/v2beta/stable-image/generate/core"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "image/*",
    }

    data = {
        "prompt": style_prompt
    }

    response = requests.post(
        url,
        headers=headers,
        files={"none": ""},
        data=data,
    )

    if response.status_code != 200:
        return {"error": response.text}

    out_name = f"out_{uuid.uuid4().hex}.png"
    out_path = f"static/{out_name}"

    with open(out_path, "wb") as f:
        f.write(response.content)

    return {"output_image": f"/static/{out_name}"}
