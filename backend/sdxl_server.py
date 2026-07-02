from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import io
import base64
import random
from typing import Optional
from PIL import Image, ImageDraw, ImageFilter
import math

class BackgroundRequest(BaseModel):
    base64_dog_image: str
    prompt: str
    neg_prompt: Optional[str] = None
    color_hint: str = "soft pastel"

class BackgroundResponse(BaseModel):
    base64_background_image: str

app = FastAPI(title="Background Service")

# 색상 팔레트 - 분위기별
COLOR_PALETTES = {
    "warm": [(255, 243, 226)],
    "cool": [(214, 234, 255)],
    "pink": [(255, 214, 228)],
    "mint": [(198, 247, 228)],
    "lavender": [(225, 214, 255)],
    "cream": [(255, 248, 220)],
    "peach": [(255, 224, 204)],
}

def get_palette_from_hint(hint: str):
    hint = hint.lower()
    if any(w in hint for w in ["pink", "핑크", "girl", "여"]):
        return COLOR_PALETTES["pink"]
    elif any(w in hint for w in ["blue", "cool", "남", "boy"]):
        return COLOR_PALETTES["cool"]
    elif any(w in hint for w in ["mint", "green", "활발"]):
        return COLOR_PALETTES["mint"]
    elif any(w in hint for w in ["purple", "lavender", "순둥"]):
        return COLOR_PALETTES["lavender"]
    elif any(w in hint for w in ["warm", "orange", "에너지"]):
        return COLOR_PALETTES["warm"]
    elif any(w in hint for w in ["peach", "복숭아"]):
        return COLOR_PALETTES["peach"]
    else:
        return random.choice(list(COLOR_PALETTES.values()))

def create_gradient_background(width: int, height: int, colors: list) -> Image.Image:
    color = colors[0]
    return Image.new("RGB", (width, height), color)

def add_decorative_elements(img: Image.Image, colors: list) -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    accent = tuple(max(0, c - 30) for c in colors[0])
    
    # 우상단 원형 장식
    for i in range(3):
        r = 80 - i * 20
        alpha = 40 - i * 10
        circle_color = accent + (alpha,)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.ellipse([w - r*2 - 20 + i*10, -r + i*10, w - 20 + i*10, r + i*10], 
                            fill=(*accent, 30 - i*8))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    
    # 좌하단 원형 장식
    draw = ImageDraw.Draw(img)
    for i in range(3):
        r = 60 - i * 15
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.ellipse([-r + i*8, h - r*2 + i*8, r + i*8, h + i*8],
                            fill=(*accent, 25 - i*6))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    
    return img

@app.on_event("startup")
def startup():
    print("✅ Background Service 시작 완료 (PIL 모드)")

@app.post("/generate/background", response_model=BackgroundResponse)
async def generate_background_api(request: BackgroundRequest):
    try:
        image_data = base64.b64decode(request.base64_dog_image)
        dog_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        w, h = dog_image.size
    except:
        raise HTTPException(status_code=400, detail="Invalid Base64 image data")

    palette = get_palette_from_hint(request.color_hint + " " + request.prompt)
    
    background = create_gradient_background(w, h, palette)
    background = add_decorative_elements(background, palette)
    background = background.filter(ImageFilter.GaussianBlur(radius=1))

    buffered = io.BytesIO()
    background.save(buffered, format="PNG")
    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return BackgroundResponse(base64_background_image=base64_img)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
