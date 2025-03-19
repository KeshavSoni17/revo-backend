from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rcm_router

app = FastAPI(
    title="Revo Application",
    description="A FastAPI-based Revo application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Revo Application API"}


app.include_router(rcm_router, prefix="/rcm", tags=["Revo Operations"])
