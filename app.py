import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Planejador de Obra", layout="wide")
st.title("📅 Planejador de Obra com Banco SINAPI")

# Carrega banco SINAPI (csv separado por vírgula, UTF-8)
def carregar_banco_sinapi(caminho_csv):
    try:
        banco = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
        # Normaliza nomes de colunas para facilitar busca
        banco.columns = [col.strip().upper() for col in banco.columns]
        return banco
    except Exception as e:
        st.error(f"Erro ao carregar banco SINAPI: {e}")
        return None

# Função para detectar blocos do tipo "5.1.1", "5.1.2" na primeira coluna
def ler_planilha_com_blocos(planilha):
    df = pd.read_excel(planilha, engine='openpyxl', skiprows=4)
    df.columns = [col.strip() for col in df.columns]

    blocos = []
    bloco_atual = None

    for idx, linha in df.iterrows():
        primeira_col = str(linha[0]).strip()
        descricao = str(linha.get('Descrição', '')).strip() if 'Descrição' in df.columns else ''

        if primeira_col and primeira_col[0].isdigit() and (descricao == '' or len(descricao) < 20):
            # Novo bloco encontrado
            bloco_atual = {
                'titulo': primeira_col,
                'linhas': []
            }
            blocos.append(bloco_atual)
        else:
            # Ignora linhas vazias totalmente
            if linha.isnull().all():
                continue
            if bloco_atual:
                bloco_atual['linhas'].append(linha)

    return blocos

# Identifica tipo da linha (Composição, Composição Auxiliar, Insumo)
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
        # Caso não detecte, tenta pela coluna 'Banco' (ex: 'SINAPI')
        banco = str(linha.get('Banco', '')).strip().upper()
        if banco == 'SINAPI':
            return "Item SINAPI"
        return "Outro"

# Função para buscar composição no banco SINAPI pelo código ou descrição
def buscar_composicao(codigo, descricao, banco):
    codigo_str = str(codigo).strip()
    # Tenta buscar por código
    comp = banco[banco['CODIGO DA COMPOSICAO'].astype(str).str.strip() == codigo_str]
    if not comp.empty:
        return comp
    # Se não achou, tenta por descrição aproximada
    desc_normalizada = descricao.lower().strip()
    candidatos = banco[banco['DESCRICAO DA COMPOSICAO'].str.lower().str.contains(desc_normalizada[:10], na=False)]
    return candidatos

# Gera cronograma baseado nas composições e banco SINAPI
def gerar_cronograma(blocos, banco, data_inicio, prazo_dias):
    cronograma = []
    dia_atual = data_inicio

    for bloco in blocos:
        st.write(f"### Bloco {bloco['titulo']} - {len(bloco['linhas'])} linhas")
        for linha in bloco['linhas']:
            tipo = tipo_linha(linha)
            if tipo != "Composição":
                continue

            codigo = str(linha[1]).strip() if len(linha) > 1 else ""
            descricao = str(linha.get('Descrição', '')).strip()
            try:
                quantidade = float(str(linha.get('Quant.', linha.get('Quant', '0'))).replace(',', '.'))
            except:
                quantidade = 0

            if quantidade == 0:
                continue

            comp = buscar_composicao(codigo, descricao, banco)
            if comp.empty:
                st.warning(f"⚠️ Composição não encontrada no banco para código '{codigo}' ou descrição '{descricao}'")
                continue

            profissionais = comp[comp['TIPO ITEM'].str.lower() == 'mão de obra']
            if profissionais.empty:
                st.warning(f"⚠️ Nenhum item de mão de obra encontrado para '{descricao}'")
                continue

            for _, prof in profissionais.iterrows():
                nome_prof = prof['DESCRIÇÃO ITEM']
                try:
                    coef = float(str(prof['COEFICIENTE']).replace(',', '.'))
                except:
                    coef = 0

                if coef == 0:
                    continue

                horas = quantidade * coef * 8
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

    return pd.DataFrame(cronograma)

# --- Interface ---
sinapi = carregar_banco_sinapi("banco_sinapi_profissionais_detalhado.csv")

arquivo_planilha = st.file_uploader("📎 Faça upload da planilha orçamentária", type=["xlsx"])
data_inicio = st.date_input("📆 Data de início da obra", value=datetime.today())
prazo_dias = st.number_input("⏱️ Prazo total de execução (em dias)", min_value=1, value=30)

if arquivo_planilha and sinapi is not None:
    st.success("✅ Planilha carregada!")
    blocos = ler_planilha_com_blocos(arquivo_planilha)
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
