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
            prompt="Transcrição de reunião profissional. Sem legendas automáticas ou agradecimentos de canal.",
            temperature=0.0
        )
    
    # Whisper commonly hallucinates YouTube captions on silent audio chunks
    hallucinations = [
        "Obrigado por assistir",
        "Inscreva-se no canal",
        "Deixe o seu like",
        "Amara.org",
        "Obrigado.",
        "Obrigada.",
        "Legendas",
        "Compartilhe",
    ]
    
    transcricao_limpa = transcricao.strip()
    # Verifica se a transcrição é apenas uma das alucinações (comum em áudio mudo)
    for h in hallucinations:
        if h.lower() in transcricao_limpa.lower() and len(transcricao_limpa) < 50:
            return ""
            
    return transcricao_limpa + " "


def chat_openai(mensagem, modelo=MODELO_CHAT):
    resposta = _client.chat.completions.create(
        model=modelo,
        messages=[{'role': 'user', 'content': mensagem}],
    )
    return resposta.choices[0].message.content
