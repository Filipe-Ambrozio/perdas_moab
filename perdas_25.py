import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import os
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="Coleta de Validade", layout="wide")
st.title("🗃️ Coletar Produto para Controle de Validade")

# === Função para carregar Excel da Web (GitHub RAW) ===
def carregar_excel_da_web(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content)), url
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {e}")
        return None, None

# === Fonte do arquivo ===
st.sidebar.header("📂 Fonte do Arquivo Excel")
modo = st.sidebar.radio("Escolha o modo de carregamento:", ["Upload Manual", "GitHub"])

df = None
arquivo_origem = None

if modo == "Upload Manual":
    uploaded_file = st.sidebar.file_uploader("Faça upload do arquivo Excel (.xlsx)", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            arquivo_origem = uploaded_file.name
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

elif modo == "GitHub":
    github_url = "https://raw.githubusercontent.com/Filipe-Ambrozio/perdas_moab/main/Consulta_de_Produto_ATUAL.xlsx"
    df, arquivo_origem = carregar_excel_da_web(github_url)

# === Interface de coleta ===
if df is not None:
    df.columns = df.columns.str.strip()

    st.markdown("### 🏷️ Informações do Produto")

    mercadologico_lista = sorted(df["Mercadológico"].dropna().unique()) if "Mercadológico" in df.columns else []
    mercadologico = st.selectbox("Escolha o Mercadológico:", mercadologico_lista)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("📷 Escaneie o Código de Barras:")
        ativar_leitor = st.checkbox("Ativar câmera")

        codigo_barras = st.text_input("Código de Barras escaneado ou digitado:")

        if ativar_leitor:
            html_code = """
            <div id="reader" width="250px"></div>
            <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
            <script>
              function onScanSuccess(decodedText, decodedResult) {
                  const input = window.parent.document.querySelector('input[aria-label="Código de Barras escaneado ou digitado:"]');
                  if (input) {
                      input.value = decodedText;
                      const event = new Event('input', { bubbles: true });
                      input.dispatchEvent(event);
                  }
              }

              const html5QrCode = new Html5Qrcode("reader");
              html5QrCode.start(
                  { facingMode: "environment" },
                  { fps: 10, qrbox: 200 },
                  onScanSuccess
              );
            </script>
            """
            components.html(html_code, height=350)

    with col2:
        descricao = ""
        if codigo_barras:
            filtro = df[df["Código Barras"].astype(str) == codigo_barras]
            if not filtro.empty:
                descricao = filtro["Descrição"].iloc[0]
            else:
                st.warning("Código não encontrado no arquivo.")

        st.text_input("Descrição do Produto:", value=descricao, disabled=True)

    data_validade = st.date_input("📅 Data de Validade (dd/mm/aaaa):", format="DD/MM/YYYY")
    lote = st.text_input("Lote do Produto:")

    # === Salvando os dados coletados ===
    if st.button("💾 Salvar Coleta"):
        if not codigo_barras or not descricao or not lote:
            st.warning("Preencha todos os campos antes de salvar.")
        else:
            registro = {
                "Data Coleta": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Mercadológico": mercadologico,
                "Código Barras": codigo_barras,
                "Descrição": descricao,
                "Data Validade": data_validade.strftime("%d/%m/%Y"),
                "Lote": lote,
            }

            # Caminho para salvar (mesmo diretório do Excel)
            if modo == "GitHub":
                save_path = "coleta_validade.csv"  # Local atual do app
            else:
                save_path = os.path.join(os.path.dirname(arquivo_origem), "coleta_validade.csv")

            # Salvar (anexar ou criar)
            if os.path.exists(save_path):
                df_existente = pd.read_csv(save_path)
                df_novo = pd.concat([df_existente, pd.DataFrame([registro])], ignore_index=True)
            else:
                df_novo = pd.DataFrame([registro])

            df_novo.to_csv(save_path, index=False)
            st.success("✅ Produto salvo com sucesso.")
else:
    st.info("Carregue um arquivo Excel para começar.")