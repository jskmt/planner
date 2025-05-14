import streamlit as st
import pandas as pd

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📊 Planejador de Obra com base no SINAPI")

# Carrega banco SINAPI
@st.cache_data
def carregar_banco_sinapi():
    try:
        df = pd.read_csv("banco_sinapi_profissionais_detalhado.csv", sep=";", engine="python")
        df.columns = df.columns.str.strip().str.lower()
        df = df.rename(columns={
            "codigo da composicao": "codigo_composicao",
            "descrição item": "descricao_item",
            "coeficiente": "coeficiente"
        })
        df["codigo_composicao"] = df["codigo_composicao"].astype(str).str.replace(r"[^\d]", "", regex=True).str.zfill(7)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return pd.DataFrame()

# Função para gerar cronograma
def gerar_cronograma(planilha, banco_sinapi):
    try:
        df_orc = pd.read_excel(planilha)
        df_orc.rename(columns=lambda x: x.strip().upper(), inplace=True)

        col_codigo = [col for col in df_orc.columns if "CÓDIGO" in col][0]
        col_servico = [col for col in df_orc.columns if "INSUMO" in col or "SERVIÇO" in col][0]
        col_quant = [col for col in df_orc.columns if "QUANT" in col][0]

        df_orc = df_orc[[col_codigo, col_servico, col_quant]]
        df_orc.columns = ["codigo_composicao", "descricao", "quantidade"]

        df_orc["codigo_composicao"] = df_orc["codigo_composicao"].astype(str).str.replace(r"[^\d]", "", regex=True).str.zfill(7)
        banco_sinapi["codigo_composicao"] = banco_sinapi["codigo_composicao"].astype(str).str.replace(r"[^\d]", "", regex=True).str.zfill(7)

        cronograma = []

        for _, row in df_orc.iterrows():
            codigo = row["codigo_composicao"]
            quantidade = row["quantidade"]

            comp = banco_sinapi[banco_sinapi["codigo_composicao"] == codigo]
            if comp.empty:
                continue

            for _, prof in comp.iterrows():
                horas_totais = quantidade * prof["coeficiente"]
                cronograma.append({
                    "Composição": codigo,
                    "Serviço": row["descricao"],
                    "Profissional": prof["descricao_item"],
                    "Horas Totais": round(horas_totais, 2)
                })

        if not cronograma:
            st.warning("Nenhum item do orçamento corresponde ao banco SINAPI.")
            return

        df_crono = pd.DataFrame(cronograma)
        st.success("✅ Cronograma gerado com sucesso!")
        st.dataframe(df_crono)

        csv = df_crono.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Cronograma", data=csv, file_name="cronograma.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")

# Upload da planilha
planilha = st.file_uploader("📁 Envie sua planilha orçamentária (.xlsx)", type=["xlsx"])

# Carrega banco SINAPI
banco = carregar_banco_sinapi()

# Botão de geração
if planilha and not banco.empty:
    gerar_cronograma(planilha, banco)
