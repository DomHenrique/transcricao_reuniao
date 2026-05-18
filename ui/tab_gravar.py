import time
import queue
from datetime import datetime

import pydub
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from config import PASTA_ARQUIVOS, INTERVALO_TRANSCRICAO
from services.openai_client import transcreve_audio
from services.storage import salva_arquivo


def _adiciona_chunk_audio(frames_de_audio, audio_chunk):
    for frame in frames_de_audio:
        sound = pydub.AudioSegment(
            data=frame.to_ndarray().tobytes(),
            sample_width=frame.format.bytes,
            frame_rate=frame.sample_rate,
            channels=len(frame.layout.channels),
        )
        audio_chunk += sound
    return audio_chunk


def tab_grava_reuniao():
    webrtc_ctx = webrtc_streamer(
        key='recebe_audio',
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        media_stream_constraints={'video': False, 'audio': True},
    )

    if not webrtc_ctx.state.playing:
        return

    container = st.empty()
    container.markdown('Comece a falar')

    pasta_reuniao = PASTA_ARQUIVOS / datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    pasta_reuniao.mkdir()

    ultima_transcricao = time.time()
    audio_completo = pydub.AudioSegment.empty()
    audio_chunk = pydub.AudioSegment.empty()
    transcricao = ''

    while True:
        if webrtc_ctx.audio_receiver:
            try:
                frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            except queue.Empty:
                time.sleep(0.1)
                continue

            audio_completo = _adiciona_chunk_audio(frames, audio_completo)
            audio_chunk = _adiciona_chunk_audio(frames, audio_chunk)

            if len(audio_chunk) > 0:
                audio_completo.export(pasta_reuniao / 'audio.mp3')
                agora = time.time()
                if agora - ultima_transcricao > INTERVALO_TRANSCRICAO:
                    ultima_transcricao = agora
                    audio_chunk.export(pasta_reuniao / 'audio_temp.mp3')
                    transcricao += transcreve_audio(pasta_reuniao / 'audio_temp.mp3')
                    salva_arquivo(pasta_reuniao / 'transcricao.txt', transcricao)
                    container.markdown(transcricao)
                    audio_chunk = pydub.AudioSegment.empty()
        else:
            break
