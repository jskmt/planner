import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📅 Planejador de Obra - Cronograma Automático com base no SINAPI")

# Inputs do usuário
data_inicio = st.date_input("Data de início da obra", datetime.today())
prazo_total = st.number_input("Prazo total da obra (em dias)", min_value=1, value=90)
uploaded_file = st.file_uploader("Envie sua planilha orçamentária", type=["xlsx"])

# Carrega o banco de dados SINAPI interno
@st.cache_data
def carregar_banco_sinapi():
    try:
        df_sinapi = pd.read_csv("banco_sinapi_profissionais_detalhado.csv", encoding="utf-8", delimiter=",", engine="python")
        df_sinapi["codigo_composicao"] = df_sinapi["CODIGO DA COMPOSICAO"].astype(str).str.strip()
        return df_sinapi
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

banco_sinapi = carregar_banco_sinapi()

# Processamento principal
def gerar_cronograma(df_orc, banco_sinapi):
    try:
        # Detecta as colunas corretas
        col_codigo = next(col for col in df_orc.columns if "CÓDIGO" in col.upper() and "COMPOSIÇÃO" in col.upper())
        col_servico = next(col for col in df_orc.columns if "INSUMO" in col.upper() or "SERVIÇO" in col.upper())
        col_quant = next(col for col in df_orc.columns if "QUANT" in col.upper())

        df_orc[col_codigo] = df_orc[col_codigo].astype(str).str.strip()
        df = df_orc[[col_codigo, col_servico, col_quant]].dropna()
        df.columns = ["codigo_composicao", "descricao", "quantidade"]
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)

        # Filtra as composições do SINAPI que existem no orçamento
        composicoes_orc = df["codigo_composicao"].unique()
        sinapi_filtrado = banco_sinapi[banco_sinapi["codigo_composicao"].isin(composicoes_orc)]

        if sinapi_filtrado.empty:
            st.warning("Nenhum item do orçamento corresponde ao banco SINAPI.")
            return

        cronograma = []
        dia_atual = data_inicio

        for _, row in df.iterrows():
            codigo = row["codigo_composicao"]
            qtd_total = row["quantidade"]

            comp = sinapi_filtrado[sinapi_filtrado["codigo_composicao"] == codigo]

            for _, prof in comp.iterrows():
                if prof["TIPO ITEM"] != "MÃO DE OBRA":
                    continue

                coef = prof["COEFICIENTE"]
                descricao = prof["DESCRIÇÃO ITEM"]
                jornada_dia = 8  # padrão

                try:
                    horas_totais = coef * qtd_total
                    dias_necessarios = round(horas_totais / jornada_dia, 2)

                    cronograma.append({
                        "Data Início": dia_atual.strftime("%d/%m/%Y"),
                        "Serviço": row["descricao"],
                        "Profissional": descricao,
                        "Qtd Serviço": qtd_total,
                        "Horas Totais": round(horas_totais, 2),
                        "Dias Necessários": dias_necessarios
                    })

                    dia_atual += timedelta(days=max(1, int(dias_necessarios)))  # incrementa dias
                except:
                    continue

        df_cronograma = pd.DataFrame(cronograma)
        return df_cronograma

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return None

# Execução
if uploaded_file is not None and banco_sinapi is not None:
    try:
        df_orc = pd.read_excel(uploaded_file, engine="openpyxl")
        df_crono = gerar_cronograma(df_orc, banco_sinapi)

        if df_crono is not None and not df_crono.empty:
            st.success("✅ Cronograma gerado com sucesso!")
            st.dataframe(df_crono, use_container_width=True)

            # Exporta como Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_crono.to_excel(writer, index=False, sheet_name="Cronograma")
            st.download_button("📥 Baixar Cronograma em Excel", data=output.getvalue(), file_name="cronograma.xlsx")
        else:
            st.warning("O cronograma está vazio. Verifique os dados da planilha.")
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
