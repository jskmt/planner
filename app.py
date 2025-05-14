import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Título do app
st.title("Planejador de Obra")

# Inputs do usuário
data_inicio = st.date_input("Data de início da obra")
prazo_total_dias = st.number_input("Prazo total para execução (em dias)", min_value=1)

# Upload da planilha de orçamento
uploaded_file = st.file_uploader("Envie a Planilha Orçamentária (.xlsx)", type=["xlsx"])

# Carregar banco SINAPI
@st.cache_data
def carregar_banco_sinapi():
    try:
        return pd.read_csv("banco_sinapi_profissionais_detalhado.csv", sep=";", encoding="utf-8")
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return pd.DataFrame()

banco_sinapi = carregar_banco_sinapi()

# Processamento da planilha orçamentária
def processar_planilha(planilha):
    try:
        df = pd.read_excel(planilha, engine="openpyxl")

        # Normalizando colunas
        colunas_esperadas = {
            "Composição": ["COMPOSIÇÃO", "CODIGO", "CÓDIGO", "Código Composição"],
            "Serviço": ["SERVIÇO", "DESCRIÇÃO", "DESCRICAO"],
            "Quantidade": ["QTDE", "QUANTIDADE", "QTD"]
        }

        colunas_encontradas = {}
        for key, possibilidades in colunas_esperadas.items():
            for p in possibilidades:
                if p in df.columns:
                    colunas_encontradas[key] = p
                    break

        if len(colunas_encontradas) < 3:
            raise Exception("Não foi possível localizar todas as colunas necessárias (composição, serviço, quantidade).")

        df = df[[colunas_encontradas["Composição"], colunas_encontradas["Serviço"], colunas_encontradas["Quantidade"]]]
        df.columns = ["composicao", "servico", "quantidade"]
        return df

    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
        return pd.DataFrame()

# Geração de cronograma
def gerar_cronograma(df_orcamento, banco_sinapi):
    cronograma = []
    data_atual = data_inicio

    for _, row in df_orcamento.iterrows():
        codigo = str(row['composicao']).strip()
        servico = row['servico']
        qtd = float(row['quantidade'])

        sinapi_match = banco_sinapi[banco_sinapi['codigo'] == codigo]
        if sinapi_match.empty:
            continue

        for _, item in sinapi_match.iterrows():
            produtividade = item['producao_por_dia']
            profissional = item['descricao']
            if produtividade <= 0:
                continue

            dias_necessarios = qtd / produtividade
            dias_necessarios = max(1, int(round(dias_necessarios)))
            data_final = data_atual + timedelta(days=dias_necessarios)

            cronograma.append({
                "Serviço": servico,
                "Código Composição": codigo,
                "Início": data_atual.strftime("%d/%m/%Y"),
                "Duração (dias)": dias_necessarios,
                "Fim": data_final.strftime("%d/%m/%Y"),
                "Profissional": profissional,
                "Produtividade": produtividade,
                "Qtd Profissionais": round(qtd / (produtividade * dias_necessarios), 2)
            })

            data_atual = data_final

    return pd.DataFrame(cronograma)

# Execução principal
if uploaded_file and data_inicio and prazo_total_dias:
    orcamento_df = processar_planilha(uploaded_file)
    if not orcamento_df.empty:
        cronograma_df = gerar_cronograma(orcamento_df, banco_sinapi)
        if not cronograma_df.empty:
            st.success("Cronograma gerado com sucesso!")
            st.dataframe(cronograma_df)

            # Baixar planilha
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cronograma_df.to_excel(writer, index=False)
            st.download_button(
                label="📥 Baixar Cronograma (.xlsx)",
                data=output.getvalue(),
                file_name="cronograma_obra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhuma composição do orçamento foi encontrada no banco SINAPI.")
