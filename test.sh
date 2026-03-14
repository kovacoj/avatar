#!/usr/bin/env bash

source ./config/.env

curl -X POST \
  'https://api.siemens.com/llm/v1/audio/transcriptions' \
  -H "Authorization: Bearer $SIEMENS_API_KEY" \
  -F "file=@./output/audio/anet.wav" \
  -F "model=whisper-large-v3-turbo" \
  -F "temperature=0.0" \
  -F "prompt=Please transcribe the following audio in the same language as the audio."
#   -F "language=cs" \
