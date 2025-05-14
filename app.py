import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Planejador de Obra", layout="centered")
st.title("📅 Planejador de Obra - Cronograma Automatizado")

# Carrega o banco SINAPI interno
@st.cache_data
def carregar_banco_sinapi():
    try:
        df = pd.read_csv("banco_sinapi_profissionais_detalhado.csv", sep=",", encoding="utf-8")
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

# Função para gerar cronograma
def gerar_cronograma(planilha, data_inicio, prazo_dias, sinapi):
    try:
        df_orc = pd.read_excel(planilha, engine="openpyxl")
        df_orc.columns = df_orc.columns.str.strip().str.upper()

        try:
            col_codigo = next(col for col in df_orc.columns if "CÓDIGO" in col)
            col_servico = next(col for col in df_orc.columns if "INSUMO" in col or "SERVIÇO" in col)
            col_quant = next(col for col in df_orc.columns if "QUANT" in col)
        except StopIteration:
            st.error("Erro: A planilha não contém colunas esperadas como 'CÓDIGO', 'INSUMO/SERVIÇO' ou 'QUANTIDADE'.")
            return

        atividades = []
        for _, row in df_orc.iterrows():
            cod = str(row[col_codigo]).strip()
            desc = str(row[col_servico]).strip()
            try:
                quant = float(str(row[col_quant]).replace(",", "."))
            except:
                continue

            comp = sinapi[sinapi["codigo_composicao"] == cod]
            if comp.empty:
                continue

            profs = comp[comp["tipo_item"] == "MÃO DE OBRA"]
            for _, prof in profs.iterrows():
                nome_prof = prof["descricao_item"]
                coef = prof["coeficiente"]
                total_horas = coef * quant
                atividades.append({
                    "Serviço": desc,
                    "Profissional": nome_prof,
                    "Horas Totais": round(total_horas, 2),
                    "Código Composição": cod,
                    "Quantidade": quant
                })

        if not atividades:
            st.warning("Nenhum item do orçamento corresponde ao banco SINAPI.")
            return

        cronograma = []
        dia_atual = datetime.strptime(data_inicio, "%Y-%m-%d")
        dias_disponiveis = [dia_atual + timedelta(days=i) for i in range(prazo_dias)]

        for idx, atv in enumerate(atividades):
            dia_execucao = dias_disponiveis[idx % len(dias_disponiveis)]
            cronograma.append({
                "Data": dia_execucao.strftime("%Y-%m-%d"),
                "Serviço": atv["Serviço"],
                "Profissional": atv["Profissional"],
                "Horas previstas": atv["Horas Totais"],
                "Código": atv["Código Composição"],
                "Quantidade": atv["Quantidade"]
            })

        df_cronograma = pd.DataFrame(cronograma)
        st.success("✅ Cronograma gerado com sucesso!")
        st.dataframe(df_cronograma)

        csv = df_cronograma.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Cronograma em CSV", csv, "cronograma_obra.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")

# Inputs da interface
with st.form("form_cronograma"):
    planilha = st.file_uploader("📤 Envie sua planilha orçamentária (.xlsx)", type=["xlsx"])
    data_inicio = st.date_input("📆 Data de início da obra", datetime.today())
    prazo = st.number_input("⏳ Prazo total da obra (em dias)", min_value=1, value=30)
    submitted = st.form_submit_button("Gerar Cronograma")

    if submitted and planilha:
        banco = carregar_banco_sinapi()
        if banco is not None:
            gerar_cronograma(planilha, str(data_inicio), prazo, banco)
