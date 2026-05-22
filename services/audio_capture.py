import queue as q
import numpy as np
import sounddevice as sd
import pydub

TARGET_SAMPLE_RATE = 16000  # taxa esperada pela API de transcrição
CHANNELS = 1


class GravadorAudio:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self._queue = q.Queue()
        self._stream = None
        self.sample_rate = None  # definida em iniciar()
        self.current_volume = 0.0

    def iniciar(self):
        # Usa a sample rate nativa do dispositivo para evitar
        # erros de "Invalid sample rate" no ALSA/PortAudio
        info = sd.query_devices(self.device_id, 'input')
        self.sample_rate = int(info['default_samplerate'])

        self._stream = sd.InputStream(
            device=self.device_id,
            channels=CHANNELS,
            samplerate=self.sample_rate,
            dtype='int16',
            callback=self._callback,
        )
        self._stream.start()

    def parar(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()

    def _callback(self, indata, frames, time_info, status):
        self._queue.put(indata.copy())
        # Calcula o volume atual (pico) normalizado de 0.0 a 1.0
        peak = np.max(np.abs(indata.astype(np.float32)))
        self.current_volume = float(np.clip(peak / 32768.0, 0.0, 1.0))

    def get_frames(self):
        frames = []
        try:
            while True:
                frames.append(self._queue.get_nowait())
        except q.Empty:
            pass
        return frames

    def frames_para_audio(self, frames):
        """Converte frames capturados em AudioSegment, reamostrando para 16 kHz."""
        if not frames:
            return pydub.AudioSegment.empty()
        data = np.concatenate(frames, axis=0)
        segment = pydub.AudioSegment(
            data=data.tobytes(),
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=CHANNELS,
        )
        # Resample para 16 kHz (exigido pela Whisper API)
        if self.sample_rate != TARGET_SAMPLE_RATE:
            segment = segment.set_frame_rate(TARGET_SAMPLE_RATE)
        return segment


def listar_dispositivos_entrada():
    devices = sd.query_devices()
    return {
        i: d['name']
        for i, d in enumerate(devices)
        if d['max_input_channels'] > 0
    }
