import queue as q
import numpy as np
import sounddevice as sd
import pydub

SAMPLE_RATE = 16000
CHANNELS = 1


class GravadorAudio:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self._queue = q.Queue()
        self._stream = None

    def iniciar(self):
        self._stream = sd.InputStream(
            device=self.device_id,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
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

    def get_frames(self):
        frames = []
        try:
            while True:
                frames.append(self._queue.get_nowait())
        except q.Empty:
            pass
        return frames

    @staticmethod
    def frames_para_audio(frames):
        if not frames:
            return pydub.AudioSegment.empty()
        data = np.concatenate(frames, axis=0)
        return pydub.AudioSegment(
            data=data.tobytes(),
            sample_width=2,
            frame_rate=SAMPLE_RATE,
            channels=CHANNELS,
        )


def listar_dispositivos_entrada():
    devices = sd.query_devices()
    return {
        i: d['name']
        for i, d in enumerate(devices)
        if d['max_input_channels'] > 0
    }
