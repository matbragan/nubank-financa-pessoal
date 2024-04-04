import subprocess
import streamlit as st

from pages.utils.arquivos import mostrar_arquivos_selecionados, escrever_arquivos


st.set_page_config(page_title='Gerenciador de Arquivos', layout='wide')

######################################################################

st.markdown('### Após carregar e/ou excluir arquivos, clique no botão abaixo:')

if st.button('Atualizar Base de Dados'):
    try:
        resultado = subprocess.run(['python3', 'main.py'])
        st.success('Dados Atualizados com Sucesso!', icon='✅')
    except Exception as e:
        st.error(f'Erro ao Atualizar os Dados - {e}', icon='❌')

st.divider()

######################################################################

st.markdown('## Carregar Arquivos')

extratos = st.file_uploader('Extratos da Conta', type=['csv'], accept_multiple_files=True)
escrever_arquivos('./data/extracts', extratos)

faturas = st.file_uploader('Faturas de Crédito', type=['csv'], accept_multiple_files=True)
escrever_arquivos('./data/invoices', faturas)

st.divider()

######################################################################

st.markdown('## Excluir Arquivos')

pastas = {
    'Extratos da Conta': './data/extracts', 
    'Faturas de Crédito': './data/invoices'
}
pasta_selecionada = st.selectbox('Selecione a pasta:', pastas)

if pasta_selecionada:
    mostrar_arquivos_selecionados(pastas[pasta_selecionada])
