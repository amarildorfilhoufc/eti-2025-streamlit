# app_dashboard_offline.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Função para carregar dados do Excel
@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados_acessos.xlsx")
    return df

# Início do app
st.set_page_config(page_title="Dashboard Moodle (Offline)", layout="wide")
st.title("📊 Dashboard de Acessos dos Alunos - Moodle (Offline)")

# Carregamento
with st.spinner("Carregando dados..."):
    df = carregar_dados()

df['access_time'] = pd.to_datetime(df['access_time'])

# Filtros laterais
st.sidebar.header("🔍 Filtros")

# Cursos únicos
cursos_disponiveis = sorted(df['course_name'].dropna().unique())
curso_selecionado = st.sidebar.multiselect("Curso(s)", cursos_disponiveis, default=cursos_disponiveis[:1])

# Datas
data_min = df['access_time'].dt.date.min()
data_max = df['access_time'].dt.date.max()
data_inicio, data_fim = st.sidebar.date_input("Período", [data_min, data_max], min_value=data_min, max_value=data_max)

# Filtragem
df_filtrado = df.copy()
if curso_selecionado:
    df_filtrado = df_filtrado[df_filtrado['course_name'].isin(curso_selecionado)]

df_filtrado = df_filtrado[
    (df_filtrado['access_time'].dt.date >= data_inicio) &
    (df_filtrado['access_time'].dt.date <= data_fim)
]

# Seção: Acessos por data
st.subheader(f"📅 Evolução dos Acessos ({data_inicio} a {data_fim})")
df_filtrado['data'] = df_filtrado['access_time'].dt.date
df_por_data = df_filtrado.groupby(['course_name', 'data']).size().reset_index(name='qtd_acessos')
fig_data = px.line(df_por_data, x='data', y='qtd_acessos', color='course_name',
                   title="Acessos por Data", markers=True)
st.plotly_chart(fig_data, use_container_width=True)

# Seção: Top 10 Alunos
st.subheader("👤 Top 10 Alunos por Acessos")
df_filtrado['aluno'] = df_filtrado['firstname'] + ' ' + df_filtrado['lastname']
df_top = df_filtrado.groupby('aluno').size().reset_index(name='qtd_acessos')
df_top = df_top.sort_values('qtd_acessos', ascending=False).head(10)
fig_top = px.bar(df_top, x='aluno', y='qtd_acessos', title="Top 10 Alunos", text='qtd_acessos')
st.plotly_chart(fig_top, use_container_width=True)

# Seção: Picos de Acesso por Hora
st.subheader("🕒 Picos de Acesso por Hora")
df_filtrado['hora'] = df_filtrado['access_time'].dt.hour
df_por_hora = df_filtrado.groupby('hora').size().reset_index(name='qtd_acessos')
fig_hora = px.line(
    df_por_hora, 
    x='hora', 
    y='qtd_acessos', 
    title="Acessos por Hora do Dia", 
    markers=True
)
fig_hora.update_layout(xaxis=dict(dtick=1), yaxis_title="Quantidade de Acessos", xaxis_title="Hora do Dia")
st.plotly_chart(fig_hora, use_container_width=True)

# Seção: Exportar dados
st.subheader("📥 Exportar Dados")
st.download_button(
    label="📄 Baixar dados filtrados (.csv)",
    data=df_filtrado.to_csv(index=False).encode('utf-8'),
    file_name='acessos_filtrados.csv',
    mime='text/csv'
)

# Seção: Tabela de visualização
st.subheader("📋 Tabela de Dados Filtrados")
st.dataframe(df_filtrado[['aluno', 'course_name', 'access_time']].sort_values(by='access_time', ascending=False).head(100))
