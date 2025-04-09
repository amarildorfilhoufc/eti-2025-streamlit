import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Estilos
plt.style.use('seaborn-v0_8')
sns.set_theme(style="whitegrid")

# Carregar dados
try:
    arquivo_excel = 'Acessos_tratado.xlsx'
    df = pd.read_excel(arquivo_excel, sheet_name='Sheet1')
    df.columns = ['nome', 'cidade', 'id_coorte', 'acesso', 'estado', 'ultimo_acesso']

    # Normalização
    df['estado'] = df['estado'].astype(str).str.upper().str.strip()
    df['cidade'] = df['cidade'].astype(str).str.strip()
    df['acesso'] = df['acesso'].astype(str).str.strip().str.lower()

    estados_validos = sorted(df['estado'].dropna().unique())

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Sidebar - Filtros
st.sidebar.title("🎛️ Filtros")
estado_selecionado = st.sidebar.multiselect("Estado", options=estados_validos, placeholder="Selecione estados...")
cidade_selecionada = st.sidebar.multiselect("Cidade", options=sorted(df['cidade'].dropna().unique()), placeholder="Selecione cidades...")
status_acesso = st.sidebar.multiselect("Status de Acesso", options=sorted(df['acesso'].dropna().unique()), placeholder="Selecione status...")

if st.sidebar.button("🔄 Limpar Filtros"):
    estado_selecionado = []
    cidade_selecionada = []
    status_acesso = []

# Campo de busca por nome
st.sidebar.markdown("---")
nome_busca = st.sidebar.text_input("🔍 Buscar Aluno por Nome", placeholder="Digite o nome...")

# Menu lateral de navegação
menu = st.sidebar.radio("📁 Navegação", [
    "📌 Visão Geral", 
    "🏙️ Por Cidade", 
    "📈 Detalhado", 
    "📚 Por Turma e Estado", 
    "📉 Menores Acessos",
    "👥 Alocação por Turma", 
    "🔍 Buscar por Nome",
    "📆 Acompanhamento por Turma"  
])

# Aplicar filtros
filtro_estado = df['estado'].isin(estado_selecionado) if estado_selecionado else pd.Series([True] * len(df))
filtro_cidade = df['cidade'].isin(cidade_selecionada) if cidade_selecionada else pd.Series([True] * len(df))
filtro_acesso = df['acesso'].isin(status_acesso) if status_acesso else pd.Series([True] * len(df))

# Dados filtrados
df_filtrado = df[filtro_estado & filtro_cidade & filtro_acesso]

# Título principal
st.title("📊 Dashboard de Acessos")

if df_filtrado.empty:
    st.info("ℹ️ Selecione filtros para visualizar os dados")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(df_filtrado))
    with col2:
        st.metric("Estados", df_filtrado['estado'].nunique())
    with col3:
        st.metric("Cidades", df_filtrado['cidade'].nunique())

    st.divider()

    if menu == "📌 Visão Geral":
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.countplot(data=df_filtrado, y='estado', order=df_filtrado['estado'].value_counts().index, ax=ax)
        ax.set_title('Distribuição por Estado')
        ax.set_xlabel('Quantidade')
        ax.set_ylabel('Estado')
        for p in ax.patches:
            width = p.get_width()
            ax.text(width + 1, p.get_y() + p.get_height()/2, f'{int(width)}', ha='left', va='center')
        st.pyplot(fig)

    elif menu == "🏙️ Por Cidade":
        top_cidades = df_filtrado['cidade'].value_counts().nlargest(10)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(
            x=top_cidades.values,
            y=top_cidades.index,
            hue=top_cidades.index,
            palette="Blues_d",
            ax=ax,
            legend=False
        )
        ax.set_title('Top 10 Cidades')
        ax.set_xlabel('Quantidade')
        ax.set_ylabel('Cidade')
        for i, v in enumerate(top_cidades.values):
            ax.text(v + 0.5, i, str(v), color='black', va='center')
        st.pyplot(fig)

    elif menu == "📈 Detalhado":
        # Tabela cruzada com totais
        cross_tab = pd.crosstab(df_filtrado['estado'], df_filtrado['acesso'])
        total_por_estado = cross_tab.sum(axis=1)
        percentual = (cross_tab.T / total_por_estado).T * 100

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Definindo as cores para "Já Acessou" e "Nunca Acessou"
        cores = ['#1f77b4', '#ff7f0e']  # Altere os códigos de cores conforme desejado
        bars = cross_tab.plot(kind='bar', stacked=True, ax=ax, color=cores)

        ax.set_title('Status de Acesso por Estado')
        ax.set_ylabel('Quantidade')

        # Adiciona os totais ao lado dos nomes de status na legenda
        acesso_labels = cross_tab.columns.tolist()  # ['Já Acessou', 'Nunca Acessou']
        acesso_totais = [cross_tab[col].sum() for col in acesso_labels]
        legenda_labels = [f"{label} ({total})" for label, total in zip(acesso_labels, acesso_totais)]

        ax.legend(title='Status', labels=legenda_labels, bbox_to_anchor=(1.05, 1))

        estados = cross_tab.index.tolist()

        for i, container in enumerate(ax.containers):
            tipo = acesso_labels[i] if i < len(acesso_labels) else None
            for j, bar in enumerate(container):
                height = bar.get_height()
                if height > 0 and tipo:
                    try:
                        grupo_estado = estados[j]  # índice do estado
                        qtd = int(height)
                        perc = percentual.loc[grupo_estado, tipo]

                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_y() + height / 2,
                            f"{qtd} ({perc:.1f}%)",
                            ha='center',
                            va='center',
                            color='white',
                            fontsize=9,
                            fontweight='bold'
                        )
                    except Exception as e:
                        print(f"Erro ao adicionar rótulo: {e}")

        st.pyplot(fig)


    elif menu == "📚 Por Turma e Estado":
        st.markdown("#### 📌 Percentual de Acesso por Estado")

        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                porcentagem_estado = (
                    df_filtrado.groupby(['estado', 'acesso']).size()
                    .groupby(level=0).apply(lambda x: 100 * x / float(x.sum()))
                    .unstack().fillna(0)
                )

                fig, ax = plt.subplots(figsize=(10, 5))
                porcentagem_estado.plot(kind='bar', stacked=True, ax=ax, colormap='Accent')
                ax.set_ylabel('%')
                ax.set_title('Distribuição Percentual por Estado')
                ax.legend(title='Status de Acesso', bbox_to_anchor=(1.05, 1), loc='upper left')

                for container in ax.containers:
                    ax.bar_label(container, fmt="%.1f%%", label_type="center")

                st.pyplot(fig)

        # Gráfico de acesso por turma em tela cheia
        if df_filtrado.empty:
            st.info("Nenhuma turma encontrada com os filtros aplicados.")
        else:
            st.markdown("#### 📊 Gráfico de Acesso por Turma")

            contagem_turma = df_filtrado.groupby(['id_coorte', 'acesso']).size().unstack(fill_value=0)
            porcentagem_turma = contagem_turma.div(contagem_turma.sum(axis=1), axis=0) * 100

            contagem_turma.index = contagem_turma.index.astype(str)
            porcentagem_turma.index = porcentagem_turma.index.astype(str)

            fig2, ax2 = plt.subplots(figsize=(18, 7))  # ⬅️ AUMENTADO O TAMANHO
            cores = ['#1f77b4', '#ff7f0e']
            contagem_turma.plot(kind='bar', stacked=True, ax=ax2, color=cores)
            ax2.set_ylabel('Quantidade')
            ax2.set_title('Status de Acesso por Turma')
            ax2.legend(title='Status', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.set_xticklabels(contagem_turma.index, rotation=45, ha='right')  # ⬅️ ROTACIONA RÓTULOS

            for i, container in enumerate(ax2.containers):
                status = contagem_turma.columns[i]
                for j, bar in enumerate(container):
                    altura = bar.get_height()
                    if altura > 0:
                        turma = contagem_turma.index[j]
                        perc = porcentagem_turma.loc[turma, status]
                        texto = f"{int(altura)} ({perc:.1f}%)"
                        if altura < 5:
                            # Se a barra for muito pequena, mostra o rótulo acima
                            ax2.text(
                                bar.get_x() + bar.get_width() / 2,
                                bar.get_y() + altura + 0.5,
                                texto,
                                ha='center', va='bottom',
                                color='black', fontsize=8
                            )
                        else:
                            # Senão, mostra dentro
                            ax2.text(
                                bar.get_x() + bar.get_width() / 2,
                                bar.get_y() + altura / 2,
                                texto,
                                ha='center', va='center',
                                color='white', fontsize=9, fontweight='bold'
                            )

            st.pyplot(fig2)

                # Tabela detalhada por Estado e Turma
        # Tabela detalhada por Estado e Turma com Percentuais
        st.markdown("#### 📝 Detalhamento por Estado e Turma")

        # Agrupar dados por estado, turma e acesso
        detalhamento = (
            df_filtrado.groupby(['estado', 'id_coorte', 'acesso'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .rename(columns={
                'já acessou': 'Já Acessou',
                'nunca acessou': 'Nunca Acessou'
            })
        )

        # Total por estado
        totais_estado = df_filtrado.groupby(['estado', 'acesso']).size().unstack(fill_value=0)
        totais_estado['% Já Acessou'] = (totais_estado['já acessou'] / totais_estado.sum(axis=1) * 100).round(1)

        # Calcular % por turma
        detalhamento['Total'] = detalhamento['Já Acessou'] + detalhamento['Nunca Acessou']
        detalhamento['% Já Acessou'] = (detalhamento['Já Acessou'] / detalhamento['Total'] * 100).round(1)
        detalhamento['% Nunca Acessou'] = (detalhamento['Nunca Acessou'] / detalhamento['Total'] * 100).round(1)

        # Exibir dados por estado
        estados = detalhamento['estado'].unique()
        for estado in sorted(estados):
            # Obter % total de acesso do estado
            percentual_estado = totais_estado.loc[estado]['% Já Acessou']
            st.markdown(f"### 📍 Estado: **{estado}** – Já Acessou: **{percentual_estado:.1f}%**")

            # Filtrar dados do estado
            df_estado = detalhamento[detalhamento['estado'] == estado][
                ['id_coorte', 'Já Acessou', '% Já Acessou', 'Nunca Acessou', '% Nunca Acessou']
            ]
            df_estado = df_estado.rename(columns={'id_coorte': 'Turma'})
            df_estado = df_estado.sort_values(by='Turma')

            st.dataframe(df_estado.reset_index(drop=True), use_container_width=True)


    elif menu == "📉 Menores Acessos":
        st.markdown("### 🏙️ Cidades com Maior % de 'Nunca Acessou'")
        estados_disponiveis = sorted(df_filtrado['estado'].dropna().unique())
        estados_selecionados = st.multiselect("Selecione o(s) Estado(s):", estados_disponiveis, default=estados_disponiveis)
        df_estado_filtrado = df_filtrado[df_filtrado['estado'].isin(estados_selecionados)]
        cidade_estado = df_estado_filtrado.groupby(['cidade', 'estado', 'acesso']).size().unstack(fill_value=0)
        colunas = [col.lower() for col in cidade_estado.columns]
        cidade_estado.columns = colunas
        ja_acessou = cidade_estado.get('já acessou', 0)
        nunca_acessou = cidade_estado.get('nunca acessou', 0)
        cidade_estado['Já Acessou'] = ja_acessou
        cidade_estado['Nunca Acessou'] = nunca_acessou
        cidade_estado['Total de Registros'] = ja_acessou + nunca_acessou
        cidade_estado['% Nunca Acessou'] = (nunca_acessou / cidade_estado['Total de Registros']) * 100
        cidades_ordenadas = cidade_estado[['% Nunca Acessou', 'Já Acessou', 'Total de Registros']].sort_values(
            by='% Nunca Acessou', ascending=False).reset_index()
        cidades_ordenadas = cidades_ordenadas.rename(columns={'cidade': 'Cidade', 'estado': 'Estado'})
        st.dataframe(cidades_ordenadas.head(100), use_container_width=True)

    elif menu == "👥 Alocação por Turma":
        st.markdown("### 👥 Turmas com Menos Alunos")
        estado_turma = st.selectbox("Selecione o Estado:", sorted(df_filtrado['estado'].unique()))
        cidades_do_estado = sorted(df_filtrado[df_filtrado['estado'] == estado_turma]['cidade'].unique())
        cidade_turma = st.selectbox("Selecione a Cidade:", cidades_do_estado)
        df_turma = df_filtrado[(df_filtrado['estado'] == estado_turma) & (df_filtrado['cidade'] == cidade_turma)]
        turma_contagem = df_turma['id_coorte'].value_counts().sort_values()
        st.write("Quantidade de alunos por turma:")
        st.dataframe(turma_contagem.reset_index().rename(columns={"index": "Turma", "id_coorte": "Qtd de Alunos"}))

    elif menu == "🔍 Buscar por Nome":
        nome_busca = st.sidebar.text_input("🔍 Buscar Aluno por Nome (sem acentos ou caracteres especias)", placeholder="Digite o nome...", key="busca_nome")

        if nome_busca:
            nome_busca_lower = nome_busca.strip().lower()
            resultados = df[df['nome'].str.lower().str.contains(nome_busca_lower)]
            st.subheader("🔍 Resultado da Busca por Nome")
            if resultados.empty:
                st.warning("Nenhum aluno encontrado com esse nome.")
            else:
                for idx, linha in resultados.iterrows():
                    st.markdown(f"""
                    - **Nome:** {linha['nome']}
                    - **Turma:** {linha['id_coorte']}
                    - **Cidade:** {linha['cidade']}
                    - **Estado:** {linha['estado']}
                    ---
                    """)
    
    elif menu == "📆 Acompanhamento por Turma":
        st.markdown("### 📊 Evolução dos Acessos por Turma")

        # Filtros
        estado_filtro = st.selectbox("Selecione o Estado:", sorted(df_filtrado['estado'].unique()))
        cidades_filtro = df_filtrado[df_filtrado['estado'] == estado_filtro]['cidade'].unique()
        cidade_filtro = st.selectbox("Selecione a Cidade:", sorted(cidades_filtro))

        turmas_disp = df_filtrado[
            (df_filtrado['estado'] == estado_filtro) & 
            (df_filtrado['cidade'] == cidade_filtro)
        ]['id_coorte'].unique()

        turma_filtro = st.selectbox("Selecione a Turma:", sorted(turmas_disp))

        # Dados filtrados
        df_turma = df_filtrado[
            (df_filtrado['estado'] == estado_filtro) & 
            (df_filtrado['cidade'] == cidade_filtro) & 
            (df_filtrado['id_coorte'] == turma_filtro) &
            (df_filtrado['acesso'].str.lower() == "já acessou")
        ].copy()

        if df_turma.empty:
            st.warning("Nenhum acesso encontrado para essa turma.")
        else:
            # Garantir que a data esteja no formato correto
            df_turma['ultimo_acesso'] = pd.to_datetime(df_turma['ultimo_acesso'], errors='coerce')

            # Contar acessos por data
            acessos_diarios = df_turma['ultimo_acesso'].dt.date.value_counts().sort_index()
            acessos_acumulados = acessos_diarios.cumsum()

            # Plotar gráfico
            fig, ax = plt.subplots(figsize=(10, 5))
            acessos_acumulados.plot(ax=ax, marker='o', linestyle='-')
            ax.set_title(f"Evolução Acumulada de Acessos - Turma {turma_filtro}")
            ax.set_xlabel("Data")
            ax.set_ylabel("Total Acumulado de Acessos")
            ax.grid(True)
            st.pyplot(fig)

            st.markdown("#### 📋 Evolução Diária")
            st.dataframe(
                pd.DataFrame({
                    "Data": acessos_acumulados.index,
                    "Acessos Acumulados": acessos_acumulados.values
                })
            )


######################################################

    st.divider()
    st.subheader("📋 Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)
