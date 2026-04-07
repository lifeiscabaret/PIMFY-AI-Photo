import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import io
import base64
from typing import Optional
from PIL import Image
from diffusers import AutoPipelineForImage2Image

class BackgroundRequest(BaseModel):
    base64_dog_image: str
    prompt: str
    neg_prompt: Optional[str] = None
    color_hint: str = "soft pastel"

class BackgroundResponse(BaseModel):
    base64_background_image: str

app = FastAPI(title="SDXL Background Service")
models = {}

@app.on_event("startup")
def load_models():
    print("🚀 SDXL-Turbo 모델 로딩 시작...")
    pipe = AutoPipelineForImage2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16"
    )
    pipe = pipe.to("cuda")
    models["sdxl_pipe"] = pipe
    print("✅ SDXL-Turbo 로드 완료")

@app.post("/generate/background", response_model=BackgroundResponse)
async def generate_background_api(request: BackgroundRequest):
    try:
        image_data = base64.b64decode(request.base64_dog_image)
        dog_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        dog_image = dog_image.resize((512, 512))
    except:
        raise HTTPException(status_code=400, detail="Invalid Base64 image data")

    final_prompt = f"Professional studio background, {request.color_hint}, {request.prompt}, high resolution"
    
    generated_output = models["sdxl_pipe"](
        prompt=final_prompt,
        image=dog_image,
        num_inference_steps=4,
        strength=0.5,
        guidance_scale=0.0
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
