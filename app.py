import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
import math

# 📌 Extrai as composições do orçamento
def extrair_composicoes(arquivo_excel):
    df = pd.read_excel(arquivo_excel, sheet_name=0)
    df = df.rename(columns=lambda x: str(x).strip().lower())
    col_codigo = next(col for col in df.columns if "composi" in col and "cód" in col)
    col_servico = next(col for col in df.columns if "descrição" in col)
    col_qtd = next(col for col in df.columns if "quantidade" in col)
    df = df[[col_codigo, col_servico, col_qtd]].dropna()
    df.columns = ["codigo", "servico", "quantidade"]
    df["codigo"] = df["codigo"].astype(str)
    return df

# 📌 Gera o cronograma baseado no banco SINAPI
def gerar_cronograma(df_composicoes, df_sinapi, data_inicio, prazo_total_dias):
    atividades = []
    data_atual = data_inicio

    for _, row in df_composicoes.iterrows():
        codigo = row["codigo"]
        servico = row["servico"]
        quantidade = row["quantidade"]

        sinapi_rows = df_sinapi[df_sinapi["codigo_composicao"] == codigo]
        if sinapi_rows.empty:
            continue

        for _, sinapi in sinapi_rows.iterrows():
            profissional = sinapi["profissional"]
            produtividade = sinapi["producao_diaria"]

            if produtividade <= 0:
                continue

            dias_execucao = quantidade / produtividade
            dias_execucao = max(1, math.ceil(dias_execucao))

            data_fim = data_atual + datetime.timedelta(days=dias_execucao - 1)

            qtde_profissionais = math.ceil(quantidade / (produtividade * dias_execucao))

            atividades.append({
                "Código": codigo,
                "Serviço": servico,
                "Data Início": data_atual.strftime('%d/%m/%Y'),
                "Dias Execução": dias_execucao,
                "Data Fim": data_fim.strftime('%d/%m/%Y'),
                "Profissional": profissional,
                "Qtde Profissionais": qtde_profissionais,
                "Produtividade (por dia)": produtividade,
                "Quantidade Total": quantidade
            })

        data_atual = data_fim + datetime.timedelta(days=1)

    return pd.DataFrame(atividades)

# 🟢 Interface Streamlit
st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📋 Planejador de Obra com base no SINAPI")

data_inicio = st.date_input("📅 Data de início da obra")
prazo_total = st.number_input("⏳ Prazo total da obra (em dias)", min_value=1)
arquivo = st.file_uploader("📂 Envie a planilha orçamentária (.xlsx)", type=["xlsx"])

if arquivo is not None:
    try:
        df_composicoes = extrair_composicoes(arquivo)
        df_sinapi = pd.read_csv("banco_sinapi_profissionais_detalhado.csv")

        cronograma = gerar_cronograma(df_composicoes, df_sinapi, data_inicio, prazo_total)

        if cronograma.empty:
            st.warning("⚠️ Nenhum item da planilha foi encontrado no banco SINAPI.")
        else:
            st.success("✅ Cronograma gerado com sucesso!")
            st.dataframe(cronograma)

            # Gerar planilha para download
            output = BytesIO()
            cronograma.to_excel(output, index=False, engine="openpyxl")
            st.download_button(
                label="📥 Baixar Cronograma (.xlsx)",
                data=output.getvalue(),
                file_name="cronograma_obra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
