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
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.adk.errors.already_exists_error import AlreadyExistsError
from google.genai import types

app = FastAPI()

# Initialize stores
# We need to make sure we are in the root directory when initializing stores
# so they find the correct paths (./chroma_db, ./user_data.json)
# This assumes the app is run from the project root.

user_store = UserStore()
vector_store = VectorStore()

# Initialize ADK Runner
session_service = SqliteSessionService("chat_sessions.db")
adk_app = App(name=root_agent.name, root_agent=root_agent)
runner = Runner(app=adk_app, session_service=session_service)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str | None = None


@app.get("/api/user")
async def get_user_profile():
    return user_store.get_profile()


@app.get("/api/vocabulary")
async def get_vocabulary():
    vocab = vector_store.get_all_phrases()
    # Deserialize references if present
    for item in vocab:
        if "references" in item["metadata"]:
            try:
                item["metadata"]["references"] = json.loads(
                    item["metadata"]["references"]
                )
            except Exception:
                item["metadata"]["references"] = []

    # Sort by created_at descending (newest first)
    vocab.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
    return vocab


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
    # app_name is available via runner.app.name if not exposed directly
    app_name = runner.app.name
    response = await session_service.list_sessions(app_name=app_name)

    result = []
    for s in response.sessions:
        result.append(
            {
                "id": s.id,
                "title": f"Session {s.id[:8]}...",
                "created_at": datetime.fromtimestamp(s.last_update_time).isoformat(),
                "msg_count": 0,  # Not available in list summary
            }
        )
    # Sort by created_at descending
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return result


@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    app_name = runner.app.name
    session = await session_service.get_session(
        app_name=app_name,
        user_id="default_user",  # Backend default
        session_id=session_id,
    )

    if not session:
        return []

    messages = []
    current_msg = None

    for event in session.events:
        if not event.content:
            continue

        role = event.content.role

        # Extract content
        text = ""
        tools = []
        for part in event.content.parts:
            if part.text:
                text += part.text
            elif part.function_call:
                tools.append(
                    {"name": part.function_call.name, "args": part.function_call.args}
                )

        if not text and not tools:
            continue

        # Merge Logic
        if current_msg and current_msg["role"] == role:
            current_msg["text"] += text
            current_msg["tool_calls"].extend(tools)
            # Typically keep timestamp of first event in turn
        else:
            if current_msg:
                messages.append(current_msg)

            current_msg = {
                "role": role,
                "text": text,
                "tool_calls": tools,
                "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
            }

    if current_msg:
        messages.append(current_msg)

    return messages


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_id = request.user_id or "default_user"
    session_id = request.session_id or str(uuid.uuid4())

    # Update streak
    user_store.update_streak()

    # Ensure session exists in SQLite
    try:
        await session_service.create_session(
            state={}, app_name=runner.app.name, user_id=user_id, session_id=session_id
        )
    except AlreadyExistsError:
        pass  # Session already exists, we can continue

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
                tool_calls.append(
                    {"name": part.function_call.name, "args": part.function_call.args}
                )

    return {
        "response": response_text,
        "session_id": session_id,
        "user_id": user_id,
        "tool_calls": tool_calls,
    }


@app.get("/")
async def read_index():
    return FileResponse("src/ui/index.html")
