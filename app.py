import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import difflib

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
    texto = re.sub(r'[^a-z0-9\s]', '', texto)  # remove pontuação
    texto = re.sub(r'\b(af|coral|suvinil|premium|equino[a-z]*)\b', '', texto)  # remove marcas/sufixos
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
        linhas = bloco['linhas']
        i = 0

        while i < len(linhas):
            linha = linhas[i]
            tipo = tipo_linha(linha)

            if tipo != "Composição":
                i += 1
                continue

            codigo = str(linha[1]).strip() if len(linha) > 1 else ""
            descricao = str(linha.get('Descrição', '')).strip()
            try:
                quantidade = float(str(linha.get('Quant.', linha.get('Quant', '0'))).replace(',', '.'))
            except:
                quantidade = 0

            if quantidade == 0:
                i += 1
                continue

            profissionais = []
            j = i + 1

            # Verifica se há auxiliares nas próximas linhas
            while j < len(linhas):
                linha_aux = linhas[j]
                tipo_aux = tipo_linha(linha_aux)
                if tipo_aux != "Composição Auxiliar":
                    break

                desc_aux = str(linha_aux.get('Descrição', '')).strip()
                if any(palavra in desc_aux.lower() for palavra in ["servente", "gesseiro", "pedreiro", "azulejista", "encargos"]):
                    try:
                        q_aux = float(str(linha_aux.get('Quant.', linha_aux.get('Quant', '0'))).replace(',', '.'))
                        nome_aux = desc_aux
                        profissionais.append((nome_aux, q_aux))
                    except:
                        pass

                j += 1

            # Se não houver auxiliares listados na planilha, busca no banco
            if not profissionais:
                comp_banco = buscar_composicao(codigo, descricao, banco)
                if not comp_banco.empty:
                    mao_obra = comp_banco[comp_banco['TIPO ITEM'].str.lower() == 'mão de obra']
                    for _, prof in mao_obra.iterrows():
                        try:
                            coef = float(str(prof['COEFICIENTE']).replace(',', '.'))
                            nome_prof = str(prof['DESCRIÇÃO ITEM']).strip()
                            profissionais.append((nome_prof, coef * quantidade))
                        except Exception as e:
                            st.warning(f"Erro ao processar profissional em '{descricao}': {e}")
                else:
                    st.warning(f"⚠️ Nenhuma composição auxiliar ou item de mão de obra encontrado para '{descricao}'")

            # Gera linha do cronograma para cada profissional
            for nome_prof, qtd_horas in profissionais:
                horas = qtd_horas * 8  # quantidade está em H
                duracao_dias = max(1, round(horas / 8))
                data_fim = dia_atual + timedelta(days=duracao_dias - 1)

                cronograma.append({
                    "Bloco": bloco['titulo'],
                    "Serviço": descricao,
                    "Profissional": nome_prof,
                    "Quantidade de Serviço": quantidade,
                    "Horas Necessárias": round(horas, 2),
                    "Data de Início": dia_atual.strftime("%d/%m/%Y"),
                    "Data de Término": data_fim.strftime("%d/%m/%Y")
                })

                dia_atual = data_fim + timedelta(days=1)
                if (dia_atual - data_inicio).days > prazo_dias:
                    st.warning("⚠️ O prazo informado foi excedido.")
                    return pd.DataFrame(cronograma)

            i = j  # pula para depois dos auxiliares

    return pd.DataFrame(cronograma)


# Interface
sinapi = carregar_banco_sinapi("banco_sinapi_profissionais_detalhado.csv")

arquivo_planilha = st.file_uploader("📎 Faça upload da planilha orçamentária", type=["xlsx"])
data_inicio = st.date_input("📆 Data de início da obra", value=datetime.today())
prazo_dias = st.number_input("⏱️ Prazo total de execução (em dias)", min_value=1, value=30)

if arquivo_planilha and sinapi is not None:
    blocos = ler_planilha_com_blocos(arquivo_planilha)

    if not blocos:
        st.error("Não foi possível detectar blocos na planilha.")
    else:
        if st.button("▶️ Gerar Cronograma"):
            with st.spinner("Gerando cronograma..."):
                df_cronograma = gerar_cronograma(blocos, sinapi, data_inicio, prazo_dias)
                if df_cronograma is not None and not df_cronograma.empty:
                    st.subheader("📊 Cronograma Gerado")
                    st.dataframe(df_cronograma)
                    csv = df_cronograma.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Baixar cronograma (.csv)", csv, "cronograma.csv", "text/csv")
                else:
                    st.warning("⚠️ O cronograma está vazio. Verifique os dados da planilha e banco SINAPI.")
