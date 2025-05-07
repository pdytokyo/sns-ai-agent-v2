from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import script

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(script.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the SNS AI Agent API"}
