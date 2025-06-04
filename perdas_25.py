import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import requests

st.set_page_config(page_title="Consulta de Perdas", layout="wide")

aba = st.sidebar.radio("Selecionar análise:", [
    "Consulta de Perdas por Produto",
    "Consulta de Perdas por Grupo Mercadológico"
])

# Função para carregar arquivo Excel de URL

def carregar_excel_da_web(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {e}")
        return None

# =====================
# ABA 1 - Produto
# =====================
if aba == "Consulta de Perdas por Produto":
    st.title("📊 Consulta de Perdas por Produto")

    st.markdown("### 📁 Carregar Arquivo de Dados")
    col_a, col_b = st.columns(2)
    with col_a:
        uploaded_file = st.file_uploader("📥 Upload manual do arquivo .xlsx", type=["xlsx"], key="upload_prod")
    with col_b:
        github_url = st.text_input("🌐 Ou insira o link direto do arquivo no GitHub (.xlsx):", key="github_prod")

    df = None
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
    elif github_url:
        df = carregar_excel_da_web(github_url)

    if df is not None:
        df.columns = df.columns.str.strip()

        st.markdown("---")
        st.subheader("🔍 Filtros")
        col1, col2, col3 = st.columns(3)

        with col1:
            lojas = df['Loja'].dropna().unique()
            loja_selecionada = st.multiselect("Filtrar por Loja:", sorted(lojas), key="loja_prod")

        with col2:
            motivos = df['Motivo'].dropna().unique()
            motivo_selecionado = st.multiselect("Filtrar por Motivo:", sorted(motivos), key="motivo_prod")

        with col3:
            termo_produto = st.text_input("Buscar por Código ou Descrição do Produto:", key="busca_prod")

        df_filtrado = df.copy()

        if loja_selecionada:
            df_filtrado = df_filtrado[df_filtrado['Loja'].isin(loja_selecionada)]
        if motivo_selecionado:
            df_filtrado = df_filtrado[df_filtrado['Motivo'].isin(motivo_selecionado)]
        if termo_produto:
            df_filtrado = df_filtrado[
                df_filtrado['Produto'].astype(str).str.contains(termo_produto, case=False, na=False) |
                df_filtrado['Descrição'].astype(str).str.contains(termo_produto, case=False, na=False)
            ]

        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader("💸 Total da Perda por Item")

            resultado = (
                df_filtrado.groupby(['Produto', 'Descrição'], as_index=False)['Total c/ Imposto']
                .sum()
                .rename(columns={'Total c/ Imposto': 'Total da Perda'})
                .sort_values(by='Total da Perda', ascending=False)
            )

            st.dataframe(resultado, use_container_width=True, hide_index=True)
            total_geral = resultado['Total da Perda'].sum()
            st.success(f"💰 Total Geral da Perda: R$ {total_geral:,.2f}")

            st.markdown("### 📊 Gráfico de Perdas por Item")
            fig = px.bar(
                resultado.head(20),
                x="Total da Perda",
                y="Descrição",
                orientation='h',
                title="Top Itens com Maior Perda",
                labels={"Total da Perda": "Total (R$)", "Descrição": "Produto"},
                height=600
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("🎯 Participação por Motivo")

            df_motivo = (
                df_filtrado.groupby('Motivo', as_index=False)['Total c/ Imposto']
                .sum()
                .rename(columns={'Total c/ Imposto': 'TT c/ Imp.'})
            )
            total_motivos = df_motivo['TT c/ Imp.'].sum()
            df_motivo['Partici%'] = (df_motivo['TT c/ Imp.'] / total_motivos) * 100
            df_motivo = df_motivo.sort_values(by='Partici%', ascending=False)

            st.dataframe(df_motivo, use_container_width=True, hide_index=True)

            fig_motivo = px.pie(
                df_motivo,
                names='Motivo',
                values='Partici%',
                title="🥧 Distribuição das Perdas por Motivo",
                hole=0.4
            )
            st.plotly_chart(fig_motivo, use_container_width=True)

        else:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
    else:
        st.info("Por favor, envie um arquivo Excel (.xlsx) ou forneça o link direto do GitHub.")

# =====================
# ABA 2 - Mercadológico
# =====================
elif aba == "Consulta de Perdas por Grupo Mercadológico":
    st.title("📊 Consulta de Perdas por Grupo Mercadológico")

    st.markdown("### 📁 Carregar Arquivo de Dados Mercadológico")
    col_a2, col_b2 = st.columns(2)
    with col_a2:
        uploaded_file2 = st.file_uploader("📥 Upload manual do arquivo .xlsx", type=["xlsx"], key="upload_merc")
    with col_b2:
        github_url2 = st.text_input("🌐 Ou insira o link direto do arquivo no GitHub (.xlsx):", key="github_merc")

    df2 = None
    if uploaded_file2:
        df2 = pd.read_excel(uploaded_file2)
    elif github_url2:
        df2 = carregar_excel_da_web(github_url2)

    if df2 is not None:
        df2.columns = df2.columns.str.strip()

        st.markdown("---")
        st.subheader("🔍 Filtros Mercadológicos")

        col1, col2, col3 = st.columns(3)

        with col1:
            mercs = df2['Mercadológico'].dropna().unique()
            grupo_sel = st.multiselect("Filtrar por Mercadológico:", sorted(mercs), key="grupo_merc")

        with col2:
            lojas2 = df2['Loja'].dropna().unique()
            loja_sel = st.multiselect("Filtrar por Loja:", sorted(lojas2), key="loja_merc")

        with col3:
            motivos2 = df2['Motivo'].dropna().unique()
            motivo_sel = st.multiselect("Filtrar por Motivo:", sorted(motivos2), key="motivo_merc")

        df_filt = df2.copy()

        if grupo_sel:
            df_filt = df_filt[df_filt['Mercadológico'].isin(grupo_sel)]
        if loja_sel:
            df_filt = df_filt[df_filt['Loja'].isin(loja_sel)]
        if motivo_sel:
            df_filt = df_filt[df_filt['Motivo'].isin(motivo_sel)]

        if not df_filt.empty:
            st.markdown("---")
            st.subheader("📈 Total da Perda por Grupo Mercadológico")

            resultado2 = (
                df_filt.groupby(['Mercadológico'], as_index=False)['Total c/ Imposto']
                .sum()
                .rename(columns={'Total c/ Imposto': 'Total da Perda'})
                .sort_values(by='Total da Perda', ascending=False)
            )

            st.dataframe(resultado2, use_container_width=True, hide_index=True)

            total_geral2 = resultado2['Total da Perda'].sum()
            st.success(f"💰 Total Geral da Perda: R$ {total_geral2:,.2f}")

            fig2 = px.bar(
                resultado2.head(20),
                x="Total da Perda",
                y="Mercadológico",
                orientation='h',
                title="Top Grupos com Maior Perda",
                labels={"Total da Perda": "Total (R$)", "Mercadológico": "Grupo"},
                height=600
            )
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            st.subheader("🎯 Participação por Motivo")

            df_motivo2 = (
                df_filt.groupby('Motivo', as_index=False)['Total c/ Imposto']
                .sum()
                .rename(columns={'Total c/ Imposto': 'TT c/ Imp.'})
            )
            total_motivos2 = df_motivo2['TT c/ Imp.'].sum()
            df_motivo2['Partici%'] = (df_motivo2['TT c/ Imp.'] / total_motivos2) * 100
            df_motivo2 = df_motivo2.sort_values(by='Partici%', ascending=False)

            st.dataframe(df_motivo2, use_container_width=True, hide_index=True)

            fig_motivo2 = px.pie(
                df_motivo2,
                names='Motivo',
                values='Partici%',
                title="🥧 Distribuição das Perdas por Motivo para o Grupo Mercadológico",
                hole=0.4
            )
            st.plotly_chart(fig_motivo2, use_container_width=True)

        else:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
    else:
        st.info("Por favor, envie um arquivo Excel (.xlsx) ou forneça o link direto do GitHub.")

#streamlit run perdas_25.py