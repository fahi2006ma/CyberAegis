from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""You are CyberAegis, an AI-powered cybercrime first responder assistant for India.
    Your job is to help victims who have been scammed, hacked, harassed, or cheated online.
    Always:
    - Identify the type of cybercrime from what the user describes
    - Mention the relevant Indian law section (IT Act 2000/2008 or IPC)
    - Give clear step by step instructions on what to do next
    - Tell them what evidence to collect and preserve
    - Guide them to report at cybercrime.gov.in or call 1930
    - Be empathetic, calm, and supportive
    - Keep responses clear and easy to understand
    - Never ask for personal sensitive information like passwords or OTPs
    Respond in English only."""
)

chat_history = []

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "CyberAegis backend is running!"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        chat_history.append({
            "role": "user",
            "parts": [request.message]
        })

        response = model.generate_content(chat_history)
        
        reply = response.text

        chat_history.append({
            "role": "model",
            "parts": [reply]
        })

        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Sorry, something went wrong: {str(e)}"}