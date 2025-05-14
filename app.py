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
            sep=",",
            encoding="utf-8",
            on_bad_lines="skip",
            engine="python"
        )

        # Renomear colunas para uso interno padronizado
        df.rename(columns={
            "CODIGO DA COMPOSICAO": "codigo_composicao",
            "DESCRIÇÃO ITEM": "descricao_item",
            "TIPO ITEM": "tipo_item",
            "COEFICIENTE": "coeficiente"
        }, inplace=True)

        # Filtra apenas mão de obra
        df = df[df["tipo_item"].str.lower().str.contains("mão de obra", na=False)]

        # Trata tipo da coluna coeficiente
        df["coeficiente"] = pd.to_numeric(df["coeficiente"], errors="coerce")
        df.dropna(subset=["coeficiente"], inplace=True)

        # Prepara o dataframe final para uso
        df["codigo_composicao"] = df["codigo_composicao"].astype(str).str.zfill(4)
        return df[["codigo_composicao", "descricao_item", "coeficiente"]]

    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None


# Função para gerar cronograma
def gerar_cronograma(planilha, banco_sinapi):
    try:
        df_orc = pd.read_excel(planilha)

        # Renomeia as colunas para evitar erro com nomes diferentes
        df_orc.rename(columns=lambda x: x.strip().upper(), inplace=True)

        # Corrige nome das colunas esperadas
        col_codigo = [col for col in df_orc.columns if "CÓDIGO" in col][0]
        col_servico = [col for col in df_orc.columns if "INSUMO" in col or "SERVIÇO" in col][0]
        col_quant = [col for col in df_orc.columns if "QUANT" in col][0]

        df_orc = df_orc[[col_codigo, col_servico, col_quant]]
        df_orc.columns = ["codigo_composicao", "descricao", "quantidade"]

        # Limpa e normaliza os códigos de composição
        df_orc["codigo_composicao"] = (
            df_orc["codigo_composicao"]
            .astype(str)
            .str.replace(r"[^\d]", "", regex=True)
            .str.zfill(7)
        )

        banco_sinapi["codigo_composicao"] = (
            banco_sinapi["codigo_composicao"]
            .astype(str)
            .str.replace(r"[^\d]", "", regex=True)
            .str.zfill(7)
        )

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
            st.error("Nenhum item do orçamento corresponde ao banco SINAPI.")
            return

        df_crono = pd.DataFrame(cronograma)
        st.success("Cronograma gerado com sucesso!")
        st.dataframe(df_crono)

        csv = df_crono.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Cronograma", data=csv, file_name="cronograma.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")


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
