import streamlit as st
import pandas as pd
import io

# Título
st.set_page_config(page_title="Planejador de Obra", layout="centered")
st.title("📅 Planejador de Obra com base no SINAPI")

# Inputs do usuário
uploaded_file = st.file_uploader("Faça upload da planilha orçamentária", type=["xlsx"])
data_inicio = st.date_input("Data de início da obra")
prazo_dias = st.number_input("Prazo total (em dias)", min_value=1, value=30)

# Carrega banco SINAPI interno
@st.cache_data
def carregar_banco_sinapi():
    try:
        with open("banco_sinapi_profissionais_detalhado.csv", "r", encoding="utf-8") as f:
            return pd.read_csv(f, sep=",", engine="python")
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

banco_sinapi = carregar_banco_sinapi()

# Função principal
def gerar_cronograma(planilha, banco_sinapi):
    try:
        df_orc = pd.read_excel(planilha)

        # Renomeia colunas para facilitar busca
        df_orc.rename(columns=lambda x: x.strip().upper(), inplace=True)

        # Identifica colunas de código, serviço e quantidade
                try:
            col_codigo = next(col for col in df_orc.columns if "CÓDIGO" in col)
            col_servico = next(col for col in df_orc.columns if "INSUMO" in col or "SERVIÇO" in col)
            col_quant = next(col for col in df_orc.columns if "QUANT" in col)
        except StopIteration:
            st.error("Erro: A planilha não contém colunas esperadas como 'CÓDIGO', 'INSUMO/SERVIÇO' ou 'QUANTIDADE'.")
            return


        df_orc = df_orc[[col_codigo, col_servico, col_quant]]
        df_orc.columns = ["codigo_composicao", "descricao", "quantidade"]

        # Padroniza os códigos
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

        # Geração do cronograma
        cronograma = []

        for _, row in df_orc.iterrows():
            codigo = row["codigo_composicao"]
            quantidade = row["quantidade"]

            try:
                quantidade = float(quantidade)
            except:
                continue

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

        # Exibição e download
        st.success("Cronograma gerado com sucesso!")
        st.dataframe(df_crono)

        csv = df_crono.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Cronograma", data=csv, file_name="cronograma.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")

# Execução
if uploaded_file and banco_sinapi is not None:
    gerar_cronograma(uploaded_file, banco_sinapi)
