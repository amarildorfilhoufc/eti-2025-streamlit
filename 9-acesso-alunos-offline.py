import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(
    page_title="📊 Dashboard Moodle (Offline)",
    layout="wide"
)

# ---------- Carregamento dos dados com cache ----------
@st.cache_data
def carregar_dados():
    df = pd.read_excel("9-dados_acesso.xlsx")
    df['access_time'] = pd.to_datetime(df['access_time'], errors='coerce')
    df['aluno'] = df['firstname'] + ' ' + df['lastname']
    df['dias_desde_ultimo_acesso'] = (datetime.now() - df['access_time']).dt.days
    df['status'] = df['dias_desde_ultimo_acesso'].apply(
        lambda x: 'Ativo' if pd.notnull(x) and x <= 30 else 'Inativo'
    )
    df['data'] = df['access_time'].dt.date
    df['hora'] = df['access_time'].dt.hour

    mapa_estado = {
        '[NFCE': 'Ceará',
        '[NFMA': 'Maranhão',
        '[NFPI': 'Piauí',
        '[NFPE': 'Pernambuco'
    }
    def extrair_estado(curso):
        for sigla, estado in mapa_estado.items():
            if pd.notnull(curso) and sigla in curso:
                return estado
        return 'Outro'

    df['estado'] = df['course_name'].apply(extrair_estado)
    return df

df = carregar_dados()

# ---------- Interface principal com abas ----------
tabs = st.tabs(["Dashboard", "Comparativo por Estado"])

# --- Aba 1: Dashboard ---
with tabs[0]:
    st.title("📊 Dashboard de Acessos dos Alunos - Moodle (Offline)")
    st.write("""
    **ℹ️ Definição**
    - Um aluno é **Ativo** se acessou o Moodle nos últimos **30 dias**.
    - Um aluno é **Inativo** se **não acessa há mais de 30 dias** ou **nunca acessou**.
    """)

    # Filtros
    st.sidebar.header("🔍 Filtros")

    cursos_disponiveis = sorted(df['course_name'].dropna().unique())
    curso_selecionado = st.sidebar.multiselect("Curso(s)", cursos_disponiveis, default=[])

    if st.sidebar.button("🗑️ Limpar Seleção de Cursos"):
        curso_selecionado = []

    status_opcoes = ['Ativo', 'Inativo']
    status_selecionado = st.sidebar.multiselect("Status do Usuário", status_opcoes, default=status_opcoes)

    data_min = df['access_time'].dt.date.min()
    data_max = df['access_time'].dt.date.max()
    data_inicio, data_fim = st.sidebar.date_input(
        "Período de Acesso", [data_min, data_max], min_value=data_min, max_value=data_max
    )

    df_filtrado = df.copy()
    if curso_selecionado:
        df_filtrado = df_filtrado[df_filtrado['course_name'].isin(curso_selecionado)]
    df_filtrado = df_filtrado[
        (df_filtrado['status'].isin(status_selecionado)) &
        (df_filtrado['data'] >= data_inicio) &
        (df_filtrado['data'] <= data_fim)
    ]

    if not curso_selecionado:
        st.info("✅ Selecione ao menos um curso para ver os resultados.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("👤 Usuários únicos", df_filtrado['user_id'].nunique())
        col2.metric("📚 Cursos filtrados", len(curso_selecionado))
        col3.metric("✅ Acessos totais", len(df_filtrado))

        # Evolução dos acessos
        st.subheader(f"📅 Evolução dos Acessos ({data_inicio} a {data_fim})")
        df_por_data = df_filtrado.groupby(['data', 'course_name']).size().reset_index(name='qtd_acessos')
        if not df_por_data.empty:
            fig_data = px.line(
                df_por_data, x='data', y='qtd_acessos', color='course_name',
                markers=True, title="Acessos por Data"
            )
            st.plotly_chart(fig_data, use_container_width=True)
        else:
            st.warning("Nenhum dado para este período/curso/status.")

        # Top 10 alunos por dias com acesso
        st.subheader("👤 Top 10 Alunos por Dias com Acessos")
        df_top = df_filtrado.groupby('aluno')['data'].nunique().reset_index(name='dias_com_acesso')
        df_top = df_top.sort_values('dias_com_acesso', ascending=False).head(10)
        if not df_top.empty:
            fig_top = px.bar(
                df_top, x='aluno', y='dias_com_acesso', text='dias_com_acesso',
                title="Top 10 Alunos por Dias com Acessos",
                labels={'aluno': 'Aluno', 'dias_com_acesso': 'Dias com Acesso'}
            )
            fig_top.update_traces(textposition='outside')
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.warning("Nenhum aluno com acessos no filtro atual.")

        # Picos por hora
        st.subheader("🕒 Picos de Acesso por Hora do Dia")
        df_por_hora = df_filtrado.groupby('hora').size().reset_index(name='qtd_acessos')
        if not df_por_hora.empty:
            fig_hora = px.line(
                df_por_hora, x='hora', y='qtd_acessos', markers=True,
                title="Distribuição de Acessos por Hora"
            )
            fig_hora.update_layout(
                xaxis=dict(dtick=1),
                yaxis_title="Quantidade de Acessos",
                xaxis_title="Hora do Dia"
            )
            st.plotly_chart(fig_hora, use_container_width=True)
        else:
            st.warning("Sem dados de hora para este filtro.")

        # Acessos por turma
        st.subheader("🏫 Acessos por Turma (Curso)")
        turmas = df_filtrado['course_name'].unique()
        for turma in sorted(turmas):
            st.markdown(f"### 📚 {turma}")
            df_turma = df_filtrado[df_filtrado['course_name'] == turma]
            tabela_turma = df_turma.groupby('aluno').agg(
                total_acessos=('access_time', 'count'),
                dias_com_acesso=('data', 'nunique'),
                ultimo_acesso=('access_time', 'max'),
                status=('status', 'first')
            ).reset_index().sort_values(by='total_acessos', ascending=False)
            st.dataframe(tabela_turma, use_container_width=True)

        # Exportar dados filtrados CSV
        st.subheader("📥 Exportar Dados")
        st.download_button(
            label="📄 Baixar dados filtrados (.csv)",
            data=df_filtrado.to_csv(index=False).encode('utf-8'),
            file_name='acessos_filtrados.csv',
            mime='text/csv'
        )

        # Tabela detalhada
        st.subheader("📋 Tabela de Acessos Detalhada")
        st.dataframe(
            df_filtrado[['aluno', 'course_name', 'access_time', 'status', 'estado']]
            .sort_values(by='access_time', ascending=False).head(100)
        )

# --- Aba 2: Comparativo por Estado ---
with tabs[1]:
    st.title("🌎 Comparativo de Acessos por Estado")

    estados_disponiveis = sorted(df['estado'].unique())
    estados_selecionados = st.multiselect("Selecione um ou mais estados", estados_disponiveis, default=estados_disponiveis)

    if not estados_selecionados:
        st.warning("Por favor, selecione pelo menos um estado.")
        st.stop()

    df_estado = df[df['estado'].isin(estados_selecionados)]

    # Métricas
    col1, col2 = st.columns(2)
    col1.metric("Estados Selecionados", len(estados_selecionados))
    col2.metric("Usuários Únicos", df_estado['user_id'].nunique())

    # Acessos por estado
    acessos_estado = df_estado.groupby('estado').agg(
        total_acessos=('user_id', 'count'),
        usuarios_unicos=('user_id', 'nunique')
    ).reset_index().sort_values('total_acessos', ascending=False)

    # Gráfico barras com cores diferentes por estado
    fig_bar = px.bar(
        acessos_estado, x='estado', y='total_acessos', text='usuarios_unicos',
        title='Total de Acessos e Usuários Únicos por Estado',
        color='estado',  # cores diferentes
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_bar.update_traces(textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

    # Gráfico pizza com percentual e quantidade
    acessos_estado['label'] = acessos_estado.apply(
        lambda row: f"{row['estado']}<br>{row['total_acessos']} acessos<br>{(row['total_acessos']/acessos_estado['total_acessos'].sum()*100):.1f}%", axis=1
    )
    fig_pie = px.pie(
        acessos_estado,
        names='label',
        values='total_acessos',
        title='Distribuição Percentual dos Acessos por Estado',
        color='estado',
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_pie, use_container_width=True)

