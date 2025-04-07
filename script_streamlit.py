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
    df.columns = ['nome', 'cidade', 'id_coorte', 'acesso', 'estado']

    # Normalização
    df['estado'] = df['estado'].astype(str).str.upper().str.strip()
    df['cidade'] = df['cidade'].astype(str).str.strip()
    df['acesso'] = df['acesso'].astype(str).str.strip().str.lower()

    estados_validos = sorted(df['estado'].dropna().unique())

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Sidebar - Filtros
st.sidebar.title("Filtros")
with st.sidebar:
    estado_selecionado = st.multiselect("Estado", options=estados_validos, placeholder="Selecione estados...")
    cidade_selecionada = st.multiselect("Cidade", options=sorted(df['cidade'].dropna().unique()), placeholder="Selecione cidades...")
    status_acesso = st.multiselect("Status de Acesso", options=sorted(df['acesso'].dropna().unique()), placeholder="Selecione status...")

    if st.button("🔄 Limpar Filtros"):
        estado_selecionado = []
        cidade_selecionada = []
        status_acesso = []

# Aplicar filtros
filtro_estado = df['estado'].isin(estado_selecionado) if estado_selecionado else pd.Series([True] * len(df))
filtro_cidade = df['cidade'].isin(cidade_selecionada) if cidade_selecionada else pd.Series([True] * len(df))
filtro_acesso = df['acesso'].isin(status_acesso) if status_acesso else pd.Series([True] * len(df))

# Dados filtrados
df_filtrado = df[filtro_estado & filtro_cidade & filtro_acesso]

# Título
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📌 Visão Geral", 
        "🏙️ Por Cidade", 
        "📈 Detalhado", 
        "📚 Por Turma e Estado", 
        "📉 Menores Acessos"
    ])

    with tab1:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.countplot(data=df_filtrado, y='estado', order=df_filtrado['estado'].value_counts().index, ax=ax)
        ax.set_title('Distribuição por Estado')
        ax.set_xlabel('Quantidade')
        ax.set_ylabel('Estado')
        for p in ax.patches:
            width = p.get_width()
            ax.text(width + 1, p.get_y() + p.get_height()/2, f'{int(width)}', ha='left', va='center')
        st.pyplot(fig)

    with tab2:
        top_cidades = df_filtrado['cidade'].value_counts().nlargest(10)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=top_cidades.values, y=top_cidades.index, palette="Blues_d", ax=ax)
        ax.set_title('Top 10 Cidades')
        ax.set_xlabel('Quantidade')
        ax.set_ylabel('Cidade')
        for i, v in enumerate(top_cidades.values):
            ax.text(v + 0.5, i, str(v), color='black', va='center')
        st.pyplot(fig)

    with tab3:
        cross_tab = pd.crosstab(df_filtrado['estado'], df_filtrado['acesso'])
        fig, ax = plt.subplots(figsize=(12, 6))
        cross_tab.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
        ax.set_title('Status de Acesso por Estado')
        ax.set_ylabel('Quantidade')
        ax.legend(title='Status', bbox_to_anchor=(1.05, 1))
        for c in ax.containers:
            ax.bar_label(c, label_type='center', fmt='%d', color='white', fontweight='bold')
        st.pyplot(fig)

    with tab4:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📌 Percentual de Acesso por Estado")
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

        with col2:
            st.markdown("#### 🎓 Percentual de Acesso por Turma (ID Coorte)")
            porcentagem_turma = (
                df_filtrado.groupby(['id_coorte', 'acesso']).size()
                .groupby(level=0).apply(lambda x: 100 * x / float(x.sum()))
                .unstack().fillna(0)
                .round(1)
            )
            if porcentagem_turma.empty:
                st.info("Nenhuma turma encontrada com os filtros aplicados.")
            else:
                for turma, linha in porcentagem_turma.iterrows():
                    st.markdown(f"**Turma {turma}:**")
                    for status, valor in linha.items():
                        st.markdown(f"- {status}: {valor:.1f}%")
                    st.markdown("---")

    with tab5:
        st.markdown("### 🏙️ Cidades com Maior % de 'Nunca Acessou'")

        cidade_estado = df_filtrado.groupby(['cidade', 'estado', 'acesso']).size().unstack(fill_value=0)

        if 'nunca acessou' in cidade_estado.columns:
            cidade_estado['percentual_nunca_acessou'] = (
                cidade_estado['nunca acessou'] / cidade_estado.sum(axis=1)
            ) * 100

            cidades_ordenadas = cidade_estado['percentual_nunca_acessou'].sort_values(ascending=False).reset_index()
            cidades_ordenadas = cidades_ordenadas[['cidade', 'estado', 'percentual_nunca_acessou']].rename(columns={
                'cidade': 'Cidade',
                'estado': 'Estado',
                'percentual_nunca_acessou': '% Nunca Acessou'
            })

            st.dataframe(cidades_ordenadas.head(20), use_container_width=True)

        else:
            st.info("Nenhuma informação disponível sobre 'nunca acessou'.")

    st.divider()
    st.subheader("📋 Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)
