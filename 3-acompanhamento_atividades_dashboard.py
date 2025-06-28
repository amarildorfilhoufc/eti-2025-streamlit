import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- Leitura dos Dados ---
arquivo = "dados_moodle.xlsx"
dados = pd.read_excel(arquivo, sheet_name=None)

# Carregando os DataFrames
df_cursos = dados["cursos"]
df_usuarios = dados["usuarios"]
df_atividades = dados["atividades_assign"]
df_envios = dados["envios_assign"]
df_modulos = dados["modulos"]

# --- Mapeamento de Estados pelas siglas nos nomes dos cursos ---
ESTADO_POR_SIGLA = {
    'CE': 'CEARÁ',
    'MA': 'MARANHÃO',
    'PI': 'PIAUÍ',
    'PE': 'PERNAMBUCO'
}

# --- Mapeamento de Atividades do Documento ---
MAPEAMENTO_ATIVIDADES = {
    "Encontros Presenciais": {"horas": 20, "ch_por_item": 10, "minimo": 1},
    "Webinários": {"horas": 15, "ch_por_item": 3, "minimo": 4},
    "Atividades dos módulos": {"horas": 20, "ch_por_item": 4, "minimo": 3},
    "Encontros Síncronos": {"horas": 12, "ch_por_item": 2, "minimo": 5},
    "Fóruns": {"horas": 12, "ch_por_item": 2, "minimo": 5},
    "Atividade Final": {"horas": 21, "obrigatoria": True},
    "Estudos e Leituras": {"horas": 20, "nao_conta_frequencia": True}
}

# --- Filtros na barra lateral ---
st.sidebar.title("🎯 Filtros")
cursos_disponiveis = df_cursos["fullname"].sort_values().unique()
curso_selecionado = st.sidebar.selectbox("Selecione a turma", cursos_disponiveis)

# Detectar o estado
estado_detectado = None
for sigla, estado in ESTADO_POR_SIGLA.items():
    if sigla in curso_selecionado.upper():
        estado_detectado = estado
        break

if estado_detectado is None:
    st.error("Não foi possível detectar o estado a partir do nome do curso.")
    st.stop()

curso_id = df_cursos[df_cursos["fullname"] == curso_selecionado]["id"].values[0]

# Filtrar dados
atividades_curso = df_atividades[df_atividades["course"] == curso_id]
envios_curso = df_envios[df_envios["course"] == curso_id]

# Merge com usuários e atividades
envios_curso = envios_curso.merge(df_usuarios, left_on="userid", right_on="id")
envios_curso = envios_curso.merge(atividades_curso[["id", "name"]], left_on="assignment", right_on="id")
envios_curso = envios_curso.rename(columns={"name": "name_atividade"})

# Converter timestamp
envios_curso["data_envio"] = pd.to_datetime(envios_curso["timemodified"], unit='s')

# Filtro de usuário
usuarios_curso = (envios_curso["firstname"] + " " + envios_curso["lastname"]).dropna().unique().tolist()
usuarios_curso.sort()
usuario_selecionado = st.sidebar.selectbox("Filtrar por usuário", ["Todos"] + usuarios_curso)

st.title("📊 Dashboard de Certificação")
st.subheader(f"Turma: {curso_selecionado} - Estado: {estado_detectado}")

# --- Cálculo ---
def calcular_carga_horaria(envios, usuario=None):
    if usuario != "Todos":
        nome_split = usuario.split()
        envios = envios[
            (envios["firstname"] == nome_split[0]) & 
            (envios["lastname"] == " ".join(nome_split[1:]))
        ]
    
    resultados = {tipo: {
        "horas_completadas": 0,
        "horas_exigidas": dados["horas"],
        "itens_completos": 0,
        "itens_exigidos": dados["horas"] / dados.get("ch_por_item", 1),
        "minimo_requerido": dados.get("minimo", 0),
        "obrigatoria": dados.get("obrigatoria", False),
        "nao_conta_frequencia": dados.get("nao_conta_frequencia", False)
    } for tipo, dados in MAPEAMENTO_ATIVIDADES.items()}
    
    tipo_por_atividade = {
        "avaliação": "Atividades dos módulos",
        "atividade 1": "Atividades dos módulos",
        "plano de estudos": "Estudos e Leituras",
        "portfólio": "Atividade Final"
    }

    atividades_nao_reconhecidas = set()

    for _, row in envios.iterrows():
        nome_atividade = str(row.get("name_atividade", "")).lower()
        tipo = None
        for chave in tipo_por_atividade:
            if chave in nome_atividade:
                tipo = tipo_por_atividade[chave]
                break
        if tipo and tipo in resultados:
            resultados[tipo]["itens_completos"] += 1
        else:
            atividades_nao_reconhecidas.add(nome_atividade)

    for tipo, dados in resultados.items():
        if not dados["nao_conta_frequencia"]:
            proporcao = min(dados["itens_completos"] / dados["itens_exigidos"], 1)
            dados["horas_completadas"] = proporcao * dados["horas_exigidas"]

    horas_frequencia = sum(d["horas_completadas"] for t, d in resultados.items() if not d["nao_conta_frequencia"])
    atividade_final_ok = resultados["Atividade Final"]["itens_completos"] > 0

    return {
        "horas_totais": 120,
        "horas_frequencia": horas_frequencia,
        "frequencia_minima": 90,
        "atividade_final_ok": atividade_final_ok,
        "apto_certificado": horas_frequencia >= 90 and atividade_final_ok,
        "detalhes": resultados,
        "nao_reconhecidas": atividades_nao_reconhecidas
    }

# --- Visualização Individual ---
st.markdown("### 📜 Status para Certificação")

if usuario_selecionado == "Todos":
    st.warning("Selecione um usuário específico para ver o status de certificação")
else:
    status = calcular_carga_horaria(envios_curso, usuario_selecionado)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Horas Cumpridas", f"{status['horas_frequencia']:.1f}h", 
                f"{status['horas_frequencia']-status['frequencia_minima']:.1f}h do mínimo")
    col2.metric("Atividade Final", "✅ Completa" if status['atividade_final_ok'] else "❌ Incompleta")
    col3.metric("Elegível para Certificado", 
                "✅ Sim" if status['apto_certificado'] else "❌ Não",
                "Requisitos cumpridos" if status['apto_certificado'] else "Faltam requisitos")

    st.markdown("#### ⚠️ Atividades não reconhecidas")
    st.write(status["nao_reconhecidas"])

    st.markdown("#### Detalhamento por Tipo de Atividade")
    detalhes = []
    for tipo, dados in status['detalhes'].items():
        if not dados["nao_conta_frequencia"]:
            detalhes.append({
                "Tipo": tipo,
                "Itens Completos": dados["itens_completos"],
                "Itens Exigidos": f"{dados['itens_exigidos']:.0f}",
                "Mínimo Requerido": dados["minimo_requerido"],
                "Horas Completadas": f"{dados['horas_completadas']:.1f}h",
                "Horas Exigidas": f"{dados['horas_exigidas']}h",
                "% Completado": f"{(dados['itens_completos']/dados['itens_exigidos'])*100:.1f}%" if dados['itens_exigidos'] > 0 else "0%",
                "Status": "✅" if dados['itens_completos'] >= dados['minimo_requerido'] else "⚠️" if dados['itens_completos'] > 0 else "❌"
            })
    st.dataframe(pd.DataFrame(detalhes))

    # --- NOVO: Detalhamento por Atividade Entregue ---
    st.markdown("#### 📅 Detalhamento de Atividades Enviadas")

    nome_split = usuario_selecionado.split()
    envios_usuario = envios_curso[
        (envios_curso["firstname"] == nome_split[0]) & 
        (envios_curso["lastname"] == " ".join(nome_split[1:]))
    ]

    linhas_detalhes = []
    for _, row in envios_usuario.iterrows():
        nome_atividade = str(row["name_atividade"]).lower()
        tipo_detectado = None
        for chave, tipo in {
            "avaliação": "Atividades dos módulos",
            "atividade 1": "Atividades dos módulos",
            "plano de estudos": "Estudos e Leituras",
            "portfólio": "Atividade Final"
        }.items():
            if chave in nome_atividade:
                tipo_detectado = tipo
                break
        if tipo_detectado is None:
            tipo_detectado = "Não Reconhecida"

        mapeamento = MAPEAMENTO_ATIVIDADES.get(tipo_detectado, {})
        horas = mapeamento.get("ch_por_item", None)
        contabiliza = not mapeamento.get("nao_conta_frequencia", False)

        linhas_detalhes.append({
            "Nome da Atividade": row["name_atividade"],
            "Tipo Detectado": tipo_detectado,
            "Data de Envio": row["data_envio"].date(),
            "Carga Horária": f"{horas}h" if horas else "N/A",
            "Contabiliza Frequência": "Sim" if contabiliza else "Não"
        })

    df_ativ_detalhes = pd.DataFrame(linhas_detalhes)
    st.dataframe(df_ativ_detalhes)

# --- Progresso da Turma ---
st.markdown("### 📊 Progresso da Turma para Certificação")

progresso_turma = []
for usuario in usuarios_curso:
    status = calcular_carga_horaria(envios_curso, usuario)
    progresso_turma.append({
        "Aluno": usuario,
        "Horas Completadas": f"{status['horas_frequencia']:.1f}",
        "Atividade Final": "✅" if status["atividade_final_ok"] else "❌",
        "% Completado": f"{(status['horas_frequencia']/120)*100:.1f}%",
        "Apto Certificado": "✅" if status["apto_certificado"] else "❌"
    })

df_progresso = pd.DataFrame(progresso_turma)
st.dataframe(df_progresso.sort_values(by="Horas Completadas", ascending=False))

# --- Módulos por Estado ---
st.markdown(f"### 📌 Distribuição de Carga Horária por Módulo - {estado_detectado}")

if estado_detectado == "CEARÁ":
    modulos = {
        "Módulo I": 24, "Módulo II": 14, "Módulo III": 24,
        "Módulo IV": 14, "Módulo V": 11, "Módulo VI": 10,
        "Atividade Final": 23
    }
elif estado_detectado in ["PERNAMBUCO", "PIAUÍ"]:
    modulos = {
        "Módulo I": 14, "Módulo II": 24, "Módulo III": 14,
        "Módulo IV": 24, "Módulo V": 11, "Módulo VI": 10,
        "Atividade Final": 23
    }
else:  # MARANHÃO
    modulos = {
        "Módulo I": 14, "Módulo II": 24, "Módulo III": 14,
        "Módulo IV": 14, "Módulo V": 21, "Módulo VI": 10,
        "Atividade Final": 23
    }

df_modulos_estado = pd.DataFrame.from_dict(modulos, orient="index", columns=["Horas"])
st.bar_chart(df_modulos_estado)

st.markdown("#### Mínimos Requeridos por Módulo")
minimos = {
    "Módulo": list(modulos.keys()),
    "Carga Horária": list(modulos.values()),
    "Mínimo (75%)": [round(h * 0.75, 1) for h in modulos.values()]
}
st.dataframe(pd.DataFrame(minimos))

# --- Visão Geral da Turma ---
st.markdown("### 📈 Visão Geral da Turma por Tipo de Atividade")

resumo_atividade = {tipo: {
    "Total Alunos": 0,
    "Completaram Mínimo": 0,
    "Média Itens Completos": 0,
    "Média % Completado": 0
} for tipo in MAPEAMENTO_ATIVIDADES.keys() if not MAPEAMENTO_ATIVIDADES[tipo].get("nao_conta_frequencia", False)}

for usuario in usuarios_curso:
    status = calcular_carga_horaria(envios_curso, usuario)
    for tipo, dados in status["detalhes"].items():
        if tipo not in resumo_atividade or dados["nao_conta_frequencia"]:
            continue
        resumo_atividade[tipo]["Total Alunos"] += 1
        resumo_atividade[tipo]["Média Itens Completos"] += dados["itens_completos"]
        resumo_atividade[tipo]["Média % Completado"] += min((dados["itens_completos"] / dados["itens_exigidos"]) * 100, 100)
        if dados["itens_completos"] >= dados["minimo_requerido"]:
            resumo_atividade[tipo]["Completaram Mínimo"] += 1

# Preparar DataFrame
linhas = []
for tipo, dados in resumo_atividade.items():
    total = dados["Total Alunos"] if dados["Total Alunos"] > 0 else 1
    linhas.append({
        "Tipo de Atividade": tipo,
        "Alunos com Mínimo": f"{dados['Completaram Mínimo']}/{dados['Total Alunos']}",
        "Média Itens Completos": f"{dados['Média Itens Completos'] / total:.1f}",
        "Média % Completado": f"{dados['Média % Completado'] / total:.1f}%"
    })

df_resumo_turma = pd.DataFrame(linhas)
st.dataframe(df_resumo_turma)

# Gráfico de barras
st.markdown("#### 📊 Gráfico de Conclusão por Tipo de Atividade")
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(df_resumo_turma["Tipo de Atividade"], 
       df_resumo_turma["Média % Completado"].str.replace('%','').astype(float), 
       color='teal')
ax.set_ylabel("% Conclusão Média")
ax.set_ylim(0, 100)
ax.set_title("Média de Conclusão por Tipo de Atividade na Turma")
plt.xticks(rotation=45, ha='right')
st.pyplot(fig)




