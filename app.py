import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb
import locale

def formatar_dinheiro(valor):
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    return 'R$ ' + locale.currency(valor, grouping=True, symbol=None)

def colorir_celula(valor):
    if valor > 0:
        return 'background-color: rgba(144, 238, 144, 0.3)'
    else:
        return 'background-color: rgba(255, 160, 122, 0.3)'

con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Nubank Finança Pessoal', layout='wide')

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
    ,   categoria
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

mes = st.sidebar.selectbox('mês', df['mes'].unique())

st.markdown(f'### Transações do Mês {mes}')
df = df[df['mes'] == mes][['data', 'categoria', 'top', 'valor', 'valor_acumulado', 'descricao']]

df = df.style.applymap(colorir_celula, subset=['valor', 'valor_acumulado'])
df = df.format({'valor': formatar_dinheiro, 'valor_acumulado': formatar_dinheiro})
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={
                'top': st.column_config.TextColumn(
                    'Top 10',
                    help='⭐ indica as 10 transações com maiores valores'
                ),
             })

######################################################################

st.divider()
st.markdown('### Cálculos Mensais')

col1, col2 = st.columns(2)
col3, col4, col5 = st.columns(3)

col1.markdown('### Saldo')
col2.markdown('### Movimentações')
col3.markdown('### Categorias')

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,	sum(if(descricao not in ('Aplicação RDB'), valor, 0)) as para_investir
    ,	abs(sum(if(descricao in ('Aplicação RDB', 'Resgate RDB'), valor, 0))) as investido
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

df = df.style.applymap(colorir_celula, subset=['para_investir', 'investido', 'entrada', 'saida', 'saldo_mes'])
df = df.format({'para_investir': formatar_dinheiro, 'investido': formatar_dinheiro, 'entrada': formatar_dinheiro, 'saida': formatar_dinheiro, 'saldo_mes': formatar_dinheiro})
col1.dataframe(df, use_container_width=True, hide_index=True)

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,   if(valor > 0, 'Entrada', 'Saída') as movimentacao
    ,   abs(sum(valor)) as valor
    from 
        extract
    group by 
        1, 2
    union
    select 
        date_trunc('month', data) as mes
    ,   'Investido' as movimentacao
    ,   abs(sum(valor)) as valor
    from 
        extract
    where 
        descricao in ('Aplicação RDB', 'Resgate RDB')
    group by 
        1, 2
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date
df = df.sort_values('movimentacao')

colors = {'Entrada': '#90EE90', 'Saída': '#FFA07A'}
categoria_movimentacao = px.bar(df, x='mes', y='valor', color='movimentacao', 
                         barmode='group', color_discrete_map=colors)

col2.plotly_chart(categoria_movimentacao)

######################################################################

query = """
    select
        date_trunc('month', data) as mes
    ,   categoria
    ,   count(*) as quantidade
    ,   sum(valor) as valor
    from 
        extract
    group by 
        1, 2
"""

df = con.sql(query).fetchdf()
df['mes'] = df['mes'].dt.date

soma_por_categoria = df.groupby('categoria')['valor'].sum().reset_index()
soma_por_categoria['valor'] = soma_por_categoria['valor'].abs()
categorias_ordenadas = soma_por_categoria.sort_values(by='valor', ascending=False)['categoria']

categoria_mes = px.bar(df, x='mes', y='valor', color='categoria', 
                       barmode='group', category_orders={'categoria': categorias_ordenadas})
col3.plotly_chart(categoria_mes)

######################################################################

con.close()
