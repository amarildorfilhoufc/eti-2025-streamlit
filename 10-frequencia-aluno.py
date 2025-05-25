import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Mapa de Presença por Curso", 
    layout="wide",
    page_icon="📚"
)

st.title("📚 Mapa de Presença por Curso")

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("10-presencas.xlsx")
        required_cols = ['user_id', 'firstname', 'lastname', 'course_name', 'access_time']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            st.error(f"Colunas faltantes: {', '.join(missing)}")
            return None
        df['access_time'] = pd.to_datetime(df['access_time'])
        df['data_acesso'] = df['access_time'].dt.normalize()
        df['nome_aluno'] = df['firstname'] + ' ' + df['lastname']
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

df = load_data()
if df is None:
    st.stop()

st.sidebar.header("Filtros")
curso_selecionado = st.sidebar.selectbox(
    "Selecione o Curso:",
    options=sorted(df['course_name'].unique()),
    index=0
)

min_date = df['data_acesso'].min().date()
max_date = df['data_acesso'].max().date()

data_inicio = st.sidebar.date_input("Data inicial:", min_date, min_value=min_date, max_value=max_date)
data_fim = st.sidebar.date_input("Data final:", max_date, min_value=min_date, max_value=max_date)

# Filtra o dataframe pelo curso e período
df_filtrado = df[
    (df['course_name'] == curso_selecionado) &
    (df['data_acesso'] >= pd.to_datetime(data_inicio)) &
    (df['data_acesso'] <= pd.to_datetime(data_fim))
]

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para o curso e período selecionados.")
    st.stop()

# Lista de alunos para filtro
alunos_curso = sorted(df_filtrado['nome_aluno'].unique())
aluno_selecionado = st.sidebar.selectbox("Filtrar por aluno (opcional):", options=["-- Todos --"] + alunos_curso)

# Se aluno selecionado, filtra para esse aluno
if aluno_selecionado != "-- Todos --":
    df_aluno = df_filtrado[df_filtrado['nome_aluno'] == aluno_selecionado]
    st.header(f"📊 Presença Individual: {aluno_selecionado}")
    
    dias_aula = sorted(df_filtrado['data_acesso'].unique())
    
    # Monta tabela individual de presença
    presenca_individual = []
    for dia in dias_aula:
        presente = "✅" if (dia in df_aluno['data_acesso'].dt.normalize().values) else "❌"
        presenca_individual.append({'Data': dia.strftime('%d/%m/%Y'), 'Presença': presente})
    
    df_presenca_ind = pd.DataFrame(presenca_individual)
    
    # Exibe tabela com cores
    def color_presence(val):
        color = 'green' if val == "✅" else 'red' if val == "❌" else 'black'
        return f'color: {color}'
    
    st.dataframe(df_presenca_ind.style.applymap(color_presence, subset=['Presença']), height=300)
    
    total_pres = (df_presenca_ind['Presença'] == "✅").sum()
    total_falt = (df_presenca_ind['Presença'] == "❌").sum()
    freq = total_pres / len(dias_aula) * 100
    
    st.markdown(f"""
    - **Total de aulas:** {len(dias_aula)}
    - **Presenças:** {total_pres}
    - **Faltas:** {total_falt}
    - **Frequência:** {freq:.1f}%
    """)
    
    st.markdown("---")

st.header(f"📋 Mapa de Presença - {curso_selecionado}")

# Recalcula para o curso todo (ou seja, todos alunos do curso)
dias_aula = sorted(df_filtrado['data_acesso'].unique())

presenca_curso = pd.DataFrame(
    index=alunos_curso,
    columns=[dia.strftime('%d/%m/%Y') for dia in dias_aula] + ['Total ✅', 'Total ❌', 'Frequência']
)

for aluno in alunos_curso:
    acessos_aluno = df_filtrado[df_filtrado['nome_aluno'] == aluno]['data_acesso'].dt.normalize().unique()
    total_presente = 0
    total_falta = 0
    for dia in dias_aula:
        if dia in acessos_aluno:
            presenca_curso.loc[aluno, dia.strftime('%d/%m/%Y')] = "✅"
            total_presente += 1
        else:
            presenca_curso.loc[aluno, dia.strftime('%d/%m/%Y')] = "❌"
            total_falta += 1
    presenca_curso.loc[aluno, 'Total ✅'] = total_presente
    presenca_curso.loc[aluno, 'Total ❌'] = total_falta
    presenca_curso.loc[aluno, 'Frequência'] = f"{(total_presente / len(dias_aula))*100:.1f}%"

def color_presence(val):
    color = 'green' if val == "✅" else 'red' if val == "❌" else 'black'
    return f'color: {color}'

st.dataframe(
    presenca_curso.style.applymap(color_presence),
    height=600,
    use_container_width=True
)

# Estatísticas gerais
st.header("📊 Estatísticas do Curso")

total_alunos = len(alunos_curso)
total_aulas = len(dias_aula)
total_presencas = presenca_curso['Total ✅'].sum()
total_faltas = presenca_curso['Total ❌'].sum()
media_frequencia = (total_presencas / (total_alunos * total_aulas)) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Alunos", total_alunos)
col2.metric("Dias de Aula", total_aulas)
col3.metric("Total de Presenças", total_presencas)
col4.metric("Total de Faltas", total_faltas)

st.markdown(f"""
    Neste curso **{curso_selecionado}**, há um total de **{total_alunos} alunos** matriculados, 
    considerando o período de **{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}**, 
    com **{total_aulas} dias de aula** contabilizados.

    Durante esse período, foram registradas **{total_presencas} presenças**, 
    correspondendo ao total de vezes em que os alunos acessaram as aulas. 
    Em contrapartida, houve **{total_faltas} faltas**, ou seja, as vezes em que os alunos não estiveram presentes nas aulas.

    Isso representa uma frequência média de **{media_frequencia:.1f}%**, calculada como a razão entre o número de presenças e o total possível de presenças 
    (que é o produto do número de alunos pelo número de dias de aula).

    Esses dados ajudam a compreender o engajamento dos alunos e a identificar possíveis dificuldades de participação no curso.
""")

tab1, tab2 = st.tabs(["Frequência por Dia", "Distribuição de Presença"])

with tab1:
    freq_dia = pd.DataFrame({
        'Dia': dias_aula,
        'Presenças': [(presenca_curso[col.strftime('%d/%m/%Y')] == "✅").sum() for col in dias_aula],
        'Total Alunos': total_alunos
    })
    freq_dia['% Presentes'] = round((freq_dia['Presenças'] / freq_dia['Total Alunos']) * 100, 1)

    fig = px.line(
        freq_dia,
        x='Dia',
        y='% Presentes',
        title='Porcentagem de Alunos Presentes por Dia',
        markers=True,
        labels={'% Presentes': 'Presenças (%)', 'Dia': 'Data da Aula'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.pie(
        names=['Presenças', 'Faltas'],
        values=[total_presencas, total_faltas],
        title='Distribuição Geral de Presenças e Faltas',
        color=['Presenças', 'Faltas'],
        color_discrete_map={'Presenças':'green', 'Faltas':'red'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Exportação
st.header("📤 Exportar Dados")

presenca_export = presenca_curso.reset_index()
presenca_export = presenca_export.rename(columns={'index': 'Aluno'})

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Baixar Mapa Completo (CSV)",
        data=presenca_export.to_csv(index=False).encode('utf-8'),
        file_name=f"mapa_presenca_{curso_selecionado.replace(' ', '_')}.csv",
        mime="text/csv"
    )

with col2:
    resumo = pd.DataFrame({
        'Curso': [curso_selecionado],
        'Período': [f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"],
        'Total Alunos': [total_alunos],
        'Total Aulas': [total_aulas],
        'Total Presenças': [total_presencas],
        'Total Faltas': [total_faltas],
        'Frequência Média': [f"{media_frequencia:.1f}%"]
    })
    
    st.download_button(
        label="Baixar Resumo Estatístico (CSV)",
        data=resumo.to_csv(index=False).encode('utf-8'),
        file_name=f"resumo_presenca_{curso_selecionado.replace(' ', '_')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
          f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
