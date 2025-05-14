import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📅 Planejador de Obra com Banco SINAPI")

def carregar_banco_sinapi(caminho_csv):
    try:
        return pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

def encontrar_por_nome(descricao, banco):
    desc_normalizada = descricao.lower().strip()
    candidatos = banco[banco['descricao_composicao'].str.lower().str.contains(desc_normalizada[:10])]
    return candidatos

def gerar_cronograma(planilha, banco, data_inicio, prazo_dias):
    try:
        df = pd.read_excel(planilha, engine="openpyxl")
        df.columns = df.columns.str.strip().str.upper()

        # Mapeamento inteligente
        mapa_colunas = {
            'CÓDIGO': ['CÓDIGO', 'CODIGO', 'CÓDIGO DA COMPOSIÇÃO'],
            'INSUMO/SERVIÇO': ['INSUMO/SERVIÇO', 'DESCRIÇÃO', 'DESCRIÇÃO COMPLETA', 'SERVIÇO'],
            'QUANTIDADE': ['QUANTIDADE', 'QUANT.', 'QTDE']
        }

        colunas_mapeadas = {}
        for padrao, opcoes in mapa_colunas.items():
            for col in df.columns:
                if col in opcoes:
                    colunas_mapeadas[padrao] = col
                    break

        if len(colunas_mapeadas) < 3:
            raise ValueError("A planilha não contém colunas esperadas como 'CÓDIGO', 'INSUMO/SERVIÇO' ou 'QUANTIDADE'.")

        cronograma = []
        dia_atual = data_inicio

        for _, linha in df.iterrows():
            codigo = str(linha[colunas_mapeadas['CÓDIGO']]).strip()
            descricao = str(linha[colunas_mapeadas['INSUMO/SERVIÇO']]).strip()
            try:
                quantidade = float(str(linha[colunas_mapeadas['QUANTIDADE']]).replace(',', '.'))
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
                horas = quantidade * coef * 8  # 8h/dia * coef

                duracao_dias = max(1, round(horas / 8))  # assume 8h por dia
                data_fim = dia_atual + timedelta(days=duracao_dias - 1)

                cronograma.append({
                    "Serviço": descricao,
                    "Profissional": nome_prof,
                    "Quantidade de Serviço": quantidade,
                    "Horas Necessárias": round(horas, 2),
                    "Data de Início": dia_atual.strftime("%d/%m/%Y"),
                    "Data de Término": data_fim.strftime("%d/%m/%Y")
                })

                dia_atual = data_fim + timedelta(days=1)
                if (dia_atual - data_inicio).days > prazo_dias:
                    st.warning("⚠️ O prazo informado foi excedido. Alguns serviços ultrapassam o prazo total.")
                    break

        if not cronograma:
            raise ValueError("⚠️ O cronograma está vazio. Verifique se os códigos ou descrições da planilha existem no banco SINAPI.")

        return pd.DataFrame(cronograma)

    except Exception as e:
        st.error(f"Erro ao processar a planilha:\n\n{e}")
        return None


# --- Interface do usuário ---
sinapi = carregar_banco_sinapi("banco_sinapi_profissionais_detalhado.csv")

arquivo_planilha = st.file_uploader("📎 Faça upload da planilha orçamentária", type=["xlsx"])

data_inicio = st.date_input("📆 Data de início da obra", value=datetime.today())
prazo_dias = st.number_input("⏱️ Prazo total de execução (em dias)", min_value=1, value=30)

if arquivo_planilha and sinapi is not None:
    st.success("✅ Planilha carregada com sucesso!")
    df_cronograma = gerar_cronograma(arquivo_planilha, sinapi, data_inicio, prazo_dias)
    if df_cronograma is not None:
        st.subheader("📊 Cronograma Gerado")
        st.dataframe(df_cronograma)

        csv = df_cronograma.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Baixar cronograma (.csv)", csv, "cronograma.csv", "text/csv")
