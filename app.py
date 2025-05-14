import streamlit as st
import pandas as pd

# Título
st.title("Planejador de Obra com Banco SINAPI")

# Inputs principais
data_inicio = st.date_input("Data de início da obra")
prazo_total = st.number_input("Prazo total (em dias)", min_value=1)

# Upload da planilha orçamentária
uploaded_file = st.file_uploader("Faça upload da planilha orçamentária (.xlsx)", type="xlsx")

# Upload do banco SINAPI
sinapi_file = st.file_uploader("Faça upload do banco SINAPI (.csv)", type="csv")

if uploaded_file and sinapi_file:
    try:
        # Lê a planilha orçamentária
        df_orcamento = pd.read_excel(uploaded_file, skiprows=5)
        
        # Ajuste dos nomes das colunas (conforme o print enviado)
        df_orcamento.columns = df_orcamento.columns.str.strip()  # remove espaços extras
        col_codigo = 'Código'
        col_descricao = 'Descrição'
        col_quantidade = 'Quant.'

        if not all(col in df_orcamento.columns for col in [col_codigo, col_descricao, col_quantidade]):
            st.error("Erro: Não foram encontradas todas as colunas esperadas: Código, Descrição, Quant.")
        else:
            df_orcamento = df_orcamento[[col_codigo, col_descricao, col_quantidade]]
            df_orcamento = df_orcamento.dropna()

            # Lê o banco SINAPI
            try:
                df_sinapi = pd.read_csv(sinapi_file, sep=";", encoding="utf-8", on_bad_lines='skip')
            except:
                st.error("Erro ao carregar banco SINAPI. Verifique o arquivo CSV.")
                st.stop()

            # Junta as informações de produtividade
            cronograma = []
            for _, row in df_orcamento.iterrows():
                codigo = str(row[col_codigo]).strip()
                descricao = row[col_descricao]
                quantidade = float(row[col_quantidade])

                sinapi_match = df_sinapi[df_sinapi['codigo_composicao'] == codigo]

                if not sinapi_match.empty:
                    for _, sinapi_row in sinapi_match.iterrows():
                        profissional = sinapi_row['profissional']
                        produtividade_dia = sinapi_row['produtividade_dia']

                        if produtividade_dia > 0:
                            duracao_dias = quantidade / produtividade_dia
                        else:
                            duracao_dias = 0

                        cronograma.append({
                            "Código": codigo,
                            "Serviço": descricao,
                            "Profissional": profissional,
                            "Quantidade": quantidade,
                            "Produtividade (dia)": produtividade_dia,
                            "Duração estimada (dias)": round(duracao_dias, 2)
                        })

            df_cronograma = pd.DataFrame(cronograma)

            st.success("Cronograma gerado com sucesso!")
            st.dataframe(df_cronograma)

            # Exportar como Excel
            cronograma_excel = df_cronograma.to_excel(index=False)
            st.download_button("Baixar Cronograma (.xlsx)", cronograma_excel, file_name="cronograma.xlsx")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
