"""Ultra-simple test FastAPI app"""
from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is running"}

@app.get("/")
async def root():
    return {"message": "Hello from Stock Analysis System"}

@app.get("/docs")
async def docs():
    return {"docs": "Available at /docs"}
