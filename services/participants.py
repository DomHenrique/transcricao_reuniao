import base64
from io import BytesIO

import mss
import openai
from PIL import Image

from config import MODELO_VISAO

_client = openai.OpenAI()

_PROMPT = (
    'Esta é uma captura de tela de uma reunião virtual (Zoom, Google Meet, Teams, etc.). '
    'Liste apenas os nomes dos participantes visíveis na tela (painéis de participantes, '
    'tiles de vídeo, etc.). Retorne somente os nomes, um por linha, sem numeração ou '
    'explicações. Se não encontrar nenhum nome, retorne exatamente: NENHUM'
)


def capturar_participantes(monitor=1):
    with mss.mss() as sct:
        raw = sct.grab(sct.monitors[monitor])
        img = Image.frombytes('RGB', raw.size, raw.bgra, 'raw', 'BGRX')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    resposta = _client.chat.completions.create(
        model=MODELO_VISAO,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': _PROMPT},
                {'type': 'image_url', 'image_url': {
                    'url': f'data:image/png;base64,{img_b64}',
                    'detail': 'low',
                }},
            ],
        }],
        max_tokens=200,
    )

    resultado = resposta.choices[0].message.content.strip()
    if resultado.upper() == 'NENHUM':
        return []
    return [nome.strip() for nome in resultado.splitlines() if nome.strip()]
