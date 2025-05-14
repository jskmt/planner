
import streamlit as st
import pandas as pd
from extrator_composicoes_empresa import extrair_composicoes_planilha_padroes_empresa
from datetime import datetime

st.set_page_config(page_title="Planejador de Obra", layout="wide")

st.title("🏗️ Planejador de Obra")
st.markdown("Este aplicativo gera um cronograma de execução de obra a partir de uma planilha orçamentária padrão.")

# Upload da planilha
arquivo = st.file_uploader("📎 Faça upload da planilha orçamentária (.xlsx):", type=["xlsx"])

# Inputs do usuário
col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("📅 Data de início da obra:", value=datetime.today())
with col2:
    prazo_dias = st.number_input("⏱️ Prazo total da obra (em dias):", min_value=1, value=90)

# Processamento após o upload
if arquivo is not None:
    try:
        df_itens = extrair_composicoes_planilha_padroes_empresa(arquivo)
        st.success("✅ Planilha processada com sucesso!")
        st.dataframe(df_itens.head(20), use_container_width=True)

        st.info("👉 Agora conecte este orçamento ao banco de dados SINAPI para gerar o cronograma.")
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
