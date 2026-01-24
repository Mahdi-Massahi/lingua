from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from gtts import gTTS
import io
import os
import sys
import uuid
import json
from datetime import datetime
from pydantic import BaseModel

# Add src to path to import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agents.memory.user_store import UserStore
from src.agents.memory.vector_store import VectorStore
from src.agents.agent import root_agent

from google.adk.runners import App, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

app = FastAPI()

# Initialize stores
# We need to make sure we are in the root directory when initializing stores
# so they find the correct paths (./chroma_db, ./user_data.json)
# This assumes the app is run from the project root.

user_store = UserStore()
vector_store = VectorStore()

# Initialize ADK Runner
session_service = InMemorySessionService()
adk_app = App(name=root_agent.name, root_agent=root_agent)
runner = Runner(app=adk_app, session_service=session_service)

# Track active sessions to know when to create vs load (or just create once)
active_sessions = set()


class ChatManager:
    def __init__(self, file_path="chat_history.json"):
        self.file_path = file_path
        self.sessions = {}  # {session_id: {created_at, title, messages: []}}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.sessions = json.load(f)
            except:
                self.sessions = {}

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def create_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "title": f"Session {len(self.sessions) + 1}",
                "messages": [],
            }
            self.save()

    def add_message(self, session_id, role, text):
        if session_id not in self.sessions:
            self.create_session(session_id)

        self.sessions[session_id]["messages"].append(
            {"role": role, "text": text, "timestamp": datetime.now().isoformat()}
        )

        # Update title if it's the first user message
        if role == "user" and len(self.sessions[session_id]["messages"]) <= 2:
            self.sessions[session_id]["title"] = (
                text[:30] + "..." if len(text) > 30 else text
            )

        self.save()

    def get_sessions(self):
        # Return list sorted by date (newest first)
        result = []
        for sid, data in self.sessions.items():
            result.append(
                {
                    "id": sid,
                    "title": data.get("title", "Untitled"),
                    "created_at": data.get("created_at"),
                    "msg_count": len(data.get("messages", [])),
                }
            )
        # Sort by created_at descending
        result.sort(key=lambda x: x["created_at"], reverse=True)
        return result

    def get_history(self, session_id):
        return self.sessions.get(session_id, {}).get("messages", [])


chat_manager = ChatManager()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str | None = None


@app.get("/api/user")
async def get_user_profile():
    return user_store.get_profile()


@app.get("/api/vocabulary")
async def get_vocabulary():
    return vector_store.get_all_phrases()


@app.get("/api/search")
async def search_vocabulary(q: str):
    return vector_store.search_phrases(q)


@app.get("/api/speak")
async def speak_text(text: str, lang: str = "nl"):
    tts = gTTS(text=text, lang=lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return StreamingResponse(fp, media_type="audio/mp3")


@app.post("/api/vocabulary/{doc_id}/star")
async def toggle_star(doc_id: str):
    new_status = vector_store.toggle_star(doc_id)
    return {"starred": new_status}


@app.get("/api/sessions")
async def get_sessions():
    return chat_manager.get_sessions()


@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    return chat_manager.get_history(session_id)


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_id = request.user_id or "default_user"
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in active_sessions:
        # Create new session in ADK
        # Note: In a real app we might try to restore state from history,
        # but for now we start fresh in ADK logic while keeping UI history.
        await session_service.create_session(
            state={}, app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
        active_sessions.add(session_id)

    # Save User Message
    chat_manager.add_message(session_id, "user", request.message)

    content = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    response_text = ""
    tool_calls = []

    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=content,
    ):
        if not event or not event.content:
            continue

        for part in event.content.parts:
            if part.text:
                response_text += part.text
            elif part.function_call:
                tool_calls.append(part.function_call.name)

    # Save Agent Message
    chat_manager.add_message(session_id, "model", response_text)

    return {
        "response": response_text,
        "session_id": session_id,
        "user_id": user_id,
        "tool_calls": tool_calls,
    }


@app.get("/")
async def read_index():
    return FileResponse("src/ui/index.html")
