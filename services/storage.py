from config import PASTA_ARQUIVOS


def salva_arquivo(caminho_arquivo, conteudo):
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)


def le_arquivo(caminho_arquivo):
    if not caminho_arquivo.exists():
        return ''
    try:
        with open(caminho_arquivo, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(caminho_arquivo, encoding='latin-1') as f:
            return f.read()


def listar_reunioes():
    pastas = sorted(PASTA_ARQUIVOS.glob('*'), reverse=True)
    reunioes_dict = {}
    for pasta_reuniao in pastas:
        data_reuniao = pasta_reuniao.stem
        ano, mes, dia, hora, minuto, seg = data_reuniao.split('_')
        label = f'{ano}/{mes}/{dia} {hora}:{minuto}:{seg}'
        titulo = le_arquivo(pasta_reuniao / 'titulo.txt')
        if titulo:
            label += f' - {titulo}'
        reunioes_dict[data_reuniao] = label
    return reunioes_dict
