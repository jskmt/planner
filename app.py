import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Função para carregar banco SINAPI
@st.cache_data
def carregar_banco_sinapi(caminho_csv):
    return pd.read_csv(caminho_csv, sep=";", encoding="utf-8")

# Função para identificar quantidade mesmo com nome diferente
def detectar_coluna_quantidade(df):
    for col in df.columns:
        col_normalizado = str(col).strip().lower()
        if 'quant' in col_normalizado:
            return col
    return None

# Função principal
def main():
    st.title("📅 Gerador de Cronograma de Obra com Base no SINAPI")
    
    planilha = st.file_uploader("📥 Envie sua planilha orçamentária (.xlsx)", type=["xlsx"])
    banco = st.file_uploader("📥 Envie o banco SINAPI (.csv)", type=["csv"])
    
    if planilha and banco:
        try:
            df_planilha = pd.read_excel(planilha, engine="openpyxl", header=4)
            df_sinapi = carregar_banco_sinapi(banco)

            col_quantidade = detectar_coluna_quantidade(df_planilha)
            if not col_quantidade:
                st.error("❌ Coluna de quantidade não encontrada na planilha.")
                return

            atividades = []
            for _, row in df_planilha.iterrows():
                codigo = str(row.get("Código", "")).strip()
                descricao = str(row.get("Descrição", "")).strip()
                try:
                    quantidade = float(str(row.get(col_quantidade, 0)).replace(",", "."))
                except:
                    quantidade = 0

                if not codigo or quantidade <= 0:
                    st.warning(f"⚠️ Quantidade zero ou inválida na linha: 📦 Código: {codigo}, Descrição: {descricao}, Quantidade lida: {quantidade}")
                    continue

                dados_banco = df_sinapi[df_sinapi['codigo'] == codigo]
                if dados_banco.empty:
                    st.warning(f"❓ Código {codigo} não encontrado no banco SINAPI.")
                    continue

                dados_banco = dados_banco.iloc[0]
                produtividade_dia = dados_banco['produtividade_dia']
                profissionais = int(dados_banco['profissionais'])

                if produtividade_dia <= 0 or profissionais <= 0:
                    st.warning(f"🚫 Dados incompletos para o código {codigo}.")
                    continue

                dias_necessarios = np.ceil(quantidade / produtividade_dia)
                atividades.append({
                    "Código": codigo,
                    "Descrição": descricao,
                    "Quantidade": quantidade,
                    "Produtividade (un/dia)": produtividade_dia,
                    "Profissionais": profissionais,
                    "Dias necessários": int(dias_necessarios)
                })

            if atividades:
                df_cronograma = pd.DataFrame(atividades)

                st.subheader("📋 Cronograma Gerado")
                st.dataframe(df_cronograma)

                data_inicio = st.date_input("🗓️ Data de início da obra", datetime.date.today())
                df_cronograma["Início"] = [data_inicio + datetime.timedelta(days=int(sum(df_cronograma["Dias necessários"][:i]))) for i in range(len(df_cronograma))]
                df_cronograma["Término"] = df_cronograma["Início"] + pd.to_timedelta(df_cronograma["Dias necessários"], unit="D")

                st.subheader("📅 Cronograma com Datas")
                st.dataframe(df_cronograma[["Código", "Descrição", "Início", "Término", "Dias necessários", "Profissionais"]])

                # Download
                st.download_button("📥 Baixar Cronograma Excel", df_cronograma.to_csv(index=False).encode("utf-8"), "cronograma.csv", "text/csv")

            else:
                st.error("Nenhuma atividade válida foi processada.")

        except Exception as e:
            st.error(f"Erro ao processar os arquivos: {e}")

if __name__ == "__main__":
    main()
