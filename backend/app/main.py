from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import products, scrape

app = FastAPI(title="Mart-pick API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(scrape.router)


@app.get("/health")
def health():
    return {"status": "ok"}
