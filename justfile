#!/usr/bin/env just --justfile

set dotenv-load

_default:
    just --list

# run the main chatbot
run-chatbot:
    uv sync
    uv run adk web src --port 8080 --reload_agents

# run the custom UI
run-ui:
    uv sync
    uv run uvicorn src.ui.app:app --reload --port 8000
