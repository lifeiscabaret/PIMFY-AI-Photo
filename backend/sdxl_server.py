import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import io
import base64
from typing import Optional
from PIL import Image
import numpy as np
from diffusers import StableDiffusionXLImg2ImgPipeline

class BackgroundRequest(BaseModel):
    base64_dog_image: str
    prompt: str
    neg_prompt: Optional[str] = "messy, cluttered, text, letters, blurry, dark, noisy, low quality"
    color_hint: str = "soft pastel"

class BackgroundResponse(BaseModel):
    base64_background_image: str

app = FastAPI(title="SDXL Background Service")
models = {}
device = "cuda" if torch.cuda.is_available() else "cpu"

@app.on_event("startup")
def load_models():
    print(f"🚀 SDXL AI 모델 로딩 시작... device: {device}")
    
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-refiner-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    )
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_tiling()
    models["sdxl_pipe"] = pipe
    print("✅ SDXL 로드 완료")

@app.post("/generate/background", response_model=BackgroundResponse)
async def generate_background_api(request: BackgroundRequest):
    try:
        image_data = base64.b64decode(request.base64_dog_image)
        dog_image = Image.open(io.BytesIO(image_data)).convert("RGB")
    except:
        raise HTTPException(status_code=400, detail="Invalid Base64 image data")

    final_prompt = f"Professional studio background, {request.color_hint}, {request.prompt}, high resolution, 8k"
    
    generated_output = models["sdxl_pipe"](
        prompt=final_prompt,
        negative_prompt=request.neg_prompt,
        image=dog_image,
        strength=0.85
    ).images[0]

    buffered = io.BytesIO()
    generated_output.save(buffered, format="PNG")
    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    return BackgroundResponse(base64_background_image=base64_img)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
