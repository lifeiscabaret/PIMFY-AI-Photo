import torch
if not hasattr(torch, 'xpu'):
    # cache, count, seed에 대응 가능한 가짜 객체
    torch.xpu = type('XPU', (), {
        'empty_cache': lambda: None, 
        'device_count': lambda: 0, 
        'manual_seed': lambda x: None
    })
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import io
import base64
from typing import Optional
from PIL import Image
import numpy as np
from diffusers import StableDiffusionXLImg2ImgPipeline # 추가됨

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
    print("🚀 SDXL AI 모델 로딩 시작...")
    # 더미 탈출: 실제 모델 로드
    models["sdxl_pipe"] = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-refiner-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    ).to(device)
    print("✅ SDXL 로드 완료.")

@app.post("/generate/background", response_model=BackgroundResponse)
async def generate_background_api(request: BackgroundRequest):
    try:
        image_data = base64.b64decode(request.base64_dog_image)
        dog_image = Image.open(io.BytesIO(image_data)).convert("RGB") # SDXL은 RGB 권장
    except:
        raise HTTPException(status_code=400, detail="Invalid Base64 image data")

    # 변수 정의 추가
    final_prompt = f"Professional studio background, {request.color_hint}, {request.prompt}, high resolution, 8k"
    
    # 실제 SDXL 추론 실행
    generated_output = models["sdxl_pipe"](
        prompt=final_prompt,        
        negative_prompt=request.neg_prompt,
        image=dog_image,
        strength=0.85
    ).images[0]

    buffered = io.BytesIO() # 추가됨
    generated_output.save(buffered, format="PNG")
    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return BackgroundResponse(base64_background_image=base64_img)

# --- 여기서부터 새로 추가/수정하는 부분입니다 ---
if __name__ == "__main__":
    import uvicorn
    
    # 1. 서버가 뜨기 전에 모델 로딩 함수를 강제로 먼저 실행!
    print("⏳ 서버 시작 전 모델 로딩을 강제 실행합니다...")
    load_models() 
    
    # 2. 모델 로딩이 성공하면 그때 서버를 시작합니다.
    print("🚀 모든 준비 완료. 서버를 시작합니다.")
    uvicorn.run(app, host="0.0.0.0", port=8001)
