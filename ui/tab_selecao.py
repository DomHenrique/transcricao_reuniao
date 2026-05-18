import streamlit as st

from config import PASTA_ARQUIVOS, PROMPT_RESUMO
from services.openai_client import chat_openai
from services.storage import salva_arquivo, le_arquivo, listar_reunioes


def tab_selecao_reuniao():
    reunioes_dict = listar_reunioes()
    if not reunioes_dict:
        st.info('Nenhuma reunião gravada ainda.')
        return

    reuniao_selecionada = st.selectbox('Selecione uma reunião', list(reunioes_dict.values()))
    st.divider()

    reuniao_data = next(k for k, v in reunioes_dict.items() if v == reuniao_selecionada)
    pasta_reuniao = PASTA_ARQUIVOS / reuniao_data

    if not (pasta_reuniao / 'titulo.txt').exists():
        st.warning('Adicione um título para esta reunião')
        titulo = st.text_input('Título da reunião')
        st.button('Salvar', on_click=_salvar_titulo, args=(pasta_reuniao, titulo))
    else:
        _exibir_reuniao(pasta_reuniao)


def _salvar_titulo(pasta_reuniao, titulo):
    salva_arquivo(pasta_reuniao / 'titulo.txt', titulo)


def _exibir_reuniao(pasta_reuniao):
    titulo = le_arquivo(pasta_reuniao / 'titulo.txt')
    transcricao = le_arquivo(pasta_reuniao / 'transcricao.txt')
    resumo = le_arquivo(pasta_reuniao / 'resumo.txt')
    participantes = le_arquivo(pasta_reuniao / 'participantes.txt')

    if not resumo:
        with st.spinner('Gerando resumo...'):
            resumo = _gerar_resumo(pasta_reuniao, transcricao, participantes)

    st.markdown(f'## {titulo}')

    if participantes:
        with st.expander('👥 Participantes', expanded=True):
            for nome in participantes.splitlines():
                st.markdown(f'- {nome}')

    st.markdown(resumo)
    st.divider()
    st.markdown('**Transcrição completa:**')
    st.markdown(transcricao)


def _gerar_resumo(pasta_reuniao, transcricao, participantes=''):
    prompt = PROMPT_RESUMO.format(transcricao)
    if participantes:
        prompt = f'Participantes da reunião: {participantes}\n\n' + prompt
    resumo = chat_openai(mensagem=prompt)
    salva_arquivo(pasta_reuniao / 'resumo.txt', resumo)
    return resumo
