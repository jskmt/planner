import streamlit as st
import pandas as pd
import difflib
import unicodedata

# Carregar banco SINAPI
@st.cache_data
def carregar_banco_sinapi():
    try:
        df = pd.read_csv("banco_sinapi_profissionais_detalhado.csv", encoding="utf-8", sep=",", engine="python")
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

# Normalizador de texto para comparação
def normalizar(texto):
    return unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII").lower()

# Função para encontrar composição similar por descrição
def encontrar_por_nome(descricao, banco):
    descricoes_sinapi = banco['descricao_composicao'].dropna().astype(str).map(normalizar)
    descricao_proc = normalizar(descricao)
    matches = difflib.get_close_matches(descricao_proc, descricoes_sinapi.tolist(), n=1, cutoff=0.8)
    if matches:
        match_desc = matches[0]
        return banco[descricoes_sinapi == match_desc]
    return pd.DataFrame()

# Função principal para gerar cronograma
def gerar_cronograma(planilha, banco):
    try:
        df = pd.read_excel(planilha, engine="openpyxl")
        df.columns = df.columns.str.strip().str.upper()
        colunas_necessarias = ['CÓDIGO', 'INSUMO/SERVIÇO', 'QUANTIDADE']
        if not all(col in df.columns for col in colunas_necessarias):
            raise ValueError("A planilha não contém colunas esperadas como 'CÓDIGO', 'INSUMO/SERVIÇO' ou 'QUANTIDADE'.")

        cronograma = []

        for _, linha in df.iterrows():
            codigo = str(linha['CÓDIGO']).strip()
            descricao = str(linha['INSUMO/SERVIÇO']).strip()
            try:
                quantidade = float(str(linha['QUANTIDADE']).replace(',', '.'))
            except:
                continue

            comp = banco[banco['codigo_composicao'].astype(str).str.strip() == codigo]
            if comp.empty:
                comp = encontrar_por_nome(descricao, banco)
            if comp.empty:
                continue

            profissionais = comp[comp['tipo_item'].str.lower() == 'mão de obra']
            for _, prof in profissionais.iterrows():
                nome_prof = prof['descrição item']
                coef = prof['coeficiente']
                horas = quantidade * coef * 8  # Considerando 8h/dia
                cronograma.append({
                    "Serviço": descricao,
                    "Profissional": nome_prof,
                    "Quantidade de Serviço": quantidade,
                    "Horas Necessárias": round(horas, 2)
                })

        if not cronograma:
            raise ValueError("⚠️ O cronograma está vazio. Verifique se os códigos ou descrições da planilha existem no banco SINAPI.")

        return pd.DataFrame(cronograma)

    except Exception as e:
        st.error(f"Erro ao processar a planilha:\n\n{e}")
        return None

# Interface do Streamlit
st.title("Planejador de Obra")
st.write("Carregue uma planilha orçamentária para gerar o cronograma baseado no banco SINAPI.")

uploaded_file = st.file_uploader("Faça upload da planilha (.xlsx)", type=["xlsx"])
data_inicio = st.date_input("Data de início da obra")
prazo_dias = st.number_input("Prazo total (em dias)", min_value=1, value=90)

if uploaded_file:
    banco = carregar_banco_sinapi()
    if banco is not None:
        cronograma_df = gerar_cronograma(uploaded_file, banco)
        if cronograma_df is not None:
            st.success("✅ Cronograma gerado com sucesso!")
            st.dataframe(cronograma_df)
            st.download_button("📥 Baixar cronograma em CSV", cronograma_df.to_csv(index=False), file_name="cronograma.csv")
