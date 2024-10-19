import streamlit as st
import webbrowser
import pandas as pd
from datetime import datetime 
import plotly.express as px

st.set_page_config(
        page_title="Home",
        page_icon="chart_with_upwards_trend",
        layout="wide",
    )

# Verificar e carregar o DataFrame na sessão do Streamlit
if "data" not in st.session_state:
    df_data = pd.read_csv("datasets/CLEAN_FIFA23_official_data.csv", index_col=0)
    df_data = df_data[df_data["Contract Valid Until"] >= datetime.today().year]
    df_data = df_data[df_data["Value(£)"] > 0]
    df_data = df_data.sort_values(by="Overall", ascending=False)
    st.session_state["data"] = df_data
else:
    df_data = st.session_state["data"]  # Carregar da sessão

# Criar a lista de posições com a opção 'All' no início
posicoes = ['All'] + df_data["Position"].value_counts().index.tolist()

# Criar o filtro de posição na barra lateral
posicao = st.sidebar.selectbox("Position", posicoes)

# Obter as nacionalidades em ordem crescente
nacionalidades = sorted(df_data["Nationality"].value_counts(ascending=False).index.tolist())
# Criar a lista de nacionalidade com a opção 'All' no início
nacionalidades = ['All'] + nacionalidades

# Criar o filtro de nacionalidade na barra lateral
nacionalidade = st.sidebar.selectbox("Nationality", nacionalidades)

# Obter as idades em ordem crescente
idades = sorted(df_data["Age"].value_counts(ascending=False).index.tolist())
# Criar a lista de idades com a opção 'All' no início
idades = ['All'] + idades
# Criar o filtro de idade na barra lateral
idade = st.sidebar.selectbox("Age", idades)

# Aplicar os filtros de posição, nacionalidade e idade
df_filtrada = df_data.copy()

if posicao != 'All':
    df_filtrada = df_filtrada[df_filtrada["Position"] == posicao]

if nacionalidade != 'All':
    df_filtrada = df_filtrada[df_filtrada["Nationality"] == nacionalidade]

if idade != 'All':
    df_filtrada = df_filtrada[df_filtrada["Age"] == idade]

# Verificar se a filtragem retornou algum dado
if df_filtrada.empty:
    st.warning("Nenhum dado encontrado com os filtros aplicados.")
else:
    # Título da aplicação
    st.markdown("# FIFA23 OFFICIAL DATASET! ⚽️")
    st.sidebar.markdown("Desenvolvido por [Matheus Medeiros](https://www.linkedin.com/in/matheusramosmedeiros/)")

    # Botão para abrir Kaggle
    btn = st.button("Acesse os dados no Kaggle")
    if btn:
        webbrowser.open_new_tab("https://www.kaggle.com/datasets/kevwesophia/fifa23-official-datasetclean-data")

    # Descrição do dataset
    st.markdown(
        """
        O conjunto de dados contém uma ampla gama de atributos, incluindo dados demográficos 
        do jogador, características físicas, estatísticas de jogo, detalhes do contrato e 
        afiliações de clubes. 
        """
    )
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["Resumo","Análise por Posição", "Potencial de Evolução"])

    with tab1:
        # Métricas
        paises = df_filtrada['Nationality'].nunique()
        jogadores = df_filtrada['ID'].nunique()

        col1, col2 = st.columns(2)
        col1.metric(label="Quantidades de Países", value=paises)
        col2.metric(label="Quantidades de Jogadores", value=jogadores)

    

        # Criar gráfico de dispersão
        fig = px.scatter(
            df_filtrada.head(100), 
            x='Value(£)', 
            y='Overall',
            hover_name='Name', 
            title="Relação entre Valor de Mercado e Pontuação Geral dos Jogadores",
            labels={"Value(£)": "Valor de Mercado (£)", "Overall": "Pontuação Geral" , 'Club': 'Clube'},
            hover_data={'Value(£)': ':.2f'}  # Formatando o valor em hover
        )

        # Customizar o layout
        fig.update_traces(marker=dict(size=12, color='royalblue', line=dict(width=2, color='DarkSlateGrey')),
                        selector=dict(mode='markers'))

        fig.update_layout(
            xaxis_title="Valor de Mercado (£)",
            yaxis_title="Overall",
            showlegend=False
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig)

        st.divider()

        variavel_selecionada = st.selectbox(
            "Selecione a variável para o Top - 10 : ",
            options=["Value(£)", "Potential", "Overall"]
        )
        st.markdown(f"### Top 10 - {variavel_selecionada}")

        top10 = df_filtrada.sort_values(variavel_selecionada, ascending= False).head(10)
        colunas = ['Photo','Name','Age','Flag' ,'Nationality' ,
                    'Club','Overall', 'Value(£)',
                    'Wage(£)']
        top10 = top10[colunas]
        st.dataframe(top10, column_config={
                 "Overall": st.column_config.ProgressColumn(
                     "Overall", format="%d", min_value=0, max_value=100
                 ),
                "Photo": st.column_config.ImageColumn(),
                "Flag": st.column_config.ImageColumn("Country")
             })

    
    with tab2:
        # Título da seção
        st.markdown("## Análise por Posição")
            # Definir agrupamento de posições específicas
        grupos_posicoes = {
            "Goleiros": ["GK"],
            "Zagueiros": ["CB", "LCB", "RCB"],
            "Meio-campistas": ["CM", "CDM", "CAM", "LM", "RM", "LDM", "RDM"],
            "Atacantes": ["ST", "CF", "RW", "LW", "RS", "LS", "RF", "LF"]
        }

        # Criar DataFrame com as posições principais
        df_posicoes = pd.DataFrame(columns=[
            "Posição", "Quantidade de Jogadores", "Overall Médio", 
            "Potencial Médio", "Valor Médio (£)", "Salário Médio (£)", 
            "Desvio Padrão dos Salários (£)", "Quantidade de Outliers de Salário"
        ])

        # Função para calcular a quantidade de outliers
        def calcular_outliers(salarios):
            q1 = salarios.quantile(0.25)
            q3 = salarios.quantile(0.75)
            iqr = q3 - q1
            limite_inferior = q1 - 1.5 * iqr
            limite_superior = q3 + 1.5 * iqr
            outliers = salarios[(salarios < limite_inferior) | (salarios > limite_superior)]
            return len(outliers)

        for grupo, posicoes in grupos_posicoes.items():
            df_grupo = df_filtrada[df_filtrada["Position"].isin(posicoes)]
            if not df_grupo.empty:
                quantidade_jogadores = df_grupo.shape[0]
                overall_medio = df_grupo["Overall"].mean()
                potencial_medio = df_grupo["Potential"].mean()
                valor_medio = df_grupo["Value(£)"].mean()
                salario_medio = df_grupo["Wage(£)"].mean()
                desvio_padrao_salario = df_grupo["Wage(£)"].std()
                quantidade_outliers = calcular_outliers(df_grupo["Wage(£)"])
                
                nova_linha = pd.DataFrame({
                    "Posição": [grupo],
                    "Quantidade de Jogadores": [quantidade_jogadores],
                    "Overall Médio": [round(overall_medio, 2)],
                    "Potencial Médio": [round(potencial_medio, 2)],
                    "Valor Médio (£)": [round(valor_medio, 2)],
                    "Salário Médio (£)": [round(salario_medio, 2)],
                    "Desvio Padrão dos Salários (£)": [round(desvio_padrao_salario, 2)],
                    "Quantidade de Outliers de Salário": [quantidade_outliers]
                })
                df_posicoes = pd.concat([df_posicoes, nova_linha], ignore_index=True)

        # Exibir a tabela com as médias por posição e contagem de outliers
        st.dataframe(df_posicoes)

        # Adicionar uma nova coluna ao DataFrame filtrado com o grupo de posição
        df_filtrada["Grupo de Posição"] = df_filtrada["Position"].map({
            "GK": "Goleiros",
            "CB": "Zagueiros", "LCB": "Zagueiros", "RCB": "Zagueiros",
            "CM": "Meio-campistas", "CDM": "Meio-campistas", "CAM": "Meio-campistas",
            "LM": "Meio-campistas", "RM": "Meio-campistas", "LDM": "Meio-campistas", "RDM": "Meio-campistas",
            "ST": "Atacantes", "CF": "Atacantes", "RW": "Atacantes", "LW": "Atacantes",
            "RS": "Atacantes", "LS": "Atacantes", "RF": "Atacantes", "LF": "Atacantes"
        })

        # Filtrar para posições que estão nos grupos definidos
        df_salarios_posicoes = df_filtrada[df_filtrada["Grupo de Posição"].notnull()]

        # Criação de um menu para selecionar a variável que o usuário deseja visualizar
        variavel_selecionada = st.selectbox(
            "Selecione a variável para o boxplot",
            options=["Salário", "Potencial", "Overall"]
        )

        # Mapeamento das seleções para as colunas correspondentes no DataFrame
        if variavel_selecionada == "Salário":
            coluna_y = "Wage(£)"
            titulo = "Distribuição de Salários por Posição Agrupada"
            label_y = "Salário (£)"
        elif variavel_selecionada == "Potencial":
            coluna_y = "Potential"
            titulo = "Distribuição de Potencial por Posição Agrupada"
            label_y = "Potencial"
        else:
            coluna_y = "Overall"
            titulo = "Distribuição de Overall por Posição Agrupada"
            label_y = "Overall"

        # Criar o gráfico de boxplot com as posições agrupadas
        fig = px.box(
            df_salarios_posicoes, 
            x="Grupo de Posição", 
            y=coluna_y, 
            title=titulo, 
            labels={coluna_y: label_y, "Grupo de Posição": "Grupo de Posição"},
            color="Grupo de Posição",
            hover_data=["Name"]  # Adiciona o nome dos jogadores ao passar o mouse
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig)


    with tab3 : 

    
        # -- Análise do Potencial de Evolução --

        # Calcular a diferença entre o Potencial e o Overall
        df_filtrada["Diff Potencial"] = df_filtrada["Potential"] - df_filtrada["Overall"]

        # Filtrar jogadores com espaço para evoluir (com potencial maior que o overall)
        jogadores_promessas = df_filtrada[df_filtrada["Diff Potencial"] > 0].sort_values(by="Diff Potencial", ascending=False)

        # Filtrar jogadores que já atingiram o máximo do potencial
        jogadores_atingiram_potencial = df_filtrada[df_filtrada["Diff Potencial"] == 0]

        # Filtrar jogadores promessas com até 20 anos
        promessas_ate_20 = jogadores_promessas[jogadores_promessas["Age"] < 20]
        promessas_ate_20 = promessas_ate_20.sort_values('Potential' ,  ascending= False)

        # Filtrar jogadores promessas com até 23 anos
        promessas_ate_23 = jogadores_promessas[(jogadores_promessas["Age"] >= 20) & (jogadores_promessas["Age"] <= 23)]
        promessas_ate_23 = promessas_ate_23.sort_values('Potential' ,  ascending= False)

        promessas_total = promessas_ate_20 + promessas_ate_23
        # Métricas sobre promessas e jogadores que atingiram o potencial
        st.markdown("## Potencial de Evolução")
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total de Promessas (ainda em desenvolvimento)", value=jogadores_promessas.shape[0])
        col2.metric(label="Jogadores com Potencial Máximo Atingido", value=jogadores_atingiram_potencial.shape[0])
        col3.metric(label="Jovens Promessas (até 23 anos)", value=promessas_total.shape[0])

        # Exibir tabelas lado a lado
        st.markdown("#### Comparação das Promessas por Idade")
        col1, col2 = st.columns(2)

        # Tabela de promessas até 20 anos
        with col1:
            st.markdown("###### Promessas até 20 anos")
            st.dataframe(promessas_ate_20[['Photo',"Name", "Age", "Overall", "Potential", "Diff Potencial", "Club"]].head(10),
                          column_config={
                    "Photo": st.column_config.ImageColumn()
                })

        # Tabela de promessas até 23 anos
        with col2:
            st.markdown("###### Promessas até 23 anos")
            st.dataframe(promessas_ate_23[['Photo', "Name", "Age", "Overall", "Potential", "Diff Potencial", "Club"]].head(10),
                column_config={
                    "Photo": st.column_config.ImageColumn()
                })
            
        # Comparação visual entre Promessas e Jogadores com Potencial Máximo Atingido
        st.markdown("#### Visualização Comparativa")
        col1, col2 = st.columns(2)

        if jogadores_promessas.empty:
            col1.warning("Nenhuma promessa encontrada.")
        else:
            fig_promessas = px.scatter(
                jogadores_promessas, 
                x="Age", 
                y="Diff Potencial", 
                hover_name="Name", 
                title="Promessas - Jogadores com Maior Potencial de Evolução",
                labels={"Age": "Idade", "Diff Potencial": "Diferença Potencial vs Overall"}
            )
            col1.plotly_chart(fig_promessas, use_container_width=True)

        if jogadores_atingiram_potencial.empty:
            col2.warning("Nenhum jogador atingiu o potencial máximo.")
        else:
            fig_potencial_max = px.scatter(
                jogadores_atingiram_potencial, 
                x="Age", 
                y="Overall", 
                hover_name="Name", 
                title="Jogadores com Potencial Máximo Atingido",
                labels={"Age": "Idade", "Overall": "Overall"}
            )
            col2.plotly_chart(fig_potencial_max, use_container_width=True)
        
        
        # Exibir tabela de custo-benefício
        st.markdown("#### Top 20 Jogadores com Melhor Custo-Benefício (Overall > 80)")
        col1, col2 = st.columns(2)

        # Adicionando a coluna de custo-benefício inverso na base filtrada
        df_filtrada["Custo_Beneficio_Inverso"] = df_filtrada["Overall"] / df_filtrada["Value(£)"]

        # Filtrar apenas jogadores com overall acima de 80
        df_custo_beneficio = df_filtrada[df_filtrada["Overall"] > 80]

        # Verificar se há jogadores suficientes após o filtro de overall
        if df_custo_beneficio.empty:
            st.warning("Nenhum jogador com Overall > 80 encontrado com os filtros aplicados.")
        else:
            # Ordenar pelo melhor custo-benefício e mostrar os top 10
            top_jogadores_custo_beneficio = df_custo_beneficio.sort_values(by="Custo_Beneficio_Inverso", ascending=False).head(20)
            col1.dataframe(top_jogadores_custo_beneficio[['Photo',"Name", "Overall", "Potential", "Value(£)"]],
                            column_config={
                    "Photo": st.column_config.ImageColumn()
                })

            # Criar gráfico de dispersão de custo-benefício
            fig = px.scatter(
                top_jogadores_custo_beneficio, 
                x='Value(£)', 
                y='Overall',
                size='Custo_Beneficio_Inverso', 
                hover_name='Name',
                title="Relação entre Valor de Mercado e Pontuação Geral (Melhor Custo-Benefício)",
                labels={"Value(£)": "Valor de Mercado (£)", "Overall": "Pontuação Geral", "Custo_Beneficio_Inverso": "Custo-Benefício Inverso"}
            )

            # Customizar o layout do gráfico
            fig.update_traces(marker=dict(size=12, color='royalblue', line=dict(width=2, color='DarkSlateGrey')),
                            selector=dict(mode='markers'))

            fig.update_layout(
                xaxis_title="Valor de Mercado (£)",
                yaxis_title="Overall",
                showlegend=False
            )

            # Exibir o gráfico no Streamlit
            col2.plotly_chart(fig)

    
    

    