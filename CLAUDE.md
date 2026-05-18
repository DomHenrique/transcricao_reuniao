# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MeetGPT** — a Streamlit web app that records meeting audio via WebRTC, transcribes it in real-time using OpenAI Whisper, and generates Portuguese-language summaries with ChatGPT.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Environment

Fill in `.env` before running:

```
OPENAI_API_KEY=your_key_here
```

## Structure

```
app.py              # entry point — mounts the two Streamlit tabs
config.py           # all constants: paths, model names, prompt, interval
services/
  openai_client.py  # transcreve_audio() and chat_openai()
  storage.py        # salva_arquivo(), le_arquivo(), listar_reunioes()
ui/
  tab_gravar.py     # recording tab + audio chunk processing
  tab_selecao.py    # meeting selection, title saving, summary display
arquivos/           # runtime data — one timestamped folder per meeting
```

## Architecture

Two Streamlit tabs, each in its own module:

**"Gravar Reunião"** (`ui/tab_gravar.py`)
- Captures audio via `streamlit_webrtc` (WebRTC, audio-only)
- Every `INTERVALO_TRANSCRICAO` seconds (default 5 s) exports the current chunk to `audio_temp.mp3` and calls Whisper
- Appends the partial transcription to `transcricao.txt` and the full audio to `audio.mp3`

**"Ver transcrições salvas"** (`ui/tab_selecao.py`)
- Lists meetings from `arquivos/` via `listar_reunioes()`
- On first view of a titled meeting, lazily generates a GPT summary and writes `resumo.txt`

### Meeting folder layout

```
arquivos/2024_01_15_14_30_00/
├── audio.mp3        # full recording
├── audio_temp.mp3   # last transcription chunk (overwritten each cycle)
├── titulo.txt       # user-provided title
├── transcricao.txt  # Whisper output (Portuguese)
└── resumo.txt       # ChatGPT summary + action items (generated on first view)
```

### Configuration (`config.py`)

| Constant | Purpose |
|---|---|
| `PASTA_ARQUIVOS` | Base directory for meeting storage |
| `MODELO_TRANSCRICAO` | Whisper model (`whisper-1`) |
| `MODELO_CHAT` | Chat model (`gpt-3.5-turbo-1106`) |
| `INTERVALO_TRANSCRICAO` | Seconds between Whisper calls |
| `PROMPT_RESUMO` | ChatGPT prompt for summary generation |

## Notes

- On Linux/Mac, FFmpeg must be installed separately (`apt install ffmpeg` / `brew install ffmpeg`). The `ffmpeg.exe` in the repo is a Windows binary.
- All UI text, prompts, and file content are in Portuguese (pt-BR).
- No test suite — validate changes by running the app manually in a browser.
