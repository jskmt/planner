import pandas as pd
import unicodedata
from difflib import get_close_matches

def normalize_text(text):
    if pd.isna(text):
        return ''
    text = str(text).lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.strip()

def preprocess_data(df):
    # normaliza código
    df['CODIGO DA COMPOSICAO'] = df['CODIGO DA COMPOSICAO'].astype(str).str.split('.').str[0].str.strip()
    # normaliza descrição
    df['desc_norm'] = df['DESCRICAO DA COMPOSICAO'].apply(normalize_text)
    return df

def buscar_composicao(codigo, descricao, banco):
    codigo_str = str(codigo).split('.')[0].strip()
    descricao_norm = normalize_text(descricao)
    
    comp = banco[banco['CODIGO DA COMPOSICAO'] == codigo_str]
    if not comp.empty:
        return comp
    
    descricoes = banco['desc_norm'].tolist()
    matches = get_close_matches(descricao_norm, descricoes, n=1, cutoff=0.6)
    if matches:
        return banco[banco['desc_norm'] == matches[0]]
    
    return pd.DataFrame()

# Exemplo simples de uso
banco_sinapi = pd.read_csv('banco_sinapi.csv', delimiter=',', decimal=',')
planilha_obra = pd.read_csv('planilha_obra.csv', delimiter=',', decimal=',')

banco_sinapi = preprocess_data(banco_sinapi)
planilha_obra = preprocess_data(planilha_obra)

# Agora pode rodar seu processamento normalmente...
