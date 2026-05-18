import openai
from config import MODELO_TRANSCRICAO, MODELO_CHAT

_client = openai.OpenAI()


def transcreve_audio(caminho_audio, language='pt', response_format='text'):
    with open(caminho_audio, 'rb') as arquivo_audio:
        transcricao = _client.audio.transcriptions.create(
            model=MODELO_TRANSCRICAO,
            language=language,
            response_format=response_format,
            file=arquivo_audio,
        )
    return transcricao


def chat_openai(mensagem, modelo=MODELO_CHAT):
    resposta = _client.chat.completions.create(
        model=modelo,
        messages=[{'role': 'user', 'content': mensagem}],
    )
    return resposta.choices[0].message.content
