import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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

meses = list(df['mes'])
ultimos_meses = meses[-8:]

######################################################################

st.markdown(f'#### Cálculos Diários')
mes_tabela = st.sidebar.selectbox('Mês - Filtro Cálculos Diários', meses, index=len(meses) - 1)

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

st.markdown(f'##### Extrato do Mês {mes_tabela}')
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={
                'data': 'Data',
                'tipo': 'Tipo',
                'top': st.column_config.Column(
                    'Top 10',
                    help='⭐ indica as 10 transações com maiores valores'
                ),
                'valor': 'Valor',
                'valor_acumulado': st.column_config.Column(
                    'Valor Acumulado',
                    help='Soma de todos os valores anteriores até então, começando com o primeiro extrato carregado'
                ),
                'descricao': 'Descrição'
             })

######################################################################

query = """
    select 
        date_trunc('month', data) as mes
    ,   data
    ,   count(id) as quantidade
    ,   abs(sum(valor)) as valor
    from
        extract
    where
        1=1 
        and valor < 0
        and descricao not in ('Aplicação RDB')
    group by 
        1, 2
"""

df = con.sql(query).fetchdf().sort_values(['data'])
df['data'] = df['data'].dt.date
df['mes'] = df['mes'].dt.date

df = df[df['mes'] == mes_tabela]

st.markdown(f'##### Gastos Diários do Mês {mes_tabela}')

fig = go.Figure()

fig.add_trace(go.Scatter(x=df['data'], y=df['valor'], mode='lines', name='Valor', line=dict(color='#FF6347')))

fig.add_trace(go.Bar(x=df['data'], y=df['quantidade'], name='Quantidade', marker_color='#1E90FF', yaxis='y2', opacity=0.4))

fig.update_layout(
    yaxis=dict(title='Valor'),
    yaxis2=dict(title='Quantidade', overlaying='y', side='right'),
    xaxis_title='Dia', yaxis_title='Valor'
)

st.plotly_chart(fig, use_container_width=True)

######################################################################

st.divider()

st.markdown(f'#### Cálculos Mensais')
meses_graficos = st.sidebar.multiselect('Meses - Filtro Cálculos Mensais', meses, default=ultimos_meses)

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,   sum(if(valor > 0, valor, 0)) as entrada
    ,	sum(if(descricao in ('Aplicação RDB'), valor, 0))*-1 as aplicado
    ,	sum(if(descricao in ('Resgate RDB'), valor, 0))*-1 as resgatado
    ,	sum(if(descricao in ('Aplicação RDB', 'Resgate RDB'), valor, 0))*-1 as investido
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
total_aplicado = df['aplicado'].sum()
total_resgatado = df['resgatado'].sum()
total_investido = df['investido'].sum()
total_gastos = df['gastos'].sum()
total_saida = df['saida'].sum()
total_saldo_mes = df['saldo_mes'].sum()

total_df = pd.DataFrame({'mes': ['Total'], 
                          'entrada': [total_entrada], 
                          'aplicado': [total_aplicado],
                          'resgatado': [total_resgatado],
                          'investido': [total_investido], 
                          'gastos': [total_gastos], 
                          'saida': [total_saida], 
                          'saldo_mes': [total_saldo_mes]})

df_com_total = pd.concat([df, total_df], ignore_index=True)

style_df = df_com_total.style.map(colorir_celula_valor, 
                                  subset=['entrada', 'aplicado', 'resgatado', 'investido', 
                                          'gastos', 'saida', 'saldo_mes'])
style_df = style_df.format({'entrada': formatar_dinheiro, 'investido': formatar_dinheiro,
                            'aplicado': formatar_dinheiro, 'resgatado': formatar_dinheiro, 
                            'gastos': formatar_dinheiro, 'saida': formatar_dinheiro, 
                            'saldo_mes': formatar_dinheiro})

st.markdown('##### Saldos Mensais')
st.checkbox('Use a largura do contêiner', value=False, key='use_container_width')
st.dataframe(style_df, use_container_width=st.session_state.use_container_width, 
             hide_index=True,
             column_config={
                 'mes': 'Mês',
                 'entrada': st.column_config.Column(
                     'Entrada',
                     help='Soma de toda entrada do mês, valores positivo no extrato'
                 ),
                 'aplicado': st.column_config.Column(
                     'Aplicado',
                     help='Soma das aplicações RDB (caixinhas)'
                 ),
                 'resgatado': st.column_config.Column(
                     'Resgatado',
                     help='Soma dos resgates RDB (caixinhas)'
                 ),
                 'investido': st.column_config.Column(
                     'Investido',
                     help='O que de fato foi investido no mês, subtração do Aplicado com Resgatado'
                 ),
                 'gastos': st.column_config.Column(
                     'Gastos',
                     help='Soma de todos os gastos do mês, valores negativo no extrato menos as Aplicações'
                 ),
                 'saida': st.column_config.Column(
                     'Saída',
                     help='Soma de toda saída do mês, valores negativo no extrato, soma dos Gastos com Aplicado'
                 ),
                 'saldo_mes': st.column_config.Column(
                     'Saldo do Mês',
                     help='Soma de todos os valores do mês, subtração da Entrada com a Saída'
                 )
            })

######################################################################

col1, col2 = st.columns(2)

######################################################################

df = df.melt(id_vars=['mes'], var_name='movimentacao', value_name='valor')
df = df[df['movimentacao'].isin(['entrada', 'investido', 'gastos', 'saida'])]
df['movimentacao'] = df['movimentacao'].replace({'entrada': 'Entrada', 'investido': 'Investido', 
                                                 'gastos': 'Gastos', 'saida': 'Saída'})
df['valor'] = df['valor'].abs()

colors = {'Entrada': '#90EE90', 'Investido': '#FFDB99', 'Gastos': '#008080', 'Saída': '#FF6347'}

col1.markdown('##### Movimentações Mensais')
fig = px.bar(df, x='mes', y='valor', color='movimentacao',
             barmode='group', color_discrete_map=colors)
fig.update_layout(xaxis_title='Mês', yaxis_title='Valor')
col1.plotly_chart(fig, use_container_width=True)

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

col2.markdown('##### Distribuição dos Gastos Mensais')
fig = px.box(df, x='mes', y='valor', color_discrete_sequence=['#FF6347'])
fig.update_layout(xaxis_title='Mês', yaxis_title='Valor')
col2.plotly_chart(fig, use_container_width=True)

######################################################################

con.close()
