def gerar_cronograma(planilha, banco):
    try:
        df = pd.read_excel(planilha, engine="openpyxl")
        df.columns = df.columns.str.strip().str.upper()

        # Mapear possíveis variações de nomes de colunas
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
                horas = quantidade * coef * 8  # 8h/dia
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
