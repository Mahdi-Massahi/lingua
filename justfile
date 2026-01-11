#!/usr/bin/env just --justfile

set dotenv-load

_default:
    just --list

# run the main chatbot
run-chatbot:
    uv sync
    uv run adk web src --port 8080 --reload_agents
