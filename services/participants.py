import base64
import subprocess
import re
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


def listar_janelas():
    """Retorna um dicionário {window_id: window_name} das janelas visíveis no X11."""
    try:
        output = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
    except Exception:
        return {}

    windows = {}
    for line in output.splitlines():
        m = re.search(r'(0x[0-9a-fA-F]+)\s+"([^"]+)"', line)
        if m:
            wid, name = m.groups()
            # Ignorar janelas internas invisíveis/escondidas do sistema
            if not name or name.isspace() or name in ['mutter guard window', 'Chromium clipboard']:
                continue
            
            # Checar tamanho
            try:
                geo_out = subprocess.check_output(['xwininfo', '-id', wid], text=True)
                w, h = 0, 0
                for geo_line in geo_out.splitlines():
                    if geo_line.strip().startswith('Width:'):
                        w = int(geo_line.split(':')[1].strip())
                    elif geo_line.strip().startswith('Height:'):
                        h = int(geo_line.split(':')[1].strip())
                
                # Considera apenas janelas maiores que 300x300
                if w > 300 and h > 300:
                    windows[wid] = name
            except Exception:
                pass
                
    return windows


def get_window_bbox(wid):
    """Pega o bounding box de uma janela via xwininfo."""
    try:
        output = subprocess.check_output(['xwininfo', '-id', wid], text=True)
        geo = {}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith('Absolute upper-left X:'): geo['left'] = int(line.split(':')[1].strip())
            elif line.startswith('Absolute upper-left Y:'): geo['top'] = int(line.split(':')[1].strip())
            elif line.startswith('Width:'): geo['width'] = int(line.split(':')[1].strip())
            elif line.startswith('Height:'): geo['height'] = int(line.split(':')[1].strip())
        return geo
    except Exception:
        return None


def capturar_participantes(window_id=None, monitor=1):
    with mss.mss() as sct:
        bbox = None
        if window_id:
            bbox = get_window_bbox(window_id)
        
        if bbox:
            raw = sct.grab(bbox)
        else:
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
