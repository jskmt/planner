import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import difflib
import re

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📅 Planejador de Obra com Banco SINAPI")

def carregar_banco_sinapi(caminho_csv):
    try:
        banco = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
        banco.columns = [col.strip().upper() for col in banco.columns]
        return banco
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

def ler_planilha_com_blocos(planilha):
    df = pd.read_excel(planilha, engine='openpyxl', skiprows=4)
    df.columns = [col.strip() for col in df.columns]

    blocos = []
    bloco_atual = None

    for idx, linha in df.iterrows():
        primeira_col = str(linha[0]).strip()
        descricao = str(linha.get('Descrição', '')).strip() if 'Descrição' in df.columns else ''

        if primeira_col and primeira_col[0].isdigit() and (descricao == '' or len(descricao) < 20):
            bloco_atual = {
                'titulo': primeira_col,
                'linhas': []
            }
            blocos.append(bloco_atual)
        else:
            if linha.isnull().all():
                continue
            if bloco_atual:
                bloco_atual['linhas'].append(linha)

    return blocos

def tipo_linha(linha):
    primeira_col = str(linha[0]).strip()
    descricao = str(linha.get('Descrição', '')).strip().lower()

    if "composição" in primeira_col.lower() or "composição" in descricao:
        return "Composição"
    elif "auxiliar" in primeira_col.lower() or "auxiliar" in descricao:
        return "Composição Auxiliar"
    elif "insumo" in primeira_col.lower() or "insumo" in descricao:
        return "Insumo"
    else:
        banco = str(linha.get('Banco', '')).strip().upper()
        if banco == 'SINAPI':
            return "Item SINAPI"
        return "Outro"

def limpar(texto):
    if not texto:
        return ''
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\b(af|coral|suvinil|premium|equino[a-z]*)\b', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def buscar_composicao(codigo, descricao, banco):
    codigo_str = str(codigo).strip()
    descricao_limpa = limpar(descricao)

    # 1. Busca por código exato
    comp = banco[banco['CODIGO DA COMPOSICAO'].astype(str).str.strip() == codigo_str]
    if not comp.empty:
        return comp

    # 2. Busca por código parcial
    codigo_base = re.sub(r'[^\d]', '', codigo_str)
    if codigo_base:
        comp = banco[banco['CODIGO DA COMPOSICAO'].astype(str).str.contains(codigo_base)]
        if not comp.empty:
            return comp

    # 3. Busca por descrição limpa (similaridade)
    banco['DESC_LIMPA'] = banco['DESCRICAO DA COMPOSICAO'].fillna('').apply(limpar)
    descricoes_banco = banco['DESC_LIMPA'].tolist()
    match = difflib.get_close_matches(descricao_limpa, descricoes_banco, n=1, cutoff=0.4)

    if match:
        comp = banco[banco['DESC_LIMPA'] == match[0]]
        return comp

    return pd.DataFrame()

def gerar_cronograma(blocos, banco, data_inicio, prazo_dias):
    cronograma = []
    dia_atual = data_inicio

    for bloco in blocos:
        st.write(f"### DEBUG: Bloco {bloco['titulo']} - {len(bloco['linhas'])} linhas")

        linhas = bloco['linhas']
        i = 0

        while i < len(linhas):
            linha = linhas[i]
            st.write(f"🔎 Linha {i}: {linha.to_dict()}")
            tipo = tipo_linha(linha)
            st.write(f"➡️ Tipo identificado: {tipo}")

            if tipo != "Composição":
                i += 1
                continue

            codigo = str(linha[1]).strip() if len(linha) > 1 else ""
            descricao = str(linha.get('Descrição', '')).strip()
            try:
                quantidade = float(str(linha.get('Quant.', linha.get('Quant', '0'))).replace(',', '.'))
            except:
                quantidade = 0

            st.write(f"📦 Código: {codigo}, Descrição: {descricao}, Quantidade: {quantidade}")

            if quantidade == 0:
                st.warning(f"⚠️ Quantidade zero na linha: {descricao}")
                i += 1
                continue

            # Aqui você pode continuar com a lógica original (auxiliares e banco)
            # Mas por enquanto vamos testar se ele chega até aqui

            i += 1  # Avança o loop

    return pd.DataFrame(cronograma)


# Interface
sinapi = carregar_banco_sinapi("banco_sinapi_profissionais_detalhado.csv")

arquivo_planilha = st.file_uploader("📎 Faça upload da planilha orçamentária", type=["xlsx"])
data_inicio = st.date_input("📆 Data de início da obra", value=datetime.today())
prazo_dias = st.number_input("⏱️ Prazo total de execução (em dias)", min_value=1, value=30)

if arquivo_planilha:
    df_teste = pd.read_excel(arquivo_planilha, engine='openpyxl', skiprows=4)
    st.write("Colunas da planilha:", df_teste.columns.tolist())

    if sinapi is not None:
        if st.button("▶️ Gerar cronograma"):
            blocos = ler_planilha_com_blocos(arquivo_planilha)
            st.write(f"Quantidade de blocos encontrados: {len(blocos)}")
            for b in blocos:
                st.write(f"Bloco {b['titulo']} com {len(b['linhas'])} linhas")

            if not blocos:
                st.error("Não foi possível detectar blocos na planilha.")
            else:
                df_cronograma = gerar_cronograma(blocos, sinapi, data_inicio, prazo_dias)
                if df_cronograma is not None and not df_cronograma.empty:
                    st.subheader("📊 Cronograma Gerado")
                    st.dataframe(df_cronograma)
                    csv = df_cronograma.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Baixar cronograma (.csv)", csv, "cronograma.csv", "text/csv")
                else:
                    st.warning("⚠️ O cronograma está vazio. Verifique os dados da planilha e banco SINAPI.")
    else:
        st.error("Banco SINAPI não carregado.")
