import os
import streamlit as st
import plotly.express as px
import duckdb
import locale

def formatar_dinheiro(valor):
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    return 'R$ ' + locale.currency(valor, grouping=True, symbol=None)

def colorir_celula_valor(valor):
    if valor > 0:
        return 'background-color: rgba(144, 238, 144, 0.3)'
    else:
        return 'background-color: rgba(255, 160, 122, 0.3)'
    
def colorir_celula_investimento(categoria):
    if categoria in ('Aplicação RDB', 'Resgate RDB'):
        return 'background-color: rgba(255, 255, 88, 0.4)'
    
def escrever_arquivos(arquivos, pasta):
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    for arquivo in arquivos:
        with open(os.path.join(pasta, arquivo.name), 'wb') as f:
            f.write(arquivo.getbuffer())

con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Nubank Finança Pessoal', layout='wide')

st.markdown('## Carregar Arquivos')
col0, col00 = st.columns(2)

extratos = col0.file_uploader('Extratos da Conta', type=['csv'], accept_multiple_files=True)
escrever_arquivos(extratos, './data/extracts')

invoices = col00.file_uploader('Faturas de Crédito', type=['csv'], accept_multiple_files=True)
escrever_arquivos(invoices, './data/invoices')

st.divider()

######################################################################
# 1 - TABELA TOTAL MES

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

mes = st.sidebar.selectbox('Mês', df['mes'].unique())

st.markdown(f'### Transações do Mês {mes}')
df = df[df['mes'] == mes][['data', 'categoria', 'top', 'valor', 'valor_acumulado', 'descricao']]

df = df.style.map(colorir_celula_valor, subset=['valor', 'valor_acumulado'])
df = df.format({'valor': formatar_dinheiro, 'valor_acumulado': formatar_dinheiro})
df = df.map(colorir_celula_investimento, subset=['categoria'])
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={
                'data': 'Data',
                'categoria': 'Categoria',
                'top': st.column_config.TextColumn(
                    'Top 10',
                    help='⭐ indica as 10 transações com maiores valores'
                ),
                'valor': 'Valor',
                'valor_acumulado': 'Valor Acumulado',
                'descricao': 'Descrição'
             })

######################################################################
# 2 - GRAFICO DE LINHAS MES

query = """
    select 
        date_trunc('month', data) as mes
    ,   data
    ,   sum(valor) as valor
    from 
        extract
    group by 
        1, 2
"""

df = con.sql(query).fetchdf().sort_values(['data'])
df['data'] = df['data'].dt.date
df['mes'] = df['mes'].dt.date

st.markdown(f'### Transações Diárias do Mês {mes}')
df = df[df['mes'] == mes]

fig = px.line(df, x='data', y='valor', color_discrete_sequence=['#FFA07A'])
st.plotly_chart(fig, use_container_width=True)

######################################################################

st.divider()

col1, col2 = st.columns(2)
col3, col4, col5 = st.columns(3)

col1.markdown('### Saldos Mensais')
col2.markdown('### Movimentações Mensais')
col3.markdown('### Categorias')

######################################################################
# 3 - TABELA SALDOS MENSAIS

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

df = df.style.map(colorir_celula_valor, subset=['para_investir', 'investido', 'entrada', 'saida', 'saldo_mes'])
df = df.format({'para_investir': formatar_dinheiro, 'investido': formatar_dinheiro, 'entrada': formatar_dinheiro, 'saida': formatar_dinheiro, 'saldo_mes': formatar_dinheiro})
col1.dataframe(df, use_container_width=True, hide_index=True,
               column_config={
                  'mes': 'Mês',
                  'para_investir': 'Para Investir',
                  'investido': 'Investido',
                  'entrada': 'Entrada',
                  'saida': 'Saída',
                  'saldo_mes': 'Saldo do Mês'
               })

######################################################################
# 4 - GRAFICO DE BARRAS MOVIMENTACOES

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
fig = px.bar(df, x='mes', y='valor', color='movimentacao', 
             barmode='group', color_discrete_map=colors)

col2.plotly_chart(fig)

######################################################################
# 5 - GRAFICO DE BARRAS CATEGORIAS

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

fig = px.bar(df, x='mes', y='valor', color='categoria', 
             barmode='group', category_orders={'categoria': categorias_ordenadas})
col3.plotly_chart(fig)

######################################################################

con.close()
