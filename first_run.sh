#!/usr/bin/env bash

if command -v apt >/dev/null 2>&1; then
  sudo apt install -qqy --fix-missing python3-pyaudio portaudio19-dev alsa-tools alsa-utils flac python3-dev clang ffmpeg
fi

if command -v brew >/dev/null 2>&1; then
  brew install portaudio
fi
