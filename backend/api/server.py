from fastapi import FastAPI
from dotenv import load_dotenv
from api.routes.chat import router as chat_router

load_dotenv()

app = FastAPI(title="ProtoPilot API")
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "ProtoPilot API is running"}

@app.get("/health")
def health():
    return {"ok": True}