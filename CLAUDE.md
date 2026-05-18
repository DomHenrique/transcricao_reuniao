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
config.py           # all constants: paths, model names, prompts, intervals
services/
  openai_client.py  # transcreve_audio() and chat_openai()
  storage.py        # salva_arquivo(), le_arquivo(), listar_reunioes()
  audio_capture.py  # GravadorAudio class + listar_dispositivos_entrada()
  participants.py   # screenshot capture + OpenAI Vision for participant names
ui/
  tab_gravar.py     # recording tab — threading, device selection, live transcription
  tab_selecao.py    # meeting selection, title saving, summary + participants display
arquivos/           # runtime data — one timestamped folder per meeting
```

## Architecture

Two Streamlit tabs, each in its own module:

**"Gravar Reunião"** (`ui/tab_gravar.py`)
- User selects audio input device from all system devices (including loopback/monitor sources)
- `GravadorAudio` records via `sounddevice.InputStream` in a background thread with `_EstadoGravacao` for thread-safe state sharing
- Every `INTERVALO_TRANSCRICAO` seconds (default 5 s) exports the chunk to `audio_temp.mp3` and calls Whisper
- `streamlit-autorefresh` refreshes the UI every 3 s to show live transcription while the thread runs
- Optional: every `INTERVALO_PARTICIPANTES` seconds (default 30 s) takes a screenshot via `mss` and calls GPT-4o Vision to extract participant names

**"Ver transcrições salvas"** (`ui/tab_selecao.py`)
- Lists meetings from `arquivos/` via `listar_reunioes()`
- On first view lazily generates a GPT summary, prepending participant names if `participantes.txt` exists
- Displays participants, summary, and full transcription

### Meeting folder layout

```
arquivos/2024_01_15_14_30_00/
├── audio.mp3          # full recording
├── audio_temp.mp3     # last transcription chunk (overwritten each cycle)
├── titulo.txt         # user-provided title
├── transcricao.txt    # Whisper output (Portuguese)
├── participantes.txt  # detected participant names, one per line (optional)
└── resumo.txt         # ChatGPT summary + action items (generated on first view)
```

### Configuration (`config.py`)

| Constant | Purpose |
|---|---|
| `PASTA_ARQUIVOS` | Base directory for meeting storage |
| `MODELO_TRANSCRICAO` | Whisper model (`whisper-1`) |
| `MODELO_CHAT` | Chat model (`gpt-3.5-turbo-1106`) |
| `MODELO_VISAO` | Vision model for participant detection (`gpt-4o`) |
| `INTERVALO_TRANSCRICAO` | Seconds between Whisper calls (default 5) |
| `INTERVALO_PARTICIPANTES` | Seconds between screenshot captures (default 30) |
| `PROMPT_RESUMO` | ChatGPT prompt for summary generation |

## System dependencies

```bash
apt install ffmpeg libportaudio2   # Linux
brew install ffmpeg portaudio      # Mac
```

`libportaudio2` is required by `sounddevice`. `ffmpeg` is required by `pydub`.

## Capturing all meeting participants (loopback audio)

To capture audio from all meeting participants (not just the local microphone), select a loopback/monitor device in the "Dispositivo de áudio" dropdown:

- **Linux (PulseAudio/PipeWire):** Enable the monitor source in sound settings, then a "Monitor of ..." device will appear in the list
- **Windows:** Enable "Stereo Mix" in sound settings, or install VB-Cable
- **Mac:** Install BlackHole (`brew install blackhole-2ch`)

## Participant name detection

The feature uses `mss` for screenshots and requires X11. On Wayland (common on modern Linux), it may not work — run with `DISPLAY=:0` or use XWayland.

## Notes

- All UI text, prompts, and file content are in Portuguese (pt-BR).
- No test suite — validate changes by running the app manually in a browser.
