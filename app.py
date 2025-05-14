import streamlit as st
import pandas as pd
import datetime

# Função para processar o orçamento
def processar_orcamento(uploaded_file):
    for skip in range(0, 15):
        df = pd.read_excel(uploaded_file, skiprows=skip)
        if {"Código", "Descrição", "Quant."}.issubset(df.columns):
            df = df[["Código", "Descrição", "Quant."]].dropna()
            df.columns = ["codigo", "descricao", "quantidade"]
            df = df[~df["quantidade"].astype(str).str.contains("Quant", na=False)]
            df["codigo"] = df["codigo"].astype(str).str.zfill(4)
            df["quantidade"] = (
                df["quantidade"].astype(str)
                .str.replace(",", ".", regex=False)
                .str.extract(r"([0-9.]+)")[0]
                .astype(float)
            )
            return df
    raise ValueError("Colunas esperadas não encontradas.")

# Função para carregar banco SINAPI embutido
def carregar_banco_sinapi():
    try:
        df = pd.read_csv(
            "banco_sinapi_profissionais_detalhado.csv",
            sep=";",
            encoding="utf-8",
            on_bad_lines="skip",
            engine="python"
        )
        # Renomeia a coluna correta
        df.rename(columns={"Código da Composição": "codigo_composicao"}, inplace=True)
        df["codigo_composicao"] = df["codigo_composicao"].astype(str).str.zfill(4)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None
# Função para gerar cronograma
def gerar_cronograma(df_orcamento, sinapi_df, data_inicio, prazo_dias):
    cronograma = []

    for _, linha in df_orcamento.iterrows():
        cod = linha["codigo"]
        qtd = linha["quantidade"]

        comp = sinapi_df[sinapi_df["codigo_composicao"] == cod]

        if comp.empty:
            continue

        for _, prof in comp.iterrows():
            nome_prof = prof["descricao_item"]
            prod = prof["producao_hora"]
            if pd.isna(prod) or prod == 0:
                continue

            horas_totais = qtd / prod
            dias_trabalho = horas_totais / 8  # considerando 8h/dia
            data_fim = data_inicio + datetime.timedelta(days=round(dias_trabalho))

            cronograma.append({
                "Serviço": linha["descricao"],
                "Profissional": nome_prof,
                "Qtd. Serviço": qtd,
                "Produtividade (h/un)": round(1/prod, 2),
                "Horas Totais": round(horas_totais, 2),
                "Dias": round(dias_trabalho, 1),
                "Início": data_inicio.strftime("%d/%m/%Y"),
                "Término": data_fim.strftime("%d/%m/%Y")
            })

    return pd.DataFrame(cronograma)

# Interface Streamlit
st.title("Planejador de Obra - Cronograma Automático via SINAPI")

uploaded_file = st.file_uploader("📤 Envie a planilha orçamentária", type=["xlsx"])

data_inicio = st.date_input("📅 Data de Início da Obra", datetime.date.today())
prazo_dias = st.number_input("⏳ Prazo Total (dias)", min_value=1, value=90)

if uploaded_file and st.button("📌 Gerar Cronograma"):
    try:
        orcamento_df = processar_orcamento(uploaded_file)
        sinapi_df = carregar_banco_sinapi()

        if sinapi_df is not None:
            cronograma_df = gerar_cronograma(orcamento_df, sinapi_df, data_inicio, prazo_dias)

            if not cronograma_df.empty:
                st.success("✅ Cronograma gerado com sucesso!")
                st.dataframe(cronograma_df)

                csv = cronograma_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Baixar Cronograma (CSV)", csv, "cronograma_obra.csv", "text/csv")
            else:
                st.warning("⚠️ Nenhum item do orçamento corresponde ao banco SINAPI.")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
