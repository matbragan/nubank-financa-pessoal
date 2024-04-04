import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb

from pages.utils.paines import formatar_dinheiro, colorir_celula_valor


con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Fatura de Crédito', layout='wide')

######################################################################

query = """
    select distinct
        date_trunc('month', data) as mes
    from
        invoice
"""

df = con.sql(query).fetchdf().sort_values(['mes'])
df['mes'] = df['mes'].dt.date

meses = df['mes'].unique()

mes_tabela = st.sidebar.selectbox('Mês da Tabela', meses, index=len(meses) - 1)

ultimos_meses = df['mes'].to_list()[-8:]
meses_graficos = st.sidebar.multiselect('Meses dos Gráficos', meses, default=ultimos_meses)

######################################################################

query = """
    with aux as (
        select 
            *
        ,   rank() over (partition by date_trunc('month', data) order by abs(valor) desc) as top
        from
            invoice
    )
    select 
        date_trunc('month', data) as mes
    ,   data
    ,   categoria
    ,   valor as valor
    ,   titulo
    ,   case
            when top <= 3 then '⭐⭐⭐'
            when top <= 6 then '⭐⭐'
            when top <= 10 then '⭐'
            else ''
        end as top
    from 
        aux
"""

df = con.sql(query).fetchdf().sort_values(['data'])
df['data'] = df['data'].dt.date
df['mes'] = df['mes'].dt.date


df = df[df['mes'] == mes_tabela][['data', 'titulo', 'top', 'valor', 'categoria']]

df = df.style.map(colorir_celula_valor, subset=['valor'])
df = df.format({'valor': formatar_dinheiro})

st.markdown(f'#### Tabela')
st.markdown(f'##### Fatura do Mês {mes_tabela}')
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={
                'data': 'Data',
                'titulo': 'Título',
                'top': st.column_config.TextColumn(
                    'Top 10',
                    help='⭐ indica as 10 transações com maiores valores'
                ),
                'valor': 'Valor',
                'categoria': 'Categoria'
             })

######################################################################

st.divider()

st.markdown(f'#### Gráficos')
col1, col2 = st.columns(2)

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,   sum(if(valor < 0, valor, 0)) as gastos
    ,   sum(if(valor > 0, valor, 0)) as pagamento_fatura
    ,   sum(valor) as saldo_mes
    from 
        invoice
    group by 
        1
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date
df = df[df['mes'].isin(meses_graficos)]

total_gastos = df['gastos'].sum()
total_pagamento_fatura = df['pagamento_fatura'].sum()
total_saldo_mes = df['saldo_mes'].sum()

total_df = pd.DataFrame({'mes': ['Total'], 
                          'gastos': [total_gastos], 
                          'pagamento_fatura': [total_pagamento_fatura], 
                          'saldo_mes': [total_saldo_mes]})

df_com_total = pd.concat([df, total_df], ignore_index=True)

style_df = df_com_total.style.map(colorir_celula_valor, subset=['gastos', 'pagamento_fatura', 'saldo_mes'])
style_df = style_df.format({'gastos': formatar_dinheiro, 'pagamento_fatura': formatar_dinheiro, 'saldo_mes': formatar_dinheiro})

col1.markdown('##### Saldos Mensais')
col1.dataframe(style_df, use_container_width=True, hide_index=True,
               column_config={
                  'mes': 'Mês',
                  'gastos': 'Gastos',
                  'pagamento_fatura': 'Pagamento da Fatura',
                  'saldo_mes': 'Saldo do Mês'
               })

######################################################################

df = df.melt(id_vars=['mes'], var_name='movimentacao', value_name='valor')
df = df[df['movimentacao'].isin(['gastos', 'pagamento_fatura', 'saldo_mes'])]
df['movimentacao'] = df['movimentacao'].replace({'gastos': 'Gastos', 'pagamento_fatura': 'Pagamento da Fatura', 'saldo_mes': 'Saldo do Mês'})
df['valor'] = df['valor'].abs()

colors = {'Gastos': '#008080', 'Pagamento da Fatura': '#90EE90', 'Saldo do Mês': '#FFDB99'}

col2.markdown('##### Movimentações Mensais')
fig = px.bar(df, x='mes', y='valor', color='movimentacao', 
             barmode='group', color_discrete_map=colors)

col2.plotly_chart(fig)

######################################################################

query = """
    select 
        date_trunc('month', data) as mes
    ,   abs(valor) as valor
    from 
        invoice
    where
        1=1 
        and valor < 0
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date
df = df[df['mes'].isin(meses_graficos)]

st.markdown('##### Distribuição dos Gastos Mensais')
fig = px.box(df, x='mes', y='valor', color_discrete_sequence=['#FF6347'])
st.plotly_chart(fig)

######################################################################

con.close()
