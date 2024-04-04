import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb

from pages.utils.paines import formatar_dinheiro, colorir_celula_investimento, colorir_celula_valor


con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Extrato da Conta', layout='wide')

######################################################################

query = """
    select distinct
        date_trunc('month', data) as mes
    from
        extract
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
            extract
    )
    select 
        id
    ,   date_trunc('month', data) as mes
    ,   data
    ,   tipo
    ,   valor
    ,   sum(valor) over (order by data, id) as valor_acumulado
    ,   descricao
    ,   case
            when top <= 3 then '⭐⭐⭐'
            when top <= 6 then '⭐⭐'
            when top <= 10 then '⭐'
            else ''
        end as top
    from 
        aux
"""

df = con.sql(query).fetchdf().sort_values(['data', 'id'])
df['data'] = df['data'].dt.date
df['mes'] = df['mes'].dt.date

df = df[df['mes'] == mes_tabela][['data', 'tipo', 'top', 'valor', 'valor_acumulado', 'descricao']]

df = df.style.map(colorir_celula_valor, subset=['valor', 'valor_acumulado'])
df = df.format({'valor': formatar_dinheiro, 'valor_acumulado': formatar_dinheiro})
df = df.map(colorir_celula_investimento, subset=['tipo'])

st.markdown(f'#### Tabela')
st.markdown(f'##### Extrato do Mês {mes_tabela}')
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={
                'data': 'Data',
                'tipo': 'Tipo',
                'top': st.column_config.TextColumn(
                    'Top 10',
                    help='⭐ indica as 10 transações com maiores valores'
                ),
                'valor': 'Valor',
                'valor_acumulado': 'Valor Acumulado',
                'descricao': 'Descrição'
             })

######################################################################

st.divider()

st.markdown(f'#### Gráficos')
col1, col2 = st.columns(2)

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,   sum(if(valor > 0, valor, 0)) as entrada
    ,	abs(sum(if(descricao in ('Aplicação RDB', 'Resgate RDB'), valor, 0))) as investido
    ,   sum(if(valor < 0, if(descricao not in ('Aplicação RDB'), valor, 0), 0)) as gastos
    ,   sum(if(valor < 0, valor, 0)) as saida
    ,   sum(valor) as saldo_mes
    from 
        extract
    group by 
        1
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date
df = df[df['mes'].isin(meses_graficos)]

total_entrada = df['entrada'].sum()
total_investido = df['investido'].sum()
total_gastos = df['gastos'].sum()
total_saida = df['saida'].sum()
total_saldo_mes = df['saldo_mes'].sum()

total_df = pd.DataFrame({'mes': ['Total'], 
                          'entrada': [total_entrada], 
                          'investido': [total_investido], 
                          'gastos': [total_gastos], 
                          'saida': [total_saida], 
                          'saldo_mes': [total_saldo_mes]})

df_com_total = pd.concat([df, total_df], ignore_index=True)

style_df = df_com_total.style.map(colorir_celula_valor, 
                                  subset=['entrada', 'investido', 'gastos', 'saida', 'saldo_mes'])
style_df = style_df.format({'entrada': formatar_dinheiro, 'investido': formatar_dinheiro, 
                            'gastos': formatar_dinheiro, 'saida': formatar_dinheiro, 
                            'saldo_mes': formatar_dinheiro})

col1.markdown('##### Saldos Mensais')
col1.dataframe(style_df, use_container_width=True, hide_index=True,
               column_config={
                  'mes': 'Mês',
                  'entrada': 'Entrada',
                  'investido': 'Investido',
                  'gastos': 'Gastos',
                  'saida': 'Saída',
                  'saldo_mes': 'Saldo do Mês'
               })

######################################################################

df = df.melt(id_vars=['mes'], var_name='movimentacao', value_name='valor')
df = df[df['movimentacao'].isin(['entrada', 'investido', 'gastos', 'saida'])]
df['movimentacao'] = df['movimentacao'].replace({'entrada': 'Entrada', 'investido': 'Investido', 
                                                 'gastos': 'Gastos', 'saida': 'Saída'})
df['valor'] = df['valor'].abs()

colors = {'Entrada': '#90EE90', 'Investido': '#FFDB99', 'Gastos': '#008080', 'Saída': '#FF6347'}

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
        extract
    where
        1=1 
        and valor < 0
        and descricao not in ('Aplicação RDB')
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date
df = df[df['mes'].isin(meses_graficos)]

st.markdown('##### Distribuição dos Gastos Mensais')
fig = px.box(df, x='mes', y='valor', color_discrete_sequence=['#FF6347'])
st.plotly_chart(fig)

######################################################################

con.close()
