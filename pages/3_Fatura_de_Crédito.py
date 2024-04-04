import streamlit as st
import plotly.express as px
import duckdb

con = duckdb.connect(database='finance.db')

st.set_page_config(page_title='Fatura de Crédito', layout='wide')