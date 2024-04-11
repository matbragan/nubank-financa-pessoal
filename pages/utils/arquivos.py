import os
import streamlit as st


def escrever_arquivos(pasta, arquivos):
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    for arquivo in arquivos:
        with open(os.path.join(pasta, arquivo.name), 'wb') as f:
            f.write(arquivo.getbuffer())
            st.success(f'O arquivo "{arquivo.name}" foi carregado com sucesso!', icon='✅')


def listar_arquivos(pasta):
    arquivos = os.listdir(pasta)
    arquivos = sorted(arquivos, key=lambda x: os.path.basename(x))
    return arquivos


def excluir_arquivo(pasta, arquivo):
    caminho_arquivo = os.path.join(pasta, arquivo)
    os.remove(caminho_arquivo)
    st.success(f'O arquivo "{arquivo}" foi excluído com sucesso!', icon='✅')


def mostrar_arquivos_selecionados(pasta):
    st.markdown('#### Clique no arquivo a ser excluído')
    arquivos = listar_arquivos(pasta)
    for arquivo in arquivos:
        if st.button(f'Excluir arquivo "{arquivo}"'):
            excluir_arquivo(pasta, arquivo)
    return arquivos