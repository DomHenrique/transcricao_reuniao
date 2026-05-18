import streamlit as st

from ui.tab_gravar import tab_grava_reuniao
from ui.tab_selecao import tab_selecao_reuniao


def main():
    st.header('Bem-vindo ao MeetGPT 🎙️', divider=True)
    tab_gravar, tab_selecao = st.tabs(['Gravar Reunião', 'Ver transcrições salvas'])
    with tab_gravar:
        tab_grava_reuniao()
    with tab_selecao:
        tab_selecao_reuniao()


if __name__ == '__main__':
    main()
