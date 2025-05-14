import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📅 Planejador de Obra com base no SINAPI")

st.markdown("Faça o upload da planilha de orçamento e o cronograma será gerado automaticamente com base no banco SINAPI.")

def gerar_cronograma(df_orcamento, banco_sinapi):
    try:
        df = df_orcamento.copy()

        # Renomear colunas para evitar erro com nomes diferentes
        df.rename(columns=lambda x: x.strip().upper(), inplace=True)

        col_codigo = [col for col in df.columns if "CÓDIGO" in col][0]
        col_servico = [col for col in df.columns if "INSUMO" in col or "SERVIÇO" in col][0]
        col_quant = [col for col in df.columns if "QUANT" in col][0]

        df = df[[col_codigo, col_servico, col_quant]]
        df.columns = ["codigo_composicao", "descricao", "quantidade"]

        # Padroniza os códigos de composição (remove pontos, espaços, etc.)
        df["codigo_composicao"] = (
            df["codigo_composicao"]
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

        for _, row in df.iterrows():
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
        st.success("✅ Cronograma gerado com sucesso!")
        st.dataframe(df_crono)

        csv = df_crono.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Cronograma", data=csv, file_name="cronograma.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")

def main():
    uploaded_file = st.file_uploader("📂 Envie a planilha de orçamento (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_orc = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
            return

        # Banco SINAPI embutido no app
        try:
            sinapi_csv = """
codigo_composicao,descricao_item,coeficiente
7010101,SERVENTE,2.5
7010101,PEDREIRO,1.2
7010202,ELETRICISTA,1.0
7010303,ENCANADOR,1.3
"""
            banco_sinapi = pd.read_csv(io.StringIO(sinapi_csv))
        except Exception as e:
            st.error(f"Erro ao carregar banco SINAPI: {e}")
            return

        gerar_cronograma(df_orc, banco_sinapi)

if __name__ == "__main__":
    main()
