from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

PASTA_ARQUIVOS = Path(__file__).parent / 'arquivos'
PASTA_ARQUIVOS.mkdir(exist_ok=True)

MODELO_TRANSCRICAO = 'whisper-1'
MODELO_CHAT = 'gpt-3.5-turbo-1106'
INTERVALO_TRANSCRICAO = 5  # segundos entre cada chamada ao Whisper

PROMPT_RESUMO = '''
Faça o resumo do texto delimitado por ####
O texto é a transcrição de uma reunião.
O resumo deve contar com os principais assuntos abordados.
O resumo deve ter no máximo 300 caracteres.
O resumo deve estar em texto corrido.
No final, devem ser apresentados todos acordos e combinados
feitos na reunião no formato de bullet points.

O formato final que eu desejo é:

Resumo reunião:
- escrever aqui o resumo.

Acordos da Reunião:
- acordo 1
- acordo 2
- acordo n

texto: ####{}####
'''
