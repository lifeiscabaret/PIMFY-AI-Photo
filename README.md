# 📸 PIMFY Photo (핌피포토)
> **유기견의 개성과 맥락을 시각화하는 AI 프로필 생성 서비스**

<p align="center">
  <img src="images/pimfyvirus.png" width="45%" alt="PIMFY Virus Data" />
  <img src="images/pimfy_profile.jpg" width="45%" alt="PIMFY AI Profile" />
</p>
<p align="center">
  <i>(왼쪽: 원본 유기동물 공고 데이터 / 오른쪽: AI를 통해 생성된 맞춤형 프로필)</i>
</p>

> ⚠️ **배포 상태**: 현재 GPU 서버(Naver Cloud V100)를 반납하여 **라이브 데모는 운영하지 않습니다.**
> 아래 [시작하기](#-시작하기-getting-started) 가이드를 따라 로컬 환경에서 실행할 수 있습니다.

## 📝 프로젝트 개요 (Overview)
기존 유기견 공고 사진의 열악한 시각적 환경을 개선하기 위해 시작되었습니다. **PIMFY Photo**는 생성형 AI 기술을 활용해 유기견의 '가장 빛나는 순간'을 재구성하고, 데이터를 기반으로 감성적인 페르소나를 부여하여 실질적인 입양률 제고를 목표로 합니다.

- **개발 기간**: 2025.10 - 2026.02
- **핵심 가치**: 기술을 통한 사회적 가치 창출, 정량적 성능 최적화, 사용자 중심의 UX 개선

---

## ✨ 주요 기능 (Features)

사용자는 목적에 맞게 **3가지 프로필 생성 모드**와 **멍생네컷** 기능을 이용할 수 있습니다.

| 모드 | 설명 | 입력 데이터 | 관련 API |
| :--- | :--- | :--- | :--- |
| **핌피바이러스 프로필** | 유기동물 공고 DB를 검색해 선택한 아이의 정보를 기반으로 **자동 생성** | 공고 검색 (`dog_uid`) | `GET /api/dogs/search`<br/>`POST /api/v1/generate-real-profile` |
| **입양·임보 프로필** | 사진 + 이름/나이/성격/특징/연락처를 입력하면 GPT가 **감성 스토리텔링** 문구 생성 | 이미지 업로드 + 텍스트 | `POST /api/v1/generate-adoption-profile` |
| **스튜디오 프로필** | 사진과 원하는 배경색만으로 간편하게 스튜디오 화보풍 프로필 제작 | 이미지 업로드 + 배경색 | `POST /api/v1/generate-studio-profile` |
| **멍생네컷** 🐾 | 업로드한 사진으로 네컷 사진 형태의 프로필 구성 | 이미지 업로드 + 사이즈 선택 | — |

> HEIC(아이폰) 이미지는 프론트엔드(`heic2any`)와 백엔드(`pillow-heif`) 양쪽에서 자동 변환/처리됩니다.

---

## 🏆 주요 성과 (Key Achievements)
- **AI 추론 성능 91% 개선**: 360초(6분) → **30초** 이내로 단축
- **인프라 효율화**: FP16 양자화를 통한 GPU 메모리 점유율 **50% 절감**
- **UX 최적화**: Web Share API 도입으로 이미지 저장 Depth 축소 (4단계 → **2단계**)

---

## 🔥 핵심 트러블슈팅 (Core Troubleshooting)

### 1️⃣ SDXL 모델 추론 최적화 (Latency 91% 단축)
- **문제**: 초기 SDXL 모델 도입 시, 이미지 한 장당 **약 6분(360초)**이 소요되어 실시간 서비스가 불가능한 병목 현상 발생.
- **원인**: API 요청 시마다 대용량 모델을 새로 로드하는 로직과 가중치(FP32)의 과도한 GPU 메모리 점유.
- **해결**: 
  - **전역 로딩(Singleton Pattern)**: 모델을 서버 구동 시 1회 메모리에 상주시켜 재사용하는 구조로 변경.
  - **FP16(Half Precision) 양자화**: 모델 가중치를 경량화하여 연산 속도 향상 및 GPU 메모리 병목 해소.
- **결과**: 추론 시간을 **30초 이내로 단축**하여 실질적인 서비스 운영 가능 상태 확보.

### 2️⃣ 모바일 저장 UX 개선 (Web Share API)
- **문제**: 모바일 브라우저 보안 정책으로 인해 다운로드 시 갤러리가 아닌 '파일 앱'으로 저장되는 UX 불편함 발견.
- **해결**: **Web Share API**를 도입하여 시스템 공유 시트를 호출, 사용자가 원클릭으로 **갤러리에 직접 저장**할 수 있도록 구현.

### 3️⃣ 데이터 정합성 및 네트워크 예외 처리
- **문제**: 특정 DB 환경에서 문자열이 `bytes` 타입으로 반환되어 서버 에러 유발 및 Mixed Content 보안 이슈로 이미지 렌더링 실패.
- **해결**: `safe_dec` 유틸리티 함수를 통한 타입 검증 로직 도입 및 이미지 데이터를 **Base64**로 인코딩하여 전송함으로써 통신 안정성 확보.

---

## 🏗 시스템 아키텍처 및 파이프라인

AI 파이프라인은 메모리 부하 분산을 위해 **메인 API 서버**와 **SDXL 배경 생성 서버**를 별도 컨테이너로 분리한 마이크로서비스 구조로 설계되었습니다.

```
[Next.js Frontend] ──HTTP──> [Main API (FastAPI, :8000)] ──HTTP──> [SDXL Service (:8001)]
                                      │
                                      ├── Rembg (배경 제거)
                                      ├── Real-ESRGAN x4 (화질 복구)
                                      ├── GPT-4o-mini (스토리텔링)
                                      ├── MySQL (유기동물 공고 DB)
                                      └── Pillow (레이어 합성 / UUID 저장)
```

1. **Rembg (`isnet-general-use`)**: 저화질 배경 제거(누끼)
2. **Real-ESRGAN (`x4plus`)**: 4배 업스케일링을 통한 화질 복구
3. **SDXL Service**: 개인화된 파스텔톤 배경 생성 (별도 GPU 서비스로 호출)
4. **GPT-4o-mini**: 공고/입력 데이터 기반 감성 스토리텔링 문구 생성
5. **Synthesis**: Pillow를 이용한 레이어 합성 및 UUID 기반 저장

---

## 🛠 기술 스택 (Tech Stack)
- **AI/ML**: SDXL, Real-ESRGAN, Rembg, GPT-4o-mini, CUDA 12.1 (TensorRT 기반 이미지)
- **Backend**: FastAPI, SQLAlchemy + `databases` + `aiomysql`, Docker (2-container), Naver Cloud Platform (V100 GPU)
- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS

---

## 📂 프로젝트 구조 (Project Structure)

```
pimfy-ai-studio/
├── backend/
│   ├── main.py                 # 메인 API 서버 (프로필 생성, 공고 검색, AI 파이프라인)
│   ├── sdxl_server.py          # SDXL 배경 생성 마이크로서비스 (:8001)
│   ├── export_onnx_final.py    # 모델 ONNX 익스포트 스크립트
│   ├── Dockerfile              # 메인 API 이미지 (nvidia/tensorrt 베이스, CUDA 12.1)
│   ├── Dockerfile.sdxl         # SDXL 서비스 이미지
│   ├── requirements.txt        # 메인 API 의존성
│   ├── requirements.sdxl.txt   # SDXL 서비스 의존성
│   └── *.ttf / *.otf           # 프로필 합성용 한글 폰트 (NanumGothic, Kyobo)
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
└── images/                     # README용 이미지 리소스
```

---

## 🚀 시작하기 (Getting Started)

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
cd backend
# 메인 API 서버
docker build -t pimfy-api -f Dockerfile .
# SDXL 서비스
docker build -t pimfy-sdxl -f Dockerfile.sdxl .
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
