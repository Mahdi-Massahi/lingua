# Lingua

Lingua is an AI-powered language learning application designed to help you master new languages through interactive conversations and personalized vocabulary management.

## Features

- **AI Tutor**: Powered by Google's **Gemini 3 Flash** model for natural and adaptive learning conversations.
- **Vocabulary Manager**: Automatically track and review new words you learn during conversations.
- **Pronunciation**: Integrated Text-to-Speech (gTTS) to help with pronunciation.
- **Personalized Learning**: Adapts to your learning style and progress.

## Tech Stack

- **Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/generative-ai-python)
- **LLM**: Google Gemini 3 Flash Preview
- **Database**: ChromaDB (Vector Store)
- **Audio**: gTTS (Google Text-to-Speech)

## Getting Started

### Prerequisites

- Python 3.12+
- A Google Cloud Project with Gemini API access

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mahdi-Massahi/lingua.git
    cd lingua
    ```

2.  **Install dependencies:**
    This project uses `uv` for dependency management.
    ```bash
    # Install dependencies
    uv sync
    ```

3.  **Configure Environment:**
    Copy the example environment file and add your API key.
    ```bash
    cp .env.example .env
    ```
    Open `.env` and paste your `GEMINI_API_KEY`.

### Usage

Run the application:

```bash
python main.py
```

## Project Structure

- `src/agents/`: Contains the AI agent logic and tools.
- `src/agents/memory/`: Handles data persistence using ChromaDB.
- `main.py`: Entry point of the application.
