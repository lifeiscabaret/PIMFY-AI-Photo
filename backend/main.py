# --- 전역 패치: torch 버전 인자 호환성 문제 해결 ---
#Mcp용
from mcp.server.fastmcp import FastMCP

import torch.utils._pytree as _pytree
def patched_register(node_type, flatten_fn, unflatten_fn, serialized_type_name=None):
    return _pytree._register_pytree_node(node_type, flatten_fn, unflatten_fn)

_pytree.register_pytree_node = patched_register
import random
import torchvision
try:
    import torchvision.transforms.functional_tensor
except ImportError:
    import torchvision.transforms.functional as F
    import sys
    sys.modules["torchvision.transforms.functional_tensor"] = F

from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
import uuid 
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch
import numpy as np
import cv2
import io
import base64
import asyncio
import re
import textwrap
import requests
from typing import Optional, List, Tuple, Union, Dict
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("✅ HEIC Image Support Enabled.")
except ImportError:
    print("⚠️ pillow-heif not found. HEIC images might cause errors.")

import databases
import sqlalchemy
from rembg import new_session, remove 
from realesrgan import RealESRGANer 
from basicsr.archs.rrdbnet_arch import RRDBNet 
import openai 
import httpx 

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
IMAGE_BASE_PATH = os.getenv("IMAGE_BASE_PATH", "/inday_fileinfo/img")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://www.pimfyvirus.com")
CURRENT_SERVER_URL = "http://223.130.146.245:8000"

database = databases.Database(DATABASE_URL) if DATABASE_URL else None
metadata = sqlalchemy.MetaData()

dogs_table = sqlalchemy.Table(
    "homeprotection", metadata,
    sqlalchemy.Column("uid", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("subject", sqlalchemy.String(250)),
    sqlalchemy.Column("s_pic01", sqlalchemy.String(150)),
    sqlalchemy.Column("addinfo01", sqlalchemy.String(100)), 
    sqlalchemy.Column("addinfo02", sqlalchemy.String(100)),
    sqlalchemy.Column("addinfo12", sqlalchemy.String(250)),
    sqlalchemy.Column("addinfo15", sqlalchemy.String(250)),
    sqlalchemy.Column("addinfo03", sqlalchemy.String(10)),
    sqlalchemy.Column("addinfo04", sqlalchemy.String(10)),
    sqlalchemy.Column("addinfo05", sqlalchemy.String(10)),
    sqlalchemy.Column("addinfo07", sqlalchemy.String(10)),
    sqlalchemy.Column("addinfo08", sqlalchemy.Text),
    sqlalchemy.Column("addinfo09", sqlalchemy.Text),
    sqlalchemy.Column("addinfo10", sqlalchemy.Text),
    sqlalchemy.Column("addinfo11", sqlalchemy.String(250)),
    sqlalchemy.Column("addinfo19", sqlalchemy.String(250)),
)

sub02_table = sqlalchemy.Table(
    "homeprotectionsub02", metadata,
    sqlalchemy.Column("puid", sqlalchemy.Integer), 
    sqlalchemy.Column("s_pic01", sqlalchemy.String(150)),
    sqlalchemy.Column("num", sqlalchemy.Integer), 
)

class Dog(BaseModel):
    uid: int
    subject: str
    s_pic01: Optional[str] = None
    image_filenames: List[str] = [] 
    addinfo01: Optional[str] = None 
    addinfo02: Optional[str] = None 
    addinfo03: Optional[str] = None
    addinfo04: Optional[str] = None
    addinfo05: Optional[str] = None
    addinfo07: Optional[str] = None
    addinfo08: Optional[str] = None
    addinfo09: Optional[str] = None
    addinfo10: Optional[str] = None
    addinfo11: Optional[str] = None
    addinfo12: Optional[str] = None
    addinfo15: Optional[str] = None
    addinfo19: Optional[str] = None

class RealProfileRequest(BaseModel):
    dog_uid: int
    contact: Optional[str] = None 

models = {}
app = FastAPI()
#Mcp용
mcp = FastMCP("PimfyVirus")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("generated_images", exist_ok=True)
#app.mount("/images", StaticFiles(directory="/app/generated_images"), name="images")
app.mount("/images", StaticFiles(directory="generated_images"), name="images")

device = "cpu"
gpu_id = None
print("🛡️ Backend is running on CPU Mode to save VRAM for SDXL.")

SDXL_SERVICE_URL = "http://172.17.0.2:8001/generate/background"

@app.on_event("startup")
def load_models_and_db():
    try:
        model_arch = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        model_path = "/app/esrgan/RealESRGAN_x4plus.pth"
        models["upsampler"] = RealESRGANer(scale=4, model_path=model_path, model=model_arch, tile=0, tile_pad=10, pre_pad=0, half=True if device == "cuda" else False, gpu_id=gpu_id)
    except Exception as e: print(f"🚨 ESRGAN Error: {e}")

    try: models["remover"] = new_session(model_name="isnet-general-use")
    except: models["remover"] = new_session()

@app.on_event("shutdown")
async def shutdown_db_client():
    if database and database.is_connected: await database.disconnect()

async def get_db_connection():
    if database and not database.is_connected: await database.connect()
    return database

def resize_image_if_too_large(img: Image.Image, max_dim: int = 1024) -> Image.Image:
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img

def create_framed_image(pil_img: Image.Image) -> Image.Image:
    w, h = pil_img.size
    max_dim = max(w, h)
    square_canvas = Image.new('RGB', (max_dim, max_dim), 'white')
    square_canvas.paste(pil_img, ((max_dim - w) // 2, (max_dim - h) // 2))
    return ImageOps.expand(square_canvas, border=int(max_dim * 0.03), fill='white')

def attach_logo_bottom_center(base_img: Image.Image) -> Image.Image:
    try:
        logo_dir = "/app/logos"
        if not os.path.exists(logo_dir): 
            return base_img
        logo_files = [f for f in os.listdir(logo_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not logo_files: 
            return base_img
        
        logo = Image.open(os.path.join(logo_dir, random.choice(logo_files))).convert("RGBA")
        base_img = base_img.convert("RGBA")
        target_width = int(base_img.size[0] * 0.10)
        logo = logo.resize((target_width, int(logo.height * (target_width / logo.width))), Image.LANCZOS)
        
        # 로고 합성 위치 및 마스크 적용 (투명도 유지)
        base_img.paste(logo, ((base_img.size[0] - target_width) // 2, base_img.size[1] - logo.height - 15), logo)
        return base_img.convert("RGB")
    except: 
        return base_img.convert("RGB")

async def get_dog_details(dog_uid: int) -> Dog:
    db = await get_db_connection()
    dog_data = await db.fetch_one(dogs_table.select().where(dogs_table.c.uid == dog_uid))
    if not dog_data: raise HTTPException(status_code=404, detail="Dog Not Found")
    image_data = await db.fetch_all(sub02_table.select().where(sub02_table.c.puid == dog_uid).order_by(sub02_table.c.num))
    
    image_filenames = []
    for row in image_data:
        fname = row['s_pic01']
        if isinstance(fname, bytes): fname = fname.decode('utf-8', errors='ignore')
        image_filenames.append(fname)
        
    return Dog(**dog_data, image_filenames=image_filenames)

def pil_to_cv2(pil_image): return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
def cv2_to_pil(cv2_image): return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

def draw_text_with_stroke(draw, x, y, text, font, fill, stroke, width):
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx*dx + dy*dy <= width*width: draw.text((x + dx, y + dy), text, font=font, fill=stroke)
    draw.text((x, y), text, font=font, fill=fill)

def get_text_width(draw, text, font):
    try: return draw.textlength(text, font=font)
    except: return len(text) * (font.size * 0.6)

def remove_emojis(text):
    if isinstance(text, bytes): text = text.decode('utf-8', errors='ignore')
    if not text: return ""
    return re.sub(r'[^\w\s,.\-?!@#%&()가-힣/]', '', text).strip() if text else ""

async def call_sdxl_service(base64_dog_image: str, dog_info: dict) -> Image.Image:
    print(f"🎨 SDXL 서버(8001)에 이미지 생성을 요청합니다...")
    try:
        async with httpx.AsyncClient(timeout=100.0) as client:
            # 주소를 컨테이너 이름인 sdxl-service로 하거나 localhost로 설정
            res = await client.post("http://172.17.0.2:8001/generate/background", 
                                    json={"base64_dog_image": base64_dog_image, "prompt": "luxury studio background"})
            res.raise_for_status()
            return Image.open(io.BytesIO(base64.b64decode(res.json().get("base64_background_image")))).convert("RGB")
    except Exception as e:
        print(f"🚨 SDXL 호출 에러: {e}")
        # 에러 나면 임시로 단색 배경이라도 띄워줌
        return Image.new('RGB', (1080, 1350), (255, 240, 245))

def generate_dog_text(dog: Dog) -> Dict:
    raw_name = dog.subject
    if isinstance(raw_name, bytes): raw_name = raw_name.decode('utf-8', errors='ignore')
    name = remove_emojis(raw_name.split('/')[0] if '/' in raw_name else raw_name).strip()
    
    age_raw = dog.addinfo05
    if isinstance(age_raw, bytes): age_raw = age_raw.decode('utf-8', errors='ignore')
    age = age_raw if age_raw and not age_raw.isdigit() else "정보 없음"
    
    info = [f"이름: {name}", f"성별: {remove_emojis(dog.addinfo03)}", f"출생: {age}", f"몸무게: {remove_emojis(dog.addinfo07)}kg", f"중성화: {remove_emojis(dog.addinfo04)}"]
    
    story = f"이름:{name}, " + " ".join([remove_emojis(x) for x in [dog.addinfo08, dog.addinfo09, dog.addinfo10] if x])
    system_prompt = "유기견이 미래 가족에게 보내는 편지. '해요체' 사용. 분량은 3문장 정도. 아이의 특징을 잘 살려서 작성. 이모지 금지."
    
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"정보: {story}"}], max_tokens=500)
        gen_story = remove_emojis(res.choices[0].message.content.strip())
    except: gen_story = f"안녕하세요, 저는 {name}이에요! 평생 가족을 기다려요. 어서 저를 만나러 와주세요."
    
    return {"basic_info": info, "story": gen_story, "name": name}

async def select_best_image(dog: Dog) -> Union[Image.Image, None]:
    best_img, best_score = None, -9999
    imgs = list(dict.fromkeys([x for x in ([dog.s_pic01] + dog.image_filenames) if x and x.strip()]))
    if not imgs or not models.get("remover"): return None
    
    for fname in imgs:
        try:
            if isinstance(fname, bytes): fname = fname.decode('utf-8', errors='ignore')
            res = requests.get(f"{SITE_BASE_URL}{IMAGE_BASE_PATH}/{fname}", stream=True, timeout=5)
            img = ImageOps.exif_transpose(Image.open(res.raw).convert("RGB"))
            if img.size[0] < 250: continue
            
            small = img.resize((320, int(img.size[1]*(320/img.size[0]))))
            no_bg = remove(small, session=models["remover"], alpha_matting=False)
            if cv2.countNonZero(np.array(no_bg.split()[3])) == 0: continue
            
            x, y, w, h = cv2.boundingRect(cv2.findNonZero(np.array(no_bg.split()[3])))
            score = (w*h)/(320*small.size[1])*100 + (1-(((x+w/2)-160)**2+((y+h/2)-small.size[1]/2)**2)**0.5 / (320**2+small.size[1]**2)**0.5)*50
            if img.size[1] > img.size[0] * 2.2: score -= 30
            if score > best_score: best_score, best_img = score, img
        except: continue
    return best_img

@app.post("/api/v1/generate-real-profile")
async def generate_real_profile(request: RealProfileRequest):
    if "upsampler" not in models: raise HTTPException(503, "Loading")
    try:
        dog = await get_dog_details(request.dog_uid)
        best_img = await select_best_image(dog)
        if not best_img: return {"profile_text": "이미지 없음"}
        
        out, _ = models["upsampler"].enhance(pil_to_cv2(resize_image_if_too_large(best_img)), outscale=4)
        processed = create_framed_image(cv2_to_pil(out))
        
        buf = io.BytesIO()
        processed.save(buf, format="PNG")
        bg_img = await call_sdxl_service(base64.b64encode(buf.getvalue()).decode("utf-8"), {})
        
        text_data = generate_dog_text(dog)
        template = bg_img.resize((1080, 1350))
        draw = ImageDraw.Draw(template)
        
        # ⭐️ 폰트 로드: 사용자님의 기존 로직 그대로 유지하면서 경로만 절대경로로 변경
        try:
            ft = ImageFont.truetype("/app/fonts/KyoboHandwriting2021sjy.otf", 80)
            fb = ImageFont.truetype("/app/fonts/KyoboHandwriting2021sjy.otf", 34)
        except: ft = fb = ImageFont.load_default()

        t_txt = f"{text_data['name']}의 가족을 찾습니다."
        draw_text_with_stroke(draw, (1080-get_text_width(draw, t_txt, ft))//2, 60, t_txt, ft, (255,255,255), (0,0,0), 3)
        
        lines = text_data['basic_info'] + textwrap.wrap(text_data['story'], 35)
        if request.contact: lines.extend(["", f"Contact. {request.contact}"])
        
        p_w, p_h = processed.size
        target_w = 980
        target_h = int(p_h * (target_w / p_w))
        avail_h = 1350 - 180 - (len(lines)*50 + 50) - 100
        if target_h > avail_h: target_h, target_w = avail_h, int(p_w * (avail_h / p_h))
        
        template.paste(processed.resize((target_w, target_h)), ((1080-target_w)//2, 160))
        
        cy = 160 + target_h + 30
        for line in lines:
            draw_text_with_stroke(draw, (1080-get_text_width(draw, line, fb))//2, cy, line, fb, (50,50,50), (255,255,255), 2)
            cy += 50
            
        template = attach_logo_bottom_center(template)
        
        fname = f"{uuid.uuid4()}.jpg"
        template.save(f"generated_images/{fname}", quality=90)
        return {"profile_text": '\n'.join(lines), "profile_image_base64": "", "image_url": f"{CURRENT_SERVER_URL}/images/{fname}"}
    except Exception as e: return {"profile_text": "Error"}

@app.post("/api/v1/generate-adoption-profile")
async def generate_adoption_profile(image: UploadFile = File(...), name: str = Form(...), age: str = Form(...), personality: str = Form(...), features: str = Form(...), contact: Optional[str] = Form(None)):
    if "upsampler" not in models: raise HTTPException(503, "Loading")
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(await image.read())).convert("RGB"))
        out, _ = models["upsampler"].enhance(pil_to_cv2(resize_image_if_too_large(img)), outscale=4)
        processed = create_framed_image(cv2_to_pil(out))
        
        buf = io.BytesIO()
        processed.save(buf, format="PNG")
        bg_img = await call_sdxl_service(base64.b64encode(buf.getvalue()).decode("utf-8"), {})
        
        sys_prompt = "유기견이 미래 가족에게 보내는 편지. '해요체'. 분량은 3문장 정도. 아이의 특징 포함. 이모지 금지."
        try:
            res = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")).chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": f"이름:{name}, 나이:{age}, 성격:{personality}, 특징:{features}"}], max_tokens=400)
            story = remove_emojis(res.choices[0].message.content.strip())
        except: story = f"안녕하세요! 저는 {name}이에요."
        
        template = bg_img.resize((1080, 1350))
        draw = ImageDraw.Draw(template)
        try:
            ft = ImageFont.truetype("/app/fonts/KyoboHandwriting2021sjy.otf", 80)
            fb = ImageFont.truetype("/app/fonts/KyoboHandwriting2021sjy.otf", 34)
        except: ft = fb = ImageFont.load_default()

        t_txt = f"{name}의 가족을 찾습니다."
        draw_text_with_stroke(draw, (1080-get_text_width(draw, t_txt, ft))//2, 60, t_txt, ft, (255,255,255), (0,0,0), 3)
        
        lines = [f"이름: {name}", f"나이: {age}"] + textwrap.wrap(story, 35)
        if contact: lines.extend(["", f"Contact. {contact}"])
        
        p_w, p_h = processed.size
        target_w = 980
        target_h = int(p_h * (target_w / p_w))
        avail_h = 1350 - 180 - (len(lines)*50 + 50) - 100
        if target_h > avail_h: target_h, target_w = avail_h, int(p_w * (avail_h / p_h))
        
        template.paste(processed.resize((target_w, target_h)), ((1080-target_w)//2, 160))
        
        cy = 160 + target_h + 30
        for line in lines:
            draw_text_with_stroke(draw, (1080-get_text_width(draw, line, fb))//2, cy, line, fb, (50,50,50), (255,255,255), 2)
            cy += 50
            
        # 하단 로고 합성
        template = attach_logo_bottom_center(template)
        
        fname = f"{uuid.uuid4()}.jpg"
        # ✅ 아래 모든 줄은 스페이스바 8칸으로 들여쓰기를 맞췄습니다.
        template.save(f"generated_images/{fname}", quality=90)
        return {"profile_text": '\n'.join(lines), "profile_image_base64": "", "image_url": f"{CURRENT_SERVER_URL}/images/{fname}"}
    except Exception as e:
        print(f"🚨 Adoption Profile Error: {e}")
        raise HTTPException(422, "Error")

#Mcp
@mcp.tool()
async def generate_studio_profile_mcp(base64_image: str, bg_color: str = "#FFD1DC"):
    """
    유기견 사진(base64)을 받아 스튜디오 스타일 프로필을 생성합니다.
    """
    if "upsampler" not in models: return {"message": "모델 로딩 중..."}
    
    try:
        # Base64 데이터를 이미지로 변환
        img_data = base64.b64decode(base64_image)
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        
        # --- 이후 로직은 기존과 동일 ---
        if max(img.size) > 1280: img.thumbnail((1280, 1280), Image.LANCZOS)
        
        # (중략: 기존 업스케일링 및 누끼 로직)
        
        no_bg = remove(img, session=models["remover"], alpha_matting=True)
        # ... (중략) ...

        fname = f"{uuid.uuid4()}.jpg"
       # template.save(f"generated_images/{fname}", quality=90)
        template.save(f"generated_images/{fname}", quality=90)

        return {
            "image_url": f"{CURRENT_SERVER_URL}/images/{fname}",
            "message": "성공적으로 생성되었습니다."
        }
    except Exception as e:
        return {"message": f"에러 발생: {str(e)}"}

@app.post("/api/v1/generate-studio-profile")
async def generate_studio_profile(image: UploadFile = File(...), bg_color: str = Form("#FFD1DC")):
    if "upsampler" not in models: raise HTTPException(503, "Loading")
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(await image.read())).convert("RGB"))
        if max(img.size) > 1280: img.thumbnail((1280, 1280), Image.LANCZOS)
        if max(img.size) < 1000:
            out, _ = models["upsampler"].enhance(pil_to_cv2(img), outscale=4)
            img = resize_image_if_too_large(cv2_to_pil(out), 1500)
            
        no_bg = remove(img, session=models["remover"], alpha_matting=True)
        subject = no_bg.crop(no_bg.getbbox()) if no_bg.getbbox() else no_bg
        
        template = Image.new("RGB", (1080, 1350), ImageColor.getrgb(bg_color) if bg_color else (255, 240, 245))
        
        scale = min(972/subject.size[0], 1215/subject.size[1])
        new_size = (int(subject.size[0]*scale), int(subject.size[1]*scale))
        subject = subject.resize(new_size, Image.LANCZOS)
        
        template.paste(subject, ((1080-new_size[0])//2, (1350-new_size[1])//2), subject)
        template = attach_logo_bottom_center(template)
        
        fname = f"{uuid.uuid4()}.jpg"
        template.save(f"generated_images/{fname}", quality=90)
        return {"profile_image_base64": "", "image_url": f"{CURRENT_SERVER_URL}/images/{fname}", "message": "성공"}
    except: return {"message": "Error"}

@app.get("/api/dogs/search")
async def search_dogs(name: str):
    db = await get_db_connection()
    rows = await db.fetch_all(dogs_table.select().where(dogs_table.c.subject.like(f"%{name}%")).limit(10))
    res = []
    for r in rows:
        img = await db.fetch_one(sub02_table.select().where(sub02_table.c.puid == r['uid']).order_by(sub02_table.c.num).limit(1))
        
        fname = img['s_pic01'] if img and img['s_pic01'] else r['s_pic01']
        if isinstance(fname, bytes): fname = fname.decode('utf-8', 'ignore')
        
        def safe_dec(val): return val.decode('utf-8', 'ignore') if isinstance(val, bytes) else val
        
        raw_name = safe_dec(r['subject'])
        dog_name = raw_name.split('/')[0] if raw_name else "이름모름"
        
        res.append({
            "id": r['uid'],
            "name": dog_name,
            "breed": safe_dec(r['addinfo03']) or "믹스",
            "age": 2025 - int(safe_dec(r['addinfo05'])[:4]) if safe_dec(r['addinfo05']) and safe_dec(r['addinfo05']).isdigit() else 0,
            "story": safe_dec(r['addinfo08']) or "사연 없음",
            "imageUrl": f"{SITE_BASE_URL}{IMAGE_BASE_PATH}/{fname}" if fname else "",
            "shelter": safe_dec(r['addinfo12']) or "정보 없음"
        })
    return res

if __name__ == "__main__":
    import uvicorn
    import threading

    # 1. MCP 서버 실행 함수
    def run_mcp():
        import os
        os.environ["MCP_PORT"] = "8002" 
        mcp.run(transport="sse")

    # MCP 서버를 별도 스레드에서 실행
    threading.Thread(target=run_mcp, daemon=True).start()

    # 2. 메인 FastAPI 서버 실행 (8000번 포트)
    print("🚀 메인 서버(8000)를 시작합니다...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
