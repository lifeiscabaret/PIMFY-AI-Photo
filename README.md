# 📸 PIMFY Photo (핌피포토)
> **유기견의 개성과 맥락을 시각화하는 AI 프로필 생성 서비스**

> ⚠️ **배포 상태**: 비용 효율 판단에 따라 GPU 서버(NCP V100)를 반납하여 **라이브 데모는 운영하지 않습니다.**
> (기존 배포 주소: `http://223.130.146.245:3000` — 현재 접속 불가) 아래 [시작하기](#-시작하기-getting-started) 가이드로 로컬 실행할 수 있습니다.
>
> 📌 **본 README는 GPU 서버에서 실제 구축·운영했던 풀 파이프라인(SDXL 배경 생성 · GPT Vision 품질 필터링 포함)을 기준으로 기술합니다.** 서버 반납 이후 공개 저장소는 GPU 없이도 구동되도록, **SDXL 배경 생성 → PIL 절차적 배경 / GPT Vision 필터링 → 비활성화**된 경량 데모 폴백 상태입니다. 데모에서 비활성인 모듈은 아래에 `⛔ 데모 비활성`으로 표기했습니다.

<p align="center">
  <img src="images/pimfyvirus.png" width="45%" alt="PIMFY Virus Data" />
  <img src="images/pimfy_profile.jpg" width="45%" alt="PIMFY AI Profile" />
</p>
<p align="center">
  <i>(왼쪽: 원본 유기동물 공고 데이터 / 오른쪽: AI를 통해 생성된 맞춤형 프로필)</i>
</p>

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![NCP](https://img.shields.io/badge/NAVER%20Cloud-03C75A?style=for-the-badge&logo=naver&logoColor=white)

---

## 📝 프로젝트 개요 (Overview)

보호소 직원은 동물 돌봄에 집중해야 하는데 입양 홍보 사진 제작까지 직접 해야 한다.
저품질 이미지는 입양률 저하로 이어지고, AI가 보편화된 시대에도 이 영역엔 아무것도 적용되지 않았다.

**PIMFY Photo**는 사진 한 장을 입력하면 배경 제거 → 업스케일 → 배경 합성 → AI 스토리 생성 → 프로필 카드 완성까지 단일 파이프라인으로 자동 처리한다. 보호소 구독 모델 기반 SaaS로 지속 가능한 비즈니스 구조를 목표로 설계했다.

- **개발 기간**: 2025.10 ~ 2026.01 | 고도화 진행 중
- **배포 환경**: NCP GPU 서버 (V100) · Docker
- **핵심 가치**: AI 기술이 닿지 않는 영역에 직접 적용 · 정량적 성능 최적화 · 사회적 임팩트 정량화

---

## 🏆 핵심 성과 (Key Achievements)

| 지표 | Before | After | 개선율 |
|------|--------|-------|--------|
| AI 추론 시간 | 360초 (6분) | 30초 이내 | **91% 단축** |
| GPU 메모리 점유 | FP32 기준 | FP16 양자화 적용 | **50% 절감** |
| Vision API 호출 비용 | 전체 이미지 호출 | OpenCV 1차 필터링 후 호출 | **70% 감소** |
| 모바일 저장 UX Depth | 4단계 | 2단계 | Web Share API 도입 |

---

## 🚀 핵심 서비스 (Core Service)

### 🧡 1. 핌피바이러스 프로필
핌피바이러스 DB의 실시간 공고 데이터와 연동하여, 유기동물의 기본 정보를 구조화된 프로필 카드로 자동 변환한다.
(`GET /api/dogs/search` → `POST /api/v1/generate-real-profile`)

### 🏠 2. 입양·임보 프로필
유기견의 성격과 특징을 AI가 분석하여, 차가운 보호소 배경 대신 SDXL로 생성한 파스텔톤 배경에 합성한다.
(`POST /api/v1/generate-adoption-profile`)

### 📸 3. 스튜디오 프로필
Real-ESRGAN 기반 4배 업스케일링으로 전문 스튜디오 수준의 고품질 프로필을 제공한다.
(`POST /api/v1/generate-studio-profile`)

> 📱 **멍생네컷**: 업로드한 사진으로 네컷 사진 형태의 프로필도 구성할 수 있습니다.
> HEIC(아이폰) 이미지는 프론트엔드(`heic2any`)·백엔드(`pillow-heif`) 양쪽에서 자동 처리됩니다.

---

## 🏗 시스템 아키텍처 (System Architecture)

AI 파이프라인은 메모리 부하 분산을 위해 **메인 API 서버**와 **SDXL 배경 생성 서버**를 별도 컨테이너로 분리한 마이크로서비스 구조로 설계했다.

```
이미지 입력
    │
    ▼
[1차 필터링] OpenCV — 선명도 · 밝기 · 얼굴 감지 (룰 기반)
    │ Vision API 호출 70% 사전 차단
    ▼
[2차 필터링] GPT Vision — 품질 채점 후 저품질 이미지 탈락      ⛔ 데모 비활성
    ▼
[Real-ESRGAN] 4배 업스케일링 (x4plus)
    ▼
[rembg] 배경 제거 (isnet-general-use)
    ▼
[SDXL] 랜덤 파스텔톤 배경 생성 (별도 GPU 서비스, :8001)      ⛔ 데모: PIL 절차적 배경으로 대체
    ▼
[GPT-4o-mini] 공공데이터 기반 감성 스토리 생성 + 텍스트 오버레이
    ▼
프로필 카드 출력 (Pillow 합성 · UUID 저장) + Web Share API 공유
```

---

## 🏗 인프라 협업 (Infrastructure)

경기도 AI 고성능 컴퓨팅 지원사업 선정 프로젝트로, 메가존클라우드 담당자의 초기 서버 구성 지원을 받아 NCP GPU(V100) 인프라를 구축·운영했습니다.

---

## ⚙️ 기술 스택 (Tech Stack)

| 분류 | 기술 |
|------|------|
| AI 모델 | Real-ESRGAN · rembg · GPT-4o-mini · SDXL `⛔ 데모 비활성` |
| 전처리 | OpenCV |
| 최적화 | FP16 양자화 · Singleton 모델 로딩 |
| Backend | FastAPI · PyTorch · Python |
| Frontend | Next.js 15 (App Router) · React 19 · TypeScript · TailwindCSS |
| DB | MySQL (`databases` + `aiomysql`) |
| 인프라 | NCP GPU 서버 (V100) · Docker · Cafe24 |

---

## 🔥 핵심 트러블슈팅 (Troubleshooting)

### 1️⃣ SDXL 추론 지연 91% 단축 — Singleton + FP16 양자화 *(GPU 운영 당시)*

**문제**: 이미지 1장당 추론 시간 약 360초(6분). 실시간 서비스 불가 수준의 병목.

**원인**:
- API 요청마다 대용량 모델을 새로 로드하는 구조
- FP32 가중치의 과도한 GPU 메모리 점유로 추론 속도 저하

**해결**:
- **Singleton Pattern 적용**: 서버 구동 시 모델을 1회만 메모리에 상주시켜 재사용
- **FP16 Half Precision 양자화**: 가중치 경량화로 연산 속도 향상 + GPU 메모리 50% 절감

**결과**: 360초 → **30초 이내** 단축. 실질적인 서비스 운영 가능 상태 확보.

---

### 2️⃣ Vision API 호출 비용 70% 감소 — 이중 필터링 파이프라인 *(GPU 운영 당시)*

**문제**: 모든 이미지에 Vision API를 호출하면 비용 폭증. 저품질 이미지를 API 호출 전에 걸러낼 방법이 필요했다.

**해결**:
- **1차 필터링 (OpenCV)**: 선명도 · 밝기 · 얼굴 감지를 룰 기반으로 사전 차단. 연산 비용 없이 부적합 이미지를 제거.
- **2차 필터링 (GPT Vision)**: 통과한 이미지에만 품질 채점을 수행해 기준 미달 이미지를 탈락.

**결과**: Vision API 호출 **70% 감소**. 비용 최적화와 품질 게이팅을 동시에 달성.

---

### 3️⃣ 모바일 저장 UX 개선 — Web Share API

**문제**: 모바일 브라우저 보안 정책으로 이미지 다운로드 시 갤러리가 아닌 '파일 앱'으로 저장. 사용자 저장 Depth 4단계.

**해결**: Web Share API 도입으로 시스템 공유 시트 호출 → 갤러리 직접 저장. Depth **4단계 → 2단계** 축소.

---

### 4️⃣ DB 타입 불일치 및 Mixed Content 이미지 렌더링 실패

**문제**: 특정 DB 환경에서 문자열이 `bytes` 타입으로 반환되어 서버 에러 발생. HTTP 이미지 URL이 HTTPS 환경에서 Mixed Content로 렌더링 실패.

**해결**:
- `safe_dec()` 유틸리티 함수로 모든 DB 반환값 타입 검증 처리
- 이미지 데이터를 **Base64**로 인코딩하여 전송, Mixed Content 이슈 완전 차단

---

## 📂 프로젝트 구조 (Project Structure)

```
pimfy-ai-studio/
├── backend/
│   ├── main.py                 # 메인 API 서버 (프로필 생성, 공고 검색, AI 파이프라인)
│   ├── sdxl_server.py          # 배경 생성 마이크로서비스 (:8001) — 데모는 PIL 절차적 배경
│   ├── Dockerfile              # 메인 API 이미지 (pytorch 2.1.0 · CUDA 12.1 베이스)
│   ├── Dockerfile.sdxl         # SDXL 서비스 이미지
│   ├── requirements.txt        # 메인 API 의존성
│   └── requirements.sdxl.txt   # SDXL 서비스 의존성
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── profile/        # 프로필 생성 플로우 (Select/Ready/Adoption/General/Studio Step)
│   │   │   ├── mungsaeng/      # 멍생네컷 플로우 (Ready/Upload/Size Step)
│   │   │   ├── result/         # 결과 페이지
│   │   │   └── page.tsx        # 시작 페이지
│   │   ├── api/profileApi.ts   # 백엔드 API 호출 레이어
│   │   └── components/ui/      # 공용 UI (LoadingSpinner, Icons)
│   └── package.json
├── fonts/                      # 프로필 합성용 한글 폰트 (NanumGothic, Kyobo)
└── images/                     # README용 이미지 리소스
```

---

## 🛠 시작하기 (Getting Started)

> **사전 요구사항**: NVIDIA GPU + CUDA 12.1 환경 (AI 추론), Python 3.10+, Node.js 18+, MySQL

### 1. 저장소 복제
```bash
git clone https://github.com/lifeiscabaret/pimfy-ai-studio.git
cd pimfy-ai-studio
```

### 2. 백엔드 실행 (Backend)

`backend/.env` 파일을 생성하고 환경 변수를 설정합니다.

```env
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname
OPENAI_API_KEY=sk-...
IMAGE_BASE_PATH=/inday_fileinfo/img
SITE_BASE_URL=https://www.pimfyvirus.com
CURRENT_SERVER_URL=http://localhost:8000
```

**(A) 로컬 실행**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# SDXL 배경 생성 서비스 (별도 터미널, :8001)
uvicorn sdxl_server:app --host 0.0.0.0 --port 8001

# 메인 API 서버 (:8000)
uvicorn main:app --host 0.0.0.0 --port 8000
```

**(B) Docker 실행**
```bash
# 루트의 docker-compose로 메인 API + SDXL 서비스 동시 실행
docker compose up --build
```
> 메인 서버는 `sdxl-service:8001`로 SDXL 서비스를 호출하므로, 두 컨테이너를 동일 네트워크에서 실행하세요.

### 3. 프론트엔드 실행 (Frontend)

`frontend/.env.local` 파일에 백엔드 주소를 설정합니다.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3000` 으로 접속합니다.

---

## 🌱 향후 계획 (Roadmap)

- [ ] 핌피 웹 AI 서비스 런칭 준비
- [ ] SDXL 배경 생성 디자이너 협업 예정
- [ ] 모델 튜닝
