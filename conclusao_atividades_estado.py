import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Conclusão", layout="wide")
st.title("📊 Dashboard de Conclusão de Atividades")

# ==============================
# Carregar dados
# ==============================
@st.cache_data
def load_data(file_name):
    df = pd.read_excel(file_name)
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data("estado_de_conclusao_tratado.xlsx")

# ==============================
# Filtros na barra lateral
# ==============================
st.sidebar.header("Filtros")
turmas = st.sidebar.multiselect(
    "Selecione as Turmas",
    options=df['turma'].unique(),
    default=df['turma'].unique()
)
atividades = st.sidebar.multiselect(
    "Selecione os Tipos de Atividade",
    options=df['tipo_atividade'].unique(),
    default=df['tipo_atividade'].unique()
)
estados = st.sidebar.multiselect(
    "Selecione os Estados",
    options=df['estado'].unique(),
    default=df['estado'].unique()
)

df_filtrado = df[
    df['turma'].isin(turmas) &
    df['tipo_atividade'].isin(atividades) &
    df['estado'].isin(estados)
]

# ==============================
# Criar abas
# ==============================
tab1, tab2, tab3 = st.tabs([
    "Conclusão Geral",
    "Conclusão por Turma",
    "Comparação por Estado"
])

# ==============================
# Aba 1: Conclusão Geral por Tipo de Atividade
# ==============================
with tab1:
    st.subheader("📌 Conclusão Geral por Tipo de Atividade")

    conclusao_geral = (
        df_filtrado.groupby("tipo_atividade")
        .agg(
            total_atividades=('estado_conclusao','count'),
            atividades_concluidas=('estado_conclusao','sum')
        )
        .reset_index()
    )
    conclusao_geral["% Conclusão"] = (
        conclusao_geral["atividades_concluidas"] / conclusao_geral["total_atividades"] * 100
    )

    col1, col2 = st.columns([1,2])
    with col1:
        st.dataframe(conclusao_geral)
    with col2:
        fig1 = px.bar(
            conclusao_geral,
            x="tipo_atividade",
            y="% Conclusão",
            text="% Conclusão",
            title="% de Conclusão por Tipo de Atividade"
        )
        fig1.update_traces(texttemplate='%{text:.1f}%', textposition="outside")
        fig1.update_layout(yaxis_title="% Conclusão", xaxis_title="Tipo de Atividade")
        st.plotly_chart(fig1, use_container_width=True)

# ==============================
# Aba 2: Conclusão por Turma e Tipo de Atividade
# ==============================
with tab2:
    st.subheader("📌 Conclusão por Turma e Tipo de Atividade")

    pivot_turma = (
        df_filtrado.groupby(["turma","tipo_atividade"])
        .agg(
            total_atividades=('estado_conclusao','count'),
            atividades_concluidas=('estado_conclusao','sum')
        )
        .reset_index()
    )
    pivot_turma["% Conclusão"] = (
        pivot_turma["atividades_concluidas"] / pivot_turma["total_atividades"] * 100
    )

    col3, col4 = st.columns([1,2])
    with col3:
        st.dataframe(pivot_turma)
    with col4:
        fig2 = px.bar(
            pivot_turma,
            x="turma",
            y="% Conclusão",
            color="tipo_atividade",
            barmode="group",
            text="% Conclusão",
            title="% de Conclusão por Turma e Tipo de Atividade"
        )
        fig2.update_traces(texttemplate='%{text:.1f}%', textposition="outside")
        fig2.update_layout(yaxis_title="% Conclusão", xaxis_title="Turma")
        st.plotly_chart(fig2, use_container_width=True)

# ==============================
# Aba 3: Comparação por Estado
# ==============================
with tab3:
    st.subheader("📌 Comparação de Conclusão por Estado")

    pivot_estado = (
        df_filtrado.groupby(["estado","tipo_atividade"])
        .agg(
            total_atividades=('estado_conclusao','count'),
            atividades_concluidas=('estado_conclusao','sum')
        )
        .reset_index()
    )
    pivot_estado["% Conclusão"] = (
        pivot_estado["atividades_concluidas"] / pivot_estado["total_atividades"] * 100
    )

    col5, col6 = st.columns([1,2])
    with col5:
        st.dataframe(pivot_estado)
    with col6:
        fig3 = px.bar(
            pivot_estado,
            x="estado",
            y="% Conclusão",
            color="tipo_atividade",
            barmode="group",
            text="% Conclusão",
            title="% de Conclusão por Estado e Tipo de Atividade"
        )
        fig3.update_traces(texttemplate='%{text:.1f}%', textposition="outside")
        fig3.update_layout(yaxis_title="% Conclusão", xaxis_title="Estado")
        st.plotly_chart(fig3, use_container_width=True)
