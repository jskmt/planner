import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

from calculador_cronograma import calcular_cronograma
from extrator_composicoes_empresa import extrair_composicoes

# Caminho local fixo do banco SINAPI
CAMINHO_SINAPI = "banco_sinapi_profissionais_detalhado.csv"

# Carregar banco SINAPI (sem necessidade de upload)
@st.cache_data
def carregar_banco_sinapi():
    return pd.read_csv(CAMINHO_SINAPI, sep=";", encoding="utf-8")

# Gerar planilha Excel para download
def gerar_planilha_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cronograma")
    return output.getvalue()

# App principal
def main():
    st.title("🏗️ Gerador de Cronograma de Obras - SINAPI")

    st.markdown("Envie a **planilha orçamentária** da empresa para gerar o cronograma com base no banco SINAPI.")

    planilha_file = st.file_uploader("📥 Planilha orçamentária (.xlsx)", type=["xlsx"])

    data_inicio = st.date_input("📅 Data de início da obra", datetime.today())
    prazo_dias = st.number_input("⏳ Prazo total da obra (dias corridos)", min_value=1, step=1)

    if planilha_file:
        try:
            df_orcamento = extrair_composicoes(planilha_file)
            df_sinapi = carregar_banco_sinapi()

            st.success(f"✅ {len(df_orcamento)} composições extraídas da planilha.")
            if st.button("📊 Gerar Cronograma"):
                df_cronograma = calcular_cronograma(
                    df_orcamento,
                    df_sinapi,
                    data_inicio.strftime("%d/%m/%Y"),
                    prazo_total_dias=prazo_dias
                )

                st.subheader("📋 Cronograma Gerado")
                st.dataframe(df_cronograma)

                excel_bytes = gerar_planilha_excel(df_cronograma)

                st.download_button(
                    label="📥 Baixar Cronograma (.xlsx)",
                    data=excel_bytes,
                    file_name="cronograma_obra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"❌ Erro ao processar os dados: {e}")

if __name__ == "__main__":
    main()
