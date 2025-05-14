import pandas as pd

def extrair_composicoes_planilha_padroes_empresa(caminho_arquivo):
    # Lê a planilha com as composições
    df = pd.read_excel(caminho_arquivo, sheet_name=0)

    # Procurar as colunas principais por nome (flexível)
    colunas_necessarias = {
        "codigo": None,
        "descricao": None,
        "quantidade": None
    }

    # Identificar colunas relevantes com base no nome
    for col in df.columns:
        col_lower = col.lower()
        if "composição" in col_lower and colunas_necessarias["codigo"] is None:
            colunas_necessarias["codigo"] = col
        elif "serviço" in col_lower and colunas_necessarias["descricao"] is None:
            colunas_necessarias["descricao"] = col
        elif "quantidade" in col_lower and colunas_necessarias["quantidade"] is None:
            colunas_necessarias["quantidade"] = col

    # Verifica se todas foram encontradas
    if None in colunas_necessarias.values():
        raise ValueError("Não foi possível localizar todas as colunas necessárias (composição, serviço, quantidade).")

    # Cria DataFrame filtrado com as colunas certas
    df_filtrado = df[[colunas_necessarias["codigo"], 
                      colunas_necessarias["descricao"], 
                      colunas_necessarias["quantidade"]]].copy()

    df_filtrado.columns = ["codigo_composicao", "descricao_servico", "quantidade"]

    # Remove linhas onde o código está vazio ou NaN
    df_filtrado = df_filtrado.dropna(subset=["codigo_composicao"])

    # Garante que os códigos são string (para cruzamento com banco SINAPI)
    df_filtrado["codigo_composicao"] = df_filtrado["codigo_composicao"].astype(str)

    return df_filtrado
