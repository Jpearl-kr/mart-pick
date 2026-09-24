# mart-pick (마트픽)

장보기 최저가 비교 서비스. 영천 지역 마트별 상품 가격을 비교해서 가장 저렴하게 장보는 방법을 알려주는 프로젝트.

## 기술 스택

- **Supabase** — PostgreSQL DB, 인증(Auth), 파일 스토리지
- **FastAPI** — 최저가 계산 로직, Supabase 연동 백엔드 API
- **Next.js (App Router)** — 품목별 최저가 비교 화면, 장보기 리스트 UI

## 폴더 구조

```
backend/    FastAPI 백엔드
frontend/   Next.js 프론트엔드
```

## 로드맵

1. [x] 로컬 개발 환경 세팅 (FastAPI + Next.js 스캐폴드, mock 데이터로 동작 확인)
2. [x] 광장식자재마트(shop.smk.kr) 전단지 스크래퍼 — OCR 없이 내부 JSON API를 직접 호출해서 상품명/옵션/가격을 그대로 수집 (`backend/app/scrapers/smk.py`)
3. [x] 이미지로만 오는 전단지용 비전 OCR — Claude Vision으로 상품명/옵션/가격을 구조화된 JSON으로 추출 (`backend/app/ocr/vision.py`). 아직 실제 API 키로 정확도 검증 전
4. [ ] Supabase 프로젝트 생성 + `backend/sql/schema.sql` 실행 (markets / price_snapshots 테이블)
5. [ ] `/scrape/smk/ingest`, `/ocr/flyer/ingest`로 실제 전단지 데이터를 Supabase에 적재, 매일 아침 자동 실행되도록 스케줄링
6. [ ] 여러 마트의 상품명을 매칭해서 "같은 품목"으로 묶는 로직 (마트마다 상품명이 달라서 별도 단계로 분리)
7. [ ] FastAPI `/products`, `/lowest-price`를 mock 데이터 → Supabase 연동으로 전환
8. [ ] Supabase Auth 연동 (FastAPI JWT 검증)
9. [ ] Next.js 로그인 화면 + 장바구니 합산 비교 기능
10. [ ] Next.js → Vercel 배포, FastAPI → Railway/Render 배포

### 전단지 스크래퍼 (광장식자재마트)

카카오톡으로 오는 `shop.smk.kr/managerplus/martSkinview22.html?...` 링크는 정적 이미지가 아니라,
페이지가 뜨면서 자체 JSON API(`categorylist.php`, `itemlist.php`)를 호출해 상품을 그려주는 구조다.
그 API를 그대로 재현해서 상품명 · 옵션(단위) · 판매가 · 정가(할인 전 가격)를 정확히 뽑아낸다.

```bash
# 미리보기 (DB에 안 씀)
curl -G "http://localhost:8000/scrape/smk" --data-urlencode "url=<카톡으로 받은 전단지 링크>"

# Supabase에 적재 (같은 날 같은 마트로 재실행해도 upsert라 중복 안 됨)
curl -X POST -G "http://localhost:8000/scrape/smk/ingest" --data-urlencode "url=<카톡으로 받은 전단지 링크>"
```

### 이미지 전단지 OCR (Claude Vision)

탑마트처럼 전단지를 사진/그래픽 이미지로 보내는 마트는 스크래핑이 불가능하다. 대신 Claude의
비전 기능으로 이미지를 직접 읽어서 상품명 · 옵션 · 판매가 · (있으면) 정가를 뽑아낸다.
전통적인 OCR(Tesseract 등)은 상품 사진 + 가격 배지가 뒤섞인 비정형 레이아웃에서 정확도가 낮아서
채택하지 않았다. `backend/.env`에 `ANTHROPIC_API_KEY`가 필요하다 (console.anthropic.com에서 발급,
Claude Code 구독과 별개의 종량제 API 키).

```bash
# 미리보기 (DB에 안 씀)
curl -F "file=@flyer.jpg" "http://localhost:8000/ocr/flyer"

# Supabase에 적재 (마트 이름을 직접 지정 - 이미지엔 shopid 같은 게 없어서)
curl -X POST -F "file=@flyer.jpg" -G "http://localhost:8000/ocr/flyer/ingest" --data-urlencode "market_name=탑마트 영천점"
```

## 로컬 실행

### 백엔드 (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # Supabase 연동 전까지는 채우지 않아도 mock 데이터로 동작함
uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

### 프론트엔드 (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

http://localhost:3000
