from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="ONC FastAPI Demo")

@app.get("/")
def root():
    return {
        "message": "Hello from ONC Platform",
        "app": "fastapi-demo",
        "time": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
