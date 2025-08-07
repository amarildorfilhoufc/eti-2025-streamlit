import pandas as pd
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Dashboard dos Cursos [NF]")

# --- Carregar dados ---
try:
    dados_path = "dados_nf.xlsx"
    cursos = pd.read_excel(dados_path, sheet_name="Cursos_NF")
    matriculas = pd.read_excel(dados_path, sheet_name="Matriculas")
    usuarios = pd.read_excel(dados_path, sheet_name="Usuarios")
    perfil = pd.read_excel(dados_path, sheet_name="Perfil")
    conclusoes = pd.read_excel(dados_path, sheet_name="Conclusoes_Modulos")
    funcoes = pd.read_excel(dados_path, sheet_name="Funcoes")
except FileNotFoundError:
    st.error("❌ Arquivo 'dados_nf.xlsx' não encontrado no diretório atual.")
    st.stop()


#_#_#_#    

st.header("🔢 Indicadores Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("Cursos [NF]", len(cursos))
col2.metric("Inscritos", matriculas['userid'].nunique())
col3.metric("Turmas", cursos['fullname'].nunique())

# Usuários ativos/inativos
usuarios_nf = usuarios[usuarios['userid'].isin(matriculas['userid'])]
nunca_acessaram = usuarios_nf[usuarios_nf['lastaccess'] == 0]
ativos = usuarios_nf[usuarios_nf['lastaccess'] > 0]

col4, col5, col6 = st.columns(3)
col4.metric("Nunca acessaram", len(nunca_acessaram))
col5.metric("Usuários ativos", len(ativos))
col6.metric("Usuários inativos", len(nunca_acessaram))

# Contar editingteachers (formadores) na tabela funcoes
editing_teachers = funcoes[funcoes['papel'].str.lower() == 'editingteacher']
qtd_editingteacher = editing_teachers['userid'].nunique()

# Exibir na métrica de formadores
st.metric("Formadores", qtd_editingteacher)

# --- Conclusões por Módulo ---
st.header("📘 Conclusões por Módulo")

concluintes = conclusoes[conclusoes['completionstate'] == 1]
resumo_modulos = concluintes.groupby(['courseid', 'modulename'])['userid'].nunique().reset_index()
resumo_modulos.columns = ['courseid', 'modulo', 'concluintes']

curso_select = st.selectbox("📌 Selecione um Curso", cursos['fullname'].unique())
id_curso = cursos[cursos['fullname'] == curso_select]['courseid'].values[0]

modulos_curso = resumo_modulos[resumo_modulos['courseid'] == id_curso]
st.bar_chart(modulos_curso.set_index('modulo')['concluintes'])

st.divider()

# --- Turmas com menos concluintes ---
st.header("🚨 Turmas com Menor Número de Concluintes por Módulo")
menor_conclusao = resumo_modulos.sort_values(by='concluintes').head(10)
menor_conclusao = menor_conclusao.merge(cursos, on='courseid', how='left')
st.dataframe(menor_conclusao[['fullname', 'modulo', 'concluintes']].rename(
    columns={"fullname": "Curso", "modulo": "Módulo", "concluintes": "Concluintes"}
))

st.divider()

# --- Estudantes por Estado (Ativos x Nunca Acessaram) ---

st.header("📍 Estudantes por Estado (Ativos x Nunca Acessaram)")

# Relacionar matriculas com cursos para pegar nome da turma
matriculas_cursos = matriculas.merge(cursos[['courseid', 'fullname']], on='courseid', how='left')

# Relacionar com usuários para saber lastaccess
matriculas_cursos = matriculas_cursos.merge(usuarios[['userid', 'lastaccess']], on='userid', how='left')

# Extrair estado da turma (NFXX)
def extrair_estado(turma):
    if pd.isna(turma):
        return "Desconhecido"
    turma = turma.strip()
    if turma.startswith('[NF') and len(turma) >= 5:
        return turma[3:5]  # Pega a sigla do estado
    return "Desconhecido"

matriculas_cursos['estado'] = matriculas_cursos['fullname'].apply(extrair_estado)

# Criar status de acesso
matriculas_cursos['status'] = matriculas_cursos['lastaccess'].apply(lambda x: 'Nunca Acessaram' if x == 0 else 'Ativo')

# Agrupar por estado e status
estado_status = matriculas_cursos.groupby(['estado', 'status']).size().unstack(fill_value=0)

# Ordenar por total
estado_status['Total'] = estado_status.sum(axis=1)
estado_status = estado_status.sort_values(by='Total', ascending=False)

# Plotar gráfico barras empilhadas
fig, ax = plt.subplots(figsize=(12, 6))
cores = ['#4CAF50', '#F44336']  # Verde para Ativo, vermelho para Nunca Acessaram
estado_status[['Ativo', 'Nunca Acessaram']].plot(kind='bar', stacked=True, color=cores, ax=ax)

# Adicionar rótulos nas barras
for container in ax.containers:
    ax.bar_label(container, label_type='center', fontsize=9)

ax.set_title("Estudantes por Estado (baseado na Turma)")
ax.set_xlabel("Estado")
ax.set_ylabel("Quantidade de Estudantes")
ax.legend(title="Status de Acesso")
plt.xticks(rotation=45)

st.pyplot(fig)

#############################

import matplotlib.pyplot as plt

st.header("🏫 Quantidade de Turmas por Estado")

# Extrair estado da turma dos cursos
cursos['estado'] = cursos['fullname'].apply(lambda x: x[3:5] if isinstance(x, str) and x.startswith('[NF') else 'Desconhecido')

# Contar turmas por estado
turmas_por_estado = cursos.groupby('estado').size().sort_values(ascending=False)

# Plotar gráfico de barras
fig, ax = plt.subplots(figsize=(10, 6))
turmas_por_estado.plot(kind='bar', color='#007acc', ax=ax)

# Adicionar rótulos nas barras
for i, v in enumerate(turmas_por_estado):
    ax.text(i, v + 0.2, str(v), ha='center', fontsize=10)

ax.set_title("Quantidade de Turmas por Estado")
ax.set_xlabel("Estado")
ax.set_ylabel("Número de Turmas")
plt.xticks(rotation=45)

st.pyplot(fig)


##################

st.header("🚨 Turmas com Menor Número de Concluintes por Módulo")

st.markdown("""
Nesta análise, identificamos as **turmas (cursos) com o menor número de concluintes** em cada módulo específico.  
- Consideramos apenas os registros de **conclusão de módulos com estado `completionstate = 1`**, ou seja, módulos efetivamente concluídos.  
- Calculamos o número de concluintes únicos por combinação de turma (curso) e módulo.  
- Ordenamos as turmas e módulos pelo menor número de concluintes para destacar as turmas com desempenho mais baixo em conclusão.  
- Extraímos o **estado** de cada turma a partir do prefixo do nome da turma, que segue o padrão `[NFXX...]`, onde `XX` é a sigla do estado.  
- A tabela exibe as 10 turmas e módulos com o menor número de concluintes.  
- Em seguida, apresentamos um gráfico que compara o total de concluintes dessas turmas com menor desempenho, agrupados por estado, para identificar quais estados concentram as turmas com menor sucesso nos módulos.
""")

# Filtrar concluintes (completionstate == 1)
concluintes = conclusoes[conclusoes['completionstate'] == 1]

# Contar concluintes por curso e módulo
resumo_modulos = concluintes.groupby(['courseid', 'modulename'])['userid'].nunique().reset_index()
resumo_modulos.columns = ['courseid', 'modulo', 'concluintes']

# Juntar com cursos para ter nome da turma e extrair estado
resumo_modulos = resumo_modulos.merge(cursos[['courseid', 'fullname']], on='courseid', how='left')

# Extrair estado do nome da turma
def extrair_estado(turma):
    if pd.isna(turma):
        return "Desconhecido"
    turma = turma.strip()
    if turma.startswith('[NF') and len(turma) >= 5:
        return turma[3:5]
    return "Desconhecido"

resumo_modulos['estado'] = resumo_modulos['fullname'].apply(extrair_estado)

# Ordenar por menor número de concluintes
menor_conclusao = resumo_modulos.sort_values(by='concluintes').head(10)

# Mostrar tabela com as turmas e módulos com menos concluintes
st.dataframe(menor_conclusao[['fullname', 'modulo', 'concluintes', 'estado']].rename(
    columns={
        'fullname': 'Turma',
        'modulo': 'Módulo',
        'concluintes': 'Número de Concluintes',
        'estado': 'Estado'
    }
))

# --- Gráfico comparativo por estado das turmas com menos concluintes ---

import matplotlib.pyplot as plt

st.subheader("Comparação dos Estados nas Turmas com Menor Número de Concluintes")


st.markdown("""
Nesta análise, identificamos as **turmas (cursos) com o menor número de concluintes** em cada módulo específico.  
- Consideramos apenas os registros de **conclusão de módulos com estado `completionstate = 1`**, ou seja, módulos efetivamente concluídos.  
- Calculamos o número de concluintes únicos por combinação de turma (curso) e módulo.  
- Ordenamos as turmas e módulos pelo menor número de concluintes para destacar as turmas com desempenho mais baixo em conclusão.  
- Extraímos o **estado** de cada turma a partir do prefixo do nome da turma, que segue o padrão `[NFXX...]`, onde `XX` é a sigla do estado.  
- A tabela exibe as 10 turmas e módulos com o menor número de concluintes.  
- Em seguida, apresentamos um gráfico que compara o total de concluintes dessas turmas com menor desempenho, agrupados por estado, para identificar quais estados concentram as turmas com menor sucesso nos módulos.
""")

# Agrupar por estado somando concluintes dessas turmas selecionadas
agrup_estado = menor_conclusao.groupby('estado')['concluintes'].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10,6))
agrup_estado.plot(kind='bar', color='#d62728', ax=ax)

# Adicionar rótulos nas barras
for i, v in enumerate(agrup_estado):
    ax.text(i, v + 0.2, str(v), ha='center', fontsize=10)

ax.set_title("Total de Concluintes por Estado nas Turmas com Menos Concluintes")
ax.set_xlabel("Estado")
ax.set_ylabel("Número de Concluintes")
plt.xticks(rotation=45)

st.pyplot(fig)

#_#_#_#
