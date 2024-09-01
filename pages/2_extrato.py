import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import duckdb

from pages.utils.paines import formatar_dinheiro, colorir_celula_investimento, colorir_celula_valor


con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Extrato da Conta', layout='wide')

######################################################################
# Criação dos filtros de meses

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

mes_tabela = st.sidebar.selectbox('Mês - Filtro Cálculos Diários', meses, index=len(meses) - 1)
meses_graficos = st.sidebar.multiselect('Meses - Filtro Cálculos Mensais', meses, default=ultimos_meses)

######################################################################
# Dados diários

st.markdown(f'#### Cálculos Diários')

###################################
# Tabela com todas as movimentações do mês

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

###################################
# Gráfico de barras/linhas de gastos diários

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
        and descricao not like '%RDB%'
        and descricao not like '%CDB%'
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
    xaxis_title='Dia', yaxis_title='Valor',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=0.15),
)

st.plotly_chart(fig, use_container_width=True)

######################################################################
# Dados mensais

st.divider()

st.markdown(f'#### Cálculos Mensais')

###################################
# Tabela com valores acumulados dos meses

query = """
    select
        date_trunc('month', data) as mes
    ,	sum(if(tipo in ('Aplicação RDB', 'Compra de CDB'), valor, 0))*-1 as aplicado
    ,	sum(if(tipo in ('Resgate RDB'), valor, 0))*-1 as resgatado
    ,	sum(if(tipo in ('Aplicação RDB', 'Compra de CDB', 'Resgate RDB'), valor, 0))*-1 as investido
    ,   sum(if(valor > 0 and tipo not in ('Resgate RDB'), valor, 0)) as ganhos
    ,   sum(if(valor < 0 and tipo not in ('Aplicação RDB', 'Compra de CDB'), valor, 0)) as gastos
    ,   sum(if(tipo not in ('Aplicação RDB', 'Compra de CDB', 'Resgate RDB'), valor, 0)) as sobras
    ,   sum(if(valor > 0, valor, 0)) as entrada
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

colunas = df.columns.tolist()
colunas.remove('mes')

totais = {coluna: df[coluna].sum() for coluna in colunas}

total_df = pd.DataFrame({'mes': ['Total'], **{coluna: [total] for coluna, total in totais.items()}})

df_com_total = pd.concat([df, total_df], ignore_index=True)

style_df = df_com_total.style.map(colorir_celula_valor, subset=colunas)
style_df = style_df.format({coluna: formatar_dinheiro for coluna in colunas})

st.markdown('##### Saldos Mensais')
st.checkbox('Use a largura do contêiner', value=False, key='use_container_width')
st.dataframe(style_df, use_container_width=st.session_state.use_container_width, 
             hide_index=True,
             column_config={
                 'mes': 'Mês',
                 'aplicado': st.column_config.Column(
                     'Aplicado',
                     help='Soma das aplicações RDB e CDB'
                 ),
                 'resgatado': st.column_config.Column(
                     'Resgatado',
                     help='Soma dos resgates RDB e CDB'
                 ),
                 'investido': st.column_config.Column(
                     'Investido',
                     help='O que de fato foi investido no mês, subtração do Aplicado com Resgatado'
                 ),
                 'ganhos': st.column_config.Column(
                     'Ganhos',
                     help='Soma de todos os ganhos do mês, valores positivos no extrato, tirando RDB e CDB'
                 ),
                 'gastos': st.column_config.Column(
                     'Gastos',
                     help='Soma de todos os gastos do mês, valores negativos no extrato, tirando RDB e CDB'
                 ),
                 'sobras': st.column_config.Column(
                     'Sobras',
                     help='O que sobrou no mês, subtração dos Ganhos com os Gastos'
                 ),
                 'entrada': st.column_config.Column(
                     'Entrada',
                     help='Soma de toda entrada do mês, valores positivos no extrato'
                 ),
                 'saida': st.column_config.Column(
                     'Saída',
                     help='Soma de toda saída do mês, valores negativos no extrato'
                 ),
                 'saldo_mes': st.column_config.Column(
                     'Saldo do Mês',
                     help='Soma de todos os valores do mês, subtração da Entrada com a Saída'
                 )
            })

###################################
# Divisão dos 2 próximos gráficos em 2 colunas

col1, col2 = st.columns(2)

###################################
# Grafico 1 - Gráfico de barras com alguns valores acumulados do mês

col1.markdown('##### Movimentações Mensais')

df = df.melt(id_vars=['mes'], var_name='movimentacao', value_name='valor')
df = df[df['movimentacao'].isin(['investido', 'ganhos', 'gastos', 'sobras'])]
df['movimentacao'] = df['movimentacao'].replace({'investido': 'Investido', 'ganhos': 'Ganhos', 
                                                 'gastos': 'Gastos', 'sobras': 'Sobras'})

col1.checkbox('Normalizar valores para positivos', value=False, key='normalizar_valores')
if st.session_state.normalizar_valores:
    df['valor'] = df['valor'].abs()

colors = {'Investido': '#FFDB99', 'Ganhos': '#90EE90', 'Gastos': '#FF6347', 'Sobras': '#008080'}

fig = px.bar(df, x='mes', y='valor', color='movimentacao',
             barmode='group', color_discrete_map=colors)
fig.update_layout(xaxis_title='Mês', yaxis_title='Valor')
col1.plotly_chart(fig, use_container_width=True)

###################################
# Grafico 2 - Boxplot com os gastos do mês

query = """
    select 
        date_trunc('month', data) as mes
    ,   abs(valor) as valor
    from 
        extract
    where
        1=1 
        and valor < 0
        and descricao not like '%RDB%'
        and descricao not like '%CDB%'
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
