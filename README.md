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
2. [ ] Supabase 프로젝트 생성 + markets/products/prices 테이블 설계
3. [ ] 실제 마트 가격 수기 입력 (10~20개)
4. [ ] FastAPI에서 mock 데이터 → Supabase 연동으로 전환
5. [ ] Supabase Auth 연동 (FastAPI JWT 검증)
6. [ ] Next.js 로그인 화면 + 장바구니 합산 비교 기능
7. [ ] Next.js → Vercel 배포, FastAPI → Railway/Render 배포

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
