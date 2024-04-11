import streamlit as st

st.set_page_config(page_title='Nubank Finança Pessoal', layout='wide')

texto = '''
    # :violet[Nubank] Finança Pessoal
    
    ##### Aplicação com o intuito de auxiliar no geranciamento de sua finança pessoal no aplicativo da :violet[Nubank], <br> principalmente para aqueles que a tem como sua principalidade.

    ##### Sobre o menu de navegação de páginas ao lado:
    
    1. **Geranciador de Arquivos:**   
        Na página de **Gerenciamento de Arquivos**, você deverá **carregar e/ou excluir arquivos**, esses arquivos serão responsáveis pelos dados visualizados nas outras 2 páginas (Extrato e Fatura).   
        Esses arquivos nada mais são que seu **extrato da conta** e **fatura do crédito**,   
        
        O primeiro pode ser pedido no aplicativo da :violet[Nubank], que chegando no seu email você deverá escolher o arquivo no formato csv para baixar e carregá-lo na aba correspondente. <br>
        &nbsp;&nbsp;&nbsp;&nbsp; Se ainda restar dúvidas de como pedir o extrato tal [link](https://blog.nubank.com.br/extrato-nubank-veja-como-tirar-no-app/) poderá ser útil.

        O segundo pode ser pedido no site da :violet[Nubank], que baixando o arquivo no formato csv o mesmo deverá ser carregado na aba correspondente. <br>
        &nbsp;&nbsp;&nbsp;&nbsp; [Link](https://app.nubank.com.br/beta/credit-card/bills/) para pedir a fatura de crédito.

        > ⚠️ IMPORTANTE  
        > Para que o objetivo da aplicação seja de auxiliar no gerenciamento de sua finança pessoal:   
            **Os arquivo de extratos da conta deverão ser carregado na aba correspondente à "Extratos da Conta"**   
            **Os arquivo de fatura de crédito deverão ser carregado na aba correspondente à "Fatura de Crédito"**
        
        Use a divisão "Excluir Arquivos" para excluir arquivos carregados, quando necessário.

        > 📃 NOTA  
        > Sempre use o botão "Atualizar Base de Dados" para atualizar os dados após carregamento e/ou exclusão de arquivos.

    
    2. **Dashboards:**   
        Com os arquivos carregados e a atualização da base dados feita, será possível ver os cálculos e análises nas 2 páginas de Dashboards.   
        Nas visualizações de tabelas passe o mouse no nome das coluna para ver mais detalhes sobre elas.   

        Páginas de Dashboards:   
        - **Extrato**:   
            Essa página será responsável por lhe mostrar cálculos e análises referentes ao seu extrato da conta.
        - **Fatura:**   
            Essa página será responsável por lhe mostrar cálculos e análises referentes à sua fatura de crédito.
'''

st.markdown(texto, unsafe_allow_html=True)
