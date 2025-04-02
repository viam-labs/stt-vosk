#!/usr/bin/env bash
export PATH=$PATH:$HOME/.local/bin
VENV_NAME=".venv-build"

source $VENV_NAME/bin/activate

uv run --active pyinstaller --onefile --collect-all vosk --paths src src/main.py
tar -czvf dist/archive.tar.gz dist/main meta.json
