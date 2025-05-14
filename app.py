import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import math

# Carregar banco SINAPI embutido
@st.cache_data
def carregar_banco_sinapi():
    sinapi_csv = """codigo_servico,descricao_servico,codigo_profissional,profissional,unidade,quantidade,hora_homens
0001,LADRILHO CERÂMICO PAREDE,101,Servente,MH,0.35,0.7
0001,LADRILHO CERÂMICO PAREDE,102,Pedreiro,MH,0.65,1.3
0002,REBOCO INTERNO,101,Servente,MH,0.25,0.5
0002,REBOCO INTERNO,102,Pedreiro,MH,0.75,1.5
0003,ALVENARIA DE BLOCO,102,Pedreiro,MH,1.2,2.4
0003,ALVENARIA DE BLOCO,101,Servente,MH,0.8,1.6
"""  # Banco reduzido de exemplo
    return pd.read_csv(io.StringIO(sinapi_csv))

# Processar planilha orçamentária
def processar_orcamento(uploaded_file):
    for skip in range(0, 15):
        df = pd.read_excel(uploaded_file, skiprows=skip)
        if {"Código", "Descrição", "Quant."}.issubset(df.columns):
            df = df[["Código", "Descrição", "Quant."]].dropna()
            df.columns = ["codigo", "descricao", "quantidade"]
            return df
    raise ValueError("Colunas esperadas não encontradas.")

# Gerar cronograma com base na produtividade
def gerar_cronograma(df_orc, df_sinapi, data_inicio, prazo_total_dias):
    cronograma = []
    for _, item in df_orc.iterrows():
        cod = str(item["codigo"]).zfill(4)
        desc = item["descricao"]
        quant = float(str(item["quantidade"]).replace(",", "."))
        comp = df_sinapi[df_sinapi["codigo_servico"] == cod]
        if comp.empty:
            continue
        for _, prof in comp.iterrows():
            horas_totais = quant * float(prof["hora_homens"])
            profs_necessarios = max(1, math.ceil(horas_totais / (prazo_total_dias * 8)))
            dias_estimados = math.ceil(horas_totais / (profs_necessarios * 8))
            cronograma.append({
                "Código Serviço": cod,
                "Descrição Serviço": desc,
                "Profissional": prof["profissional"],
                "Total Horas-Homens": round(horas_totais, 2),
                "Profissionais Necessários": profs_necessarios,
                "Dias Estimados": dias_estimados,
                "Início Previsto": data_inicio.strftime('%d/%m/%Y'),
                "Término Previsto": (data_inicio + timedelta(days=dias_estimados)).strftime('%d/%m/%Y')
            })
    return pd.DataFrame(cronograma)

# Interface do chatbot com Streamlit
st.set_page_config(page_title="Planejador de Obra", layout="centered")
st.title("🏗️ Planejador de Execução de Obra com Base no SINAPI")

uploaded_file = st.file_uploader("📤 Faça o upload da planilha de orçamento (.xlsx)", type=["xlsx"])
data_inicio = st.date_input("📅 Data de início da obra", value=datetime.today())
prazo_dias = st.number_input("⏱️ Prazo total da obra (em dias úteis)", min_value=1, value=30)

if uploaded_file and data_inicio and prazo_dias:
    try:
        df_orc = processar_orcamento(uploaded_file)
        df_sinapi = carregar_banco_sinapi()
        cronograma = gerar_cronograma(df_orc, df_sinapi, data_inicio, prazo_dias)
        if not cronograma.empty:
            st.success("✅ Cronograma gerado com sucesso!")
            st.dataframe(cronograma)
            csv = cronograma.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Cronograma", data=csv, file_name="cronograma_execucao.csv", mime="text/csv")
        else:
            st.warning("⚠️ Nenhuma correspondência encontrada no banco SINAPI.")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
