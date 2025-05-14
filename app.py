import streamlit as st
import pandas as pd
import datetime
import csv

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📊 Planejador de Obra com Base no SINAPI")

# -----------------------
# Função: Carregar banco SINAPI
# -----------------------
@st.cache_data
def carregar_banco_sinapi():
    try:
        with open("banco_sinapi_profissionais_detalhado.csv", "r", encoding="utf-8") as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            return pd.read_csv(f, delimiter=dialect.delimiter, engine="python")
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return pd.DataFrame()

# -----------------------
# Função: Ler planilha orçamentária
# -----------------------
def ler_planilha_orcamento(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl", skiprows=7)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Tenta identificar as colunas principais
        col_codigo = next((c for c in df.columns if "CÓDIGO" in c), None)
        col_servico = next((c for c in df.columns if "INSUMO" in c or "SERVIÇO" in c), None)
        col_qtd = next((c for c in df.columns if "QUANTIDADE" in c), None)

        if not all([col_codigo, col_servico, col_qtd]):
            raise ValueError("Não foi possível localizar todas as colunas necessárias (composição, serviço, quantidade).")

        df = df[[col_codigo, col_servico, col_qtd]]
        df.columns = ['composicao', 'servico', 'quantidade']
        df.dropna(subset=['composicao', 'servico', 'quantidade'], inplace=True)
        return df

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return pd.DataFrame()

# -----------------------
# Função: Gerar cronograma
# -----------------------
def gerar_cronograma(df_orcamento, df_sinapi, data_inicio, prazo_total):
    cronograma = []

    for _, row in df_orcamento.iterrows():
        codigo = str(row['composicao']).strip()
        servico = row['servico']
        quantidade = float(row['quantidade'])

        composicoes = df_sinapi[df_sinapi['codigo'] == codigo]

        if composicoes.empty:
            continue

        for _, item in composicoes.iterrows():
            profissional = item['profissional']
            produtividade = item['quantidade_por_dia']

            if produtividade <= 0:
                continue

            dias_necessarios = quantidade / produtividade
            dias_necessarios = int(dias_necessarios) + 1

            data_fim = data_inicio + datetime.timedelta(days=dias_necessarios)
            profissionais_necessarios = 1  # Pode-se estimar divisão aqui

            cronograma.append({
                "Serviço": f"{codigo} - {servico}",
                "Início": data_inicio.strftime("%d/%m/%Y"),
                "Dias de Duração": dias_necessarios,
                "Término": data_fim.strftime("%d/%m/%Y"),
                "Profissional": profissional,
                "Qtd. Profissionais": profissionais_necessarios,
                "Produtividade (un/dia)": produtividade
            })

            data_inicio = data_fim

    return pd.DataFrame(cronograma)

# -----------------------
# Interface do usuário
# -----------------------
with st.sidebar:
    st.header("📥 Entrada de Dados")
    uploaded_file = st.file_uploader("Upload da planilha de orçamento (.xlsx)", type="xlsx")
    data_inicio = st.date_input("Data de Início da Obra", datetime.date.today())
    prazo_total = st.number_input("Prazo Total (dias)", min_value=1, value=90)

# -----------------------
# Execução
# -----------------------
df_sinapi = carregar_banco_sinapi()

if uploaded_file and data_inicio and prazo_total:
    df_orcamento = ler_planilha_orcamento(uploaded_file)

    if not df_orcamento.empty and not df_sinapi.empty:
        st.subheader("📅 Cronograma Gerado")
        cronograma = gerar_cronograma(df_orcamento, df_sinapi, data_inicio, prazo_total)
        st.dataframe(cronograma, use_container_width=True)

        # Download do Excel
        excel_output = cronograma.to_excel(index=False, engine='openpyxl')
        st.download_button(
            label="📥 Baixar Cronograma (.xlsx)",
            data=excel_output,
            file_name="cronograma_obra.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
