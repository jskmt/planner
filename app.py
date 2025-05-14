import streamlit as st
import pandas as pd
import io

# Carrega o banco SINAPI embutido
@st.cache_data
def carregar_banco_sinapi():
    try:
        sinapi_data = """codigo_servico,descricao_servico,codigo_profissional,profissional,unidade,quantidade,hora_homens
0001,LADRILHO CERÂMICO PAREDE,101,Servente,MH,0.35,0.7
0001,LADRILHO CERÂMICO PAREDE,102,Pedreiro,MH,0.65,1.3
0002,REBOCO INTERNO,101,Servente,MH,0.25,0.5
0002,REBOCO INTERNO,102,Pedreiro,MH,0.75,1.5
"""  # Exemplo mínimo
        df = pd.read_csv(io.StringIO(sinapi_data), sep=",")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

# Processa a planilha de orçamento
def processar_orcamento(arquivo):
    try:
        for i in range(0, 15):
            df = pd.read_excel(arquivo, skiprows=i)
            if "Código" in df.columns and "Descrição" in df.columns and "Quant." in df.columns:
                df = df[["Código", "Descrição", "Quant."]].dropna()
                df.columns = ["codigo", "descricao", "quantidade"]
                return df
        raise ValueError("Não foram encontradas todas as colunas esperadas: Código, Descrição, Quant.")
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return None

# Gera o cronograma com base no banco SINAPI
def gerar_cronograma(df_orc, df_sinapi):
    cronograma = []
    for _, linha in df_orc.iterrows():
        cod = str(linha["codigo"]).strip()
        quant = float(str(linha["quantidade"]).replace(",", "."))
        comp_sinapi = df_sinapi[df_sinapi["codigo_servico"] == cod]
        for _, prof in comp_sinapi.iterrows():
            total_horas = quant * float(prof["hora_homens"])
            cronograma.append({
                "Código Serviço": cod,
                "Descrição Serviço": linha["descricao"],
                "Profissional": prof["profissional"],
                "Quantidade Total (h)": round(total_horas, 2)
            })
    return pd.DataFrame(cronograma)

# Streamlit UI
st.title("Planejador de Obra")
arquivo_orcamento = st.file_uploader("Faça upload da planilha de orçamento (.xlsx)", type=["xlsx"])
if arquivo_orcamento:
    df_orc = processar_orcamento(arquivo_orcamento)
    df_sinapi = carregar_banco_sinapi()
    if df_orc is not None and df_sinapi is not None:
        cronograma = gerar_cronograma(df_orc, df_sinapi)
        st.success("Cronograma gerado com sucesso!")
        st.dataframe(cronograma)
        csv = cronograma.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar Cronograma", csv, "cronograma.csv", "text/csv")
