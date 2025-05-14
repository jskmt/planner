
import streamlit as st
import pandas as pd
from extrator_composicoes_empresa import extrair_composicoes

st.title("Planejador de Obra")

# Inputs do usuário
data_inicio = st.date_input("Data de início da obra")
prazo_total_dias = st.number_input("Prazo total (em dias)", min_value=1)
arquivo = st.file_uploader("Envie a planilha orçamentária (.xlsx)", type=["xlsx"])

# Processamento da planilha
if arquivo is not None:
    try:
        composicoes = extrair_composicoes(arquivo)
        st.success("Planilha processada com sucesso!")
        st.write("Composições extraídas:")
        st.dataframe(composicoes)
        
        # Aqui ainda entra a lógica de cronograma com banco SINAPI etc.
        st.info("A próxima etapa é integrar com o banco SINAPI e gerar o cronograma.")
    
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
