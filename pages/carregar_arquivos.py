import os
import subprocess
import streamlit as st


def escrever_arquivos(arquivos, pasta):
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    for arquivo in arquivos:
        with open(os.path.join(pasta, arquivo.name), 'wb') as f:
            f.write(arquivo.getbuffer())


st.set_page_config(page_title='Arquivos - Nubank Finança Pessoal', layout='wide')

extratos = st.file_uploader('Extratos da Conta', type=['csv'], accept_multiple_files=True)
escrever_arquivos(extratos, './data/extracts')

invoices = st.file_uploader('Faturas de Crédito', type=['csv'], accept_multiple_files=True)
escrever_arquivos(invoices, './data/invoices')

st.divider()

st.markdown('''
            Após colocar os arquivos csvs de extrato e/ou fatura acima,
            clique no botão abaixo para atualizar os dados no dashboard.
            ''')

if st.button('Atualizar Dados no Dashboard'):
    resultado = subprocess.run(['python3', 'main.py'], capture_output=True, text=True)
    
    st.text(resultado.stdout)
    st.text(resultado.stderr)