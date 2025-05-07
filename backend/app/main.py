import os
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

if os.getenv("ENABLE_ANALYSIS") == "true":
    from .routers import analysis
    app.include_router(analysis.router)
else:
    from fastapi import APIRouter
    
    mock_router = APIRouter()
    
    @mock_router.post("/api/analysis/verify_token")
    async def mock_verify_token():
        return {"status": "mock", "valid": True}
    
    @mock_router.post("/api/analysis/account")
    async def mock_account_analysis():
        return {"status": "mock"}
    
    @mock_router.get("/api/analysis/account/{client_id}")
    async def mock_get_account_analysis(client_id: str):
        return {"status": "mock"}
    
    @mock_router.get("/api/analysis/profile")
    async def mock_profile():
        return {"status": "mock"}
    
    app.include_router(mock_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the SNS AI Agent API"}
