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
        return 'background-color: rgba(255, 255, 0, 0.3)'

con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Nubank Finança Pessoal', layout='wide')

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

st.markdown(f'### Movimentações do Mês {mes}')
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

style_df = df.style.map(colorir_celula_valor, subset=['entrada', 'investido', 'gastos', 'saida', 'saldo_mes'])
style_df = style_df.format({'entrada': formatar_dinheiro, 'investido': formatar_dinheiro, 'gastos': formatar_dinheiro, 'saida': formatar_dinheiro, 'saldo_mes': formatar_dinheiro})
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
# 4 - GRAFICO DE BARRAS MOVIMENTACOES

df = df.melt(id_vars=['mes'], var_name='movimentacao', value_name='valor')
df = df[df['movimentacao'].isin(['entrada', 'investido', 'gastos', 'saida'])]
df['movimentacao'] = df['movimentacao'].replace({'entrada': 'Entrada', 'investido': 'Investido', 'gastos': 'Gastos', 'saida': 'Saída'})
df['valor'] = df['valor'].abs()

colors = {'Entrada': '#90EE90', 'Investido': '#FFDB99', 'Gastos': '#008080', 'Saída': '#FF6347'}
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
