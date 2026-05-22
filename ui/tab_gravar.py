import time
import threading
from datetime import datetime

import pydub
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import PASTA_ARQUIVOS, INTERVALO_TRANSCRICAO, INTERVALO_PARTICIPANTES
from services.audio_capture import GravadorAudio, listar_dispositivos_entrada
from services.openai_client import transcreve_audio
from services.participants import capturar_participantes, listar_janelas
from services.storage import salva_arquivo


class _EstadoGravacao:
    def __init__(self):
        self._lock = threading.Lock()
        self.transcricao = ''
        self.participantes = []
        self.volume = 0.0
        self.erro = None
        self._ativo = True

    def parar(self):
        with self._lock:
            self._ativo = False

    def esta_ativo(self):
        with self._lock:
            return self._ativo

    def set_transcricao(self, texto):
        with self._lock:
            self.transcricao = texto

    def set_participantes(self, nomes):
        with self._lock:
            self.participantes = list(nomes)

    def get_transcricao(self):
        with self._lock:
            return self.transcricao

    def get_participantes(self):
        with self._lock:
            return list(self.participantes)


def _loop_gravacao(estado, device_id, pasta_reuniao, capturar_nomes, window_id=None):
    gravador = GravadorAudio(device_id=device_id)
    try:
        gravador.iniciar()
    except Exception as e:
        estado.erro = f"Dispositivo indisponível ou erro no áudio: {e}"
        estado.parar()
        return

    ultima_transcricao = time.time()
    ultimo_participantes = time.time()
    audio_completo = pydub.AudioSegment.empty()
    audio_chunk = pydub.AudioSegment.empty()
    transcricao = ''

    while estado.esta_ativo():
        estado.volume = gravador.current_volume
        frames = gravador.get_frames()
        if frames:
            novo = gravador.frames_para_audio(frames)
            audio_completo += novo
            audio_chunk += novo
            audio_completo.export(pasta_reuniao / 'audio.mp3')

        agora = time.time()

        if len(audio_chunk) > 0 and agora - ultima_transcricao > INTERVALO_TRANSCRICAO:
            ultima_transcricao = agora
            audio_chunk.export(pasta_reuniao / 'audio_temp.mp3')
            transcricao += transcreve_audio(pasta_reuniao / 'audio_temp.mp3')
            estado.set_transcricao(transcricao)
            salva_arquivo(pasta_reuniao / 'transcricao.txt', transcricao)
            audio_chunk = pydub.AudioSegment.empty()

        if capturar_nomes and agora - ultimo_participantes > INTERVALO_PARTICIPANTES:
            ultimo_participantes = agora
            try:
                nomes = capturar_participantes(window_id=window_id)
                if nomes:
                    estado.set_participantes(nomes)
                    salva_arquivo(pasta_reuniao / 'participantes.txt', '\n'.join(nomes))
            except Exception:
                pass

        time.sleep(0.2)

    gravador.parar()


def tab_grava_reuniao():
    if 'gravando' not in st.session_state:
        st.session_state.gravando = False

    dispositivos = listar_dispositivos_entrada()

    device_label = st.selectbox(
        'Dispositivo de áudio',
        options=list(dispositivos.values()),
        disabled=st.session_state.gravando,
        help=(
            'Para capturar todos os participantes, selecione um dispositivo de loopback '
            '(ex: "Monitor of ...", "Stereo Mix" ou similar). '
            'No Linux: ative o monitor do PulseAudio/PipeWire nas configurações de som.'
        ),
    )
    device_id = next(k for k, v in dispositivos.items() if v == device_label)

    capturar_nomes = st.toggle(
        '👥 Detectar participantes via screenshot',
        value=False,
        disabled=st.session_state.gravando,
        help='Captura a tela a cada 30s e usa IA para identificar nomes visíveis na reunião. Requer X11 no Linux.',
    )

    window_id = None
    if capturar_nomes:
        janelas = listar_janelas()
        opcoes = ["Tela Inteira"] + list(janelas.values())
        janela_label = st.selectbox(
            'Janela alvo para captura',
            options=opcoes,
            disabled=st.session_state.gravando
        )
        if janela_label != "Tela Inteira":
            window_id = next(k for k, v in janelas.items() if v == janela_label)

    col1, col2 = st.columns(2)
    with col1:
        if st.button('▶ Iniciar', disabled=st.session_state.gravando, use_container_width=True):
            pasta_reuniao = PASTA_ARQUIVOS / datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            pasta_reuniao.mkdir()
            estado = _EstadoGravacao()
            st.session_state.estado_gravacao = estado
            st.session_state.gravando = True
            threading.Thread(
                target=_loop_gravacao,
                args=(estado, device_id, pasta_reuniao, capturar_nomes, window_id),
                daemon=True,
            ).start()
            st.rerun()

    with col2:
        if st.button('⏹ Parar', disabled=not st.session_state.gravando, use_container_width=True):
            st.session_state.estado_gravacao.parar()
            st.session_state.gravando = False
            st.rerun()

    if st.session_state.gravando:
        estado = st.session_state.estado_gravacao

        if estado.erro:
            st.error(estado.erro)
            st.session_state.gravando = False
            time.sleep(2)
            st.rerun()

        st_autorefresh(interval=800, key='refresh_gravacao')

        st.progress(estado.volume, text='🔊 Nível de Áudio captado')

        participantes = estado.get_participantes()
        if participantes:
            with st.expander('👥 Participantes detectados', expanded=True):
                for nome in participantes:
                    st.markdown(f'- {nome}')

        st.markdown('**Transcrição em tempo real:**')
        transcricao = estado.get_transcricao()
        st.markdown(transcricao if transcricao else '_Aguardando áudio..._')
