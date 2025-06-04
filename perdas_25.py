import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import requests

st.set_page_config(page_title="Controle de Validades", layout="wide")
st.title("📅 Controle de Validades de Produtos")

# === Função para carregar Excel da Web (GitHub RAW) ===
def carregar_excel_da_web(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {e}")
        return None

# === Opção de carregamento ===
st.sidebar.header("📂 Fonte do Arquivo Excel")
modo = st.sidebar.radio("Escolha o modo de carregamento:", ["GitHub", "Upload Manual"])

df = None

if modo == "GitHub":
    # Corrigido: link RAW do GitHub
    github_url = "https://raw.githubusercontent.com/Filipe-Ambrozio/perdas_moab/main/Consulta_de_Produto_ATUAL.xlsx"
    df = carregar_excel_da_web(github_url)

elif modo == "Upload Manual":
    uploaded_file = st.sidebar.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# === Processamento ===
if df is not None:
    df.columns = df.columns.str.strip()

    if "Data Validade" not in df.columns:
        st.error("A coluna 'Data Validade' não foi encontrada no arquivo.")
    else:
        df["Data Validade"] = pd.to_datetime(df["Data Validade"], errors="coerce")
        df = df.dropna(subset=["Data Validade"])

        st.markdown("---")
        st.subheader("🔍 Filtros opcionais")

        colf1, colf2 = st.columns(2)
        with colf1:
            lojas = sorted(df["Loja"].dropna().unique()) if "Loja" in df.columns else []
            loja_sel = st.multiselect("Filtrar por Loja:", lojas)

            mercadologico = sorted(df["Mercadológico"].dropna().unique()) if "Mercadológico" in df.columns else []
            merc_sel = st.multiselect("Filtrar por Mercadológico:", mercadologico)

            cod_input = st.text_input("Filtrar por Código (parcial ou completo):")

        with colf2:
            barras_input = st.text_input("Filtrar por Código Barras (parcial ou completo):")

            desc_input = st.text_input("Filtrar por Descrição (parcial):")

            dias = st.slider("Mostrar produtos com validade nos próximos X dias:", 0, 180, 30)

        hoje = pd.Timestamp.today()
        limite = hoje + pd.Timedelta(days=dias)

        df_filtrado = df.copy()

        # Aplicar filtros
        if loja_sel:
            df_filtrado = df_filtrado[df_filtrado["Loja"].isin(loja_sel)]
        if merc_sel:
            df_filtrado = df_filtrado[df_filtrado["Mercadológico"].isin(merc_sel)]
        if cod_input:
            df_filtrado = df_filtrado[df_filtrado["Código"].astype(str).str.contains(cod_input, case=False, na=False)]
        if barras_input:
            df_filtrado = df_filtrado[df_filtrado["Código Barras"].astype(str).str.contains(barras_input, case=False, na=False)]
        if desc_input:
            df_filtrado = df_filtrado[df_filtrado["Descrição"].astype(str).str.contains(desc_input, case=False, na=False)]

        df_filtrado = df_filtrado[df_filtrado["Data Validade"] <= limite]
        df_filtrado = df_filtrado.sort_values("Data Validade")

        st.markdown("---")
        st.subheader("📝 Lista por Data de Validade")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        if not df_filtrado.empty:
            st.markdown("### ⬇️ Exportar Dados")

            # Exportar CSV
            csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Baixar como CSV",
                data=csv_data,
                file_name="controle_validade.csv",
                mime="text/csv"
            )

            # Exportar Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name='Validades')
            excel_buffer.seek(0)
            st.download_button(
                label="📊 Baixar como Excel",
                data=excel_buffer,
                file_name="controle_validade.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhum produto com validade encontrada no período/filtros selecionados.")
else:
    st.info("Carregue um arquivo Excel para começar.")