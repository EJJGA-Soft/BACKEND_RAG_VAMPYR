
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

from rag_pipeline import CHAIN

load_dotenv()
app = FastAPI(
    title="Vampyr: Rise of the Night Walkers Assistant API", 
    version="2.0.0",
    description="API RAG para consultas sobre Vampyr: Rise of the Night Walkers"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restringe en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "service": "Vampyr: Rise of the Night Walkers Assistant API",
        "message": "The night awaits... �🦇"
    }

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        out = CHAIN.invoke({"question": req.message})
        return ChatResponse(answer=out)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Error al procesar tu consulta sobre Vampyr. Por favor intenta de nuevo."
        )

