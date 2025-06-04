import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

st.set_page_config(page_title="Controle de Validades", layout="wide")

st.title("📅 Controle de Validades de Produtos")

# === Função para carregar Excel da Web ===
def carregar_excel_da_web(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {e}")
        return None

# === Upload ou GitHub ===
st.markdown("### 📥 Carregar Arquivo de Validades")
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload manual do arquivo .xlsx", type=["xlsx"])
with col2:
    github_url = st.text_input("Ou insira o link direto do GitHub (.xlsx):")

df = None
if uploaded_file:
    df = pd.read_excel(uploaded_file)
elif github_url:
    df = carregar_excel_da_web(github_url)

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
            lojas = sorted(df["Loja"].dropna().unique())
            loja_sel = st.multiselect("Filtrar por Loja:", lojas)
        with colf2:
            dias = st.slider("Mostrar produtos com validade nos próximos X dias:", 0, 180, 30)

        hoje = pd.Timestamp.today()
        limite = hoje + pd.Timedelta(days=dias)

        df_filtrado = df.copy()
        if loja_sel:
            df_filtrado = df_filtrado[df_filtrado["Loja"].isin(loja_sel)]

        df_filtrado = df_filtrado[df_filtrado["Data Validade"] <= limite]
        df_filtrado = df_filtrado.sort_values("Data Validade")

        st.markdown("---")
        st.subheader("📝 Lista por Data de Validade")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        # === PDF: função para gerar ===
        def gerar_pdf_validade(dataframe):
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            largura, altura = A4

            c.setFont("Helvetica-Bold", 14)
            c.drawString(2 * cm, altura - 2 * cm, "Relatório de Controle de Validade")
            c.setFont("Helvetica", 10)

            y = altura - 3 * cm
            linha = 1

            for i, row in dataframe.iterrows():
                produto = str(row.get("Descrição", ""))
                codigo = str(row.get("Produto", ""))
                validade = row["Data Validade"].strftime("%d/%m/%Y")
                loja = str(row.get("Loja", ""))
                quantidade = str(row.get("Quantidade", ""))

                texto = f"{linha}. Produto: {produto} | Código: {codigo} | Validade: {validade} | Loja: {loja} | Qtde: {quantidade}"
                c.drawString(2 * cm, y, texto)

                y -= 1 * cm
                linha += 1
                if y < 2 * cm:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = altura - 2 * cm

            c.save()
            buffer.seek(0)
            return buffer

        if not df_filtrado.empty:
            st.markdown("### 📄 Gerar PDF para Impressão")
            pdf = gerar_pdf_validade(df_filtrado)
            st.download_button("📥 Baixar PDF A4", data=pdf, file_name="controle_validade.pdf", mime="application/pdf")
        else:
            st.warning("Nenhum produto com validade encontrada no período selecionado.")
else:
    st.info("Envie um arquivo Excel ou insira o link direto do GitHub.")