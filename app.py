import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Planejador de Obra")

st.title("Planejador de Obra com Banco SINAPI Embutido")

data_inicio = st.date_input("Data de início da obra")
prazo_total = st.number_input("Prazo total da obra (em dias)", min_value=1)

uploaded_file = st.file_uploader("Envie a planilha orçamentária (.xlsx)", type="xlsx")

# --- Banco SINAPI embutido ---
sinapi_csv = """
codigo_composicao;descricao_atividade;profissional;quantidade_por_atividade;produtividade_dia
95571;SERVIÇO DE EXEMPLO 1;Pedreiro;10;5
95572;SERVIÇO DE EXEMPLO 2;Servente;20;10
95573;SERVIÇO DE EXEMPLO 3;Armador;5;2
"""  # Aqui você insere todo o conteúdo real do CSV convertido para texto

df_sinapi = pd.read_csv(io.StringIO(sinapi_csv), sep=";")

if uploaded_file:
    try:
        # Detecta automaticamente onde começa a tabela
        xls = pd.ExcelFile(uploaded_file)
        for i in range(0, 20):  # Verifica até 20 primeiras linhas
            df_temp = pd.read_excel(xls, skiprows=i)
            if "Código" in df_temp.columns and "Descrição" in df_temp.columns:
                df_orcamento = df_temp
                break
        else:
            st.error("Erro: Não foram encontradas as colunas necessárias (Código, Descrição, Quant.).")
            st.stop()

        df_orcamento.columns = df_orcamento.columns.str.strip()
        col_codigo = 'Código'
        col_descricao = 'Descrição'
        col_quantidade = [col for col in df_orcamento.columns if 'Quant' in col][0]

        df_orcamento = df_orcamento[[col_codigo, col_descricao, col_quantidade]].dropna()

        # Geração do cronograma
        cronograma = []
        for _, row in df_orcamento.iterrows():
            codigo = str(row[col_codigo]).strip()
            descricao = row[col_descricao]
            quantidade = float(row[col_quantidade])

            sinapi_match = df_sinapi[df_sinapi['codigo_composicao'].astype(str) == codigo]

            if not sinapi_match.empty:
                for _, sinapi_row in sinapi_match.iterrows():
                    profissional = sinapi_row['profissional']
                    produtividade = sinapi_row['produtividade_dia']
                    duracao = quantidade / produtividade if produtividade > 0 else 0

                    cronograma.append({
                        "Código": codigo,
                        "Serviço": descricao,
                        "Profissional": profissional,
                        "Quantidade": quantidade,
                        "Produtividade (dia)": produtividade,
                        "Duração estimada (dias)": round(duracao, 2)
                    })

        if cronograma:
            df_crono = pd.DataFrame(cronograma)
            st.success("Cronograma gerado com sucesso!")
            st.dataframe(df_crono)
            st.download_button("Baixar Cronograma (.xlsx)", df_crono.to_excel(index=False), file_name="cronograma.xlsx")
        else:
            st.warning("Nenhuma correspondência com o banco SINAPI.")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
