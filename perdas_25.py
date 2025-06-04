import streamlit as st
import pandas as pd
from io import BytesIO
import requests

st.set_page_config(page_title="Controle de Validades", layout="wide")

st.title("📅 Controle de Validades de Produtos")

# Função para carregar Excel da Web
def carregar_excel_da_web(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {e}")
        return None

# Upload ou GitHub
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

if df is not None:
    df.columns = df.columns.str.strip()
    
    # Ajuste para garantir que a coluna de validade está em datetime
    col_val = [col for col in df.columns if "validade" in col.lower()]
    if not col_val:
        st.error("Nenhuma coluna de data de validade encontrada no arquivo.")
    else:
        col_validade = col_val[0]
        df[col_validade] = pd.to_datetime(df[col_validade], errors='coerce')
        df = df.dropna(subset=[col_validade])
        
        # Filtros opcionais
        st.markdown("---")
        st.subheader("🔍 Filtros opcionais")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            loja = st.multiselect("Filtrar por Loja:", sorted(df['Loja'].dropna().unique()) if 'Loja' in df.columns else [])
        with col_f2:
            dias = st.slider("Mostrar produtos com validade nos próximos X dias:", 0, 180, 30)

        hoje = pd.Timestamp.today()
        limite = hoje + pd.Timedelta(days=dias)
        
        df_filtrado = df.copy()
        if loja and 'Loja' in df.columns:
            df_filtrado = df_filtrado[df_filtrado['Loja'].isin(loja)]
        
        df_filtrado = df_filtrado[df_filtrado[col_validade] <= limite]
        df_filtrado = df_filtrado.sort_values(by=col_validade)

        # Exibição
        st.markdown("---")
        st.subheader("📝 Lista por Data de Validade")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        # Exportar para PDF (modo texto/table no Streamlit)
        st.markdown("### 📄 Visualização para Impressão (A4)")
        for i, row in df_filtrado.iterrows():
            with st.container():
                st.markdown(f"""
                **Produto:** {row.get('Descrição', row.get('Produto', ''))}  
                **Código:** {row.get('Produto', '')}  
                **Validade:** `{row[col_validade].date()}`  
                **Loja:** {row.get('Loja', '')}  
                **Quantidade:** {row.get('Quantidade', '')}  
                ---
                """)

        # Opção de download CSV para impressão
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV para impressão", data=csv, file_name="controle_validade.csv", mime="text/csv")

else:
    st.info("Por favor, envie um arquivo Excel (.xlsx) ou forneça o link direto do GitHub.")