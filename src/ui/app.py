from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from gtts import gTTS
import io
import os
import sys

# Add src to path to import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agents.memory.user_store import UserStore
from src.agents.memory.vector_store import VectorStore

app = FastAPI()

# Initialize stores
# We need to make sure we are in the root directory when initializing stores
# so they find the correct paths (./chroma_db, ./user_data.json)
# This assumes the app is run from the project root.

user_store = UserStore()
vector_store = VectorStore()


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


@app.get("/")
async def read_index():
    return FileResponse("src/ui/index.html")
