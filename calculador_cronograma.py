import pandas as pd

def calcular_cronograma(df_orcamento, df_sinapi, data_inicio_str, prazo_total_dias):
    # Converter string de data para objeto datetime
    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y")

    # Lista para armazenar os resultados
    cronograma = []

    for _, item in df_orcamento.iterrows():
        codigo = item['codigo_composicao']
        descricao = item['descricao_servico']
        quantidade = item['quantidade']

        # Filtra os dados do SINAPI para a composição atual
        composicao = df_sinapi[df_sinapi['CODIGO_COMPOSICAO'] == codigo]

        # Filtra apenas mão de obra
        profissionais = composicao[composicao['TIPO_ITEM'] == 'MÃO DE OBRA']

        if profissionais.empty:
            continue  # pula se não tiver profissionais definidos

        duracao_total_dias = 0
        detalhes_profissionais = []

        for _, row in profissionais.iterrows():
            descricao_prof = row['DESCRICAO_ITEM']
            coeficiente = row['COEFICIENTE']
            horas_totais = coeficiente * quantidade  # total de horas para essa quantidade
            dias_totais = horas_totais / 8  # considerando jornada de 8h/dia
            detalhes_profissionais.append({
                "profissional": descricao_prof,
                "horas_totais": horas_totais,
                "dias_totais": dias_totais
            })
            duracao_total_dias = max(duracao_total_dias, dias_totais)

        data_fim = data_inicio + timedelta(days=round(duracao_total_dias))

        cronograma.append({
            "codigo_composicao": codigo,
            "descricao_servico": descricao,
            "data_inicio": data_inicio.strftime("%d/%m/%Y"),
            "duracao_dias": round(duracao_total_dias),
            "data_fim": data_fim.strftime("%d/%m/%Y"),
            "profissionais": detalhes_profissionais
        })

        # Avança a data de início para a próxima tarefa sequencialmente
        data_inicio = data_fim

    return pd.DataFrame(cronograma)
