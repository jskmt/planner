import streamlit as st
import pandas as pd

st.set_page_config(page_title="Planejador de Obra", layout="centered")

st.title("📊 Planejador de Obra com SINAPI")

# Inputs
data_inicio = st.date_input("Data de início da obra")
prazo_total = st.number_input("Prazo total (em dias)", min_value=1, step=1)
arquivo_planilha = st.file_uploader("📎 Envie sua planilha orçamentária (Excel)", type=["xlsx"])

def carregar_banco_sinapi():
    try:
        df = pd.read_csv("banco_sinapi_profissionais_detalhado.csv", sep=",", encoding="utf-8")
        # Padroniza os códigos para garantir a correspondência
        df["codigo_composicao"] = df["CODIGO DA COMPOSICAO"].astype(str).str.replace(".", "", regex=False).str.strip().str.zfill(11)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

def gerar_cronograma(df_orc, df_sinapi):
    try:
        # Tenta identificar colunas automaticamente
        col_codigo = next(col for col in df_orc.columns if "CÓDIGO" in col.upper())
        col_servico = next(col for col in df_orc.columns if "INSUMO" in col.upper() or "SERVIÇO" in col.upper())
        col_quant = next(col for col in df_orc.columns if "QUANT" in col.upper())

        # Padroniza códigos
        df_orc[col_codigo] = df_orc[col_codigo].astype(str).str.replace(".", "", regex=False).str.strip().str.zfill(11)

        cronograma = []

        for _, row in df_orc.iterrows():
            codigo = row[col_codigo]
            descricao = row[col_servico]
            try:
                quantidade = float(row[col_quant])
            except:
                continue

            composicao = df_sinapi[df_sinapi["codigo_composicao"] == codigo]

            if composicao.empty:
                continue

            profissionais = composicao[composicao["TIPO ITEM"].str.upper().str.contains("MÃO DE OBRA", na=False)]

            for _, prof in profissionais.iterrows():
                nome = prof["DESCRIÇÃO ITEM"]
                coef = prof["COEFICIENTE"]
                unidade = prof["UNIDADE ITEM"]
                total_horas = coef * quantidade
                cronograma.append({
                    "Serviço": descricao,
                    "Profissional": nome,
                    "Horas estimadas": round(total_horas, 2),
                    "Unidade": unidade
                })

        df_crono = pd.DataFrame(cronograma)
        return df_crono

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return pd.DataFrame()

# Execução principal
if arquivo_planilha and data_inicio and prazo_total:
    try:
        df_orc = pd.read_excel(arquivo_planilha, engine="openpyxl")
        banco = carregar_banco_sinapi()
        if banco is not None:
            resultado = gerar_cronograma(df_orc, banco)
            if not resultado.empty:
                st.success("✅ Cronograma gerado com sucesso!")
                st.dataframe(resultado)
                st.download_button("📥 Baixar cronograma (CSV)", data=resultado.to_csv(index=False), file_name="cronograma_obra.csv", mime="text/csv")
            else:
                st.warning("⚠️ O cronograma está vazio. Verifique se os códigos de composição da planilha existem no banco SINAPI.")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
