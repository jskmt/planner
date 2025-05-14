import pandas as pd

def extrair_composicoes(planilha):
    try:
        # Lê a planilha usando a linha 5 como cabeçalho (índice 4 no pandas)
        df = pd.read_excel(planilha, header=4)

        # Renomear colunas relevantes para facilitar
        df = df.rename(columns={
            df.columns[1]: 'codigo_composicao',
            df.columns[3]: 'servico',
            df.columns[7]: 'quantidade'
        })

        # Filtrar colunas necessárias
        df_filtrado = df[['codigo_composicao', 'servico', 'quantidade']]

        # Remove linhas com valores faltantes
        df_filtrado = df_filtrado.dropna(subset=['codigo_composicao', 'servico', 'quantidade'])

        return df_filtrado

    except Exception as e:
        raise ValueError(f"Erro ao processar a planilha: {e}")
