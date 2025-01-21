import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Configurações da página
st.set_page_config(
    page_title="Relatórios de Manutenção Solares ☀️⚒️",
    layout="wide"  # Usa layout wide para maximizar o espaço disponível
)

# Palavras-chave de classificação
classification_keywords = [
    'CORRETIVA', 'PREVENTIVA', 'CONTENÇÃO VEGETAL', 'LAVAGEM DE MÓDULOS', 'MATERIAIS'
]


def parse_message(text, enviado_por):
    data = []
    current_section = None
    current_subsection = None

    # Dividir o texto em linhas
    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # Identificar seção principal
        for keyword in classification_keywords:
            if keyword in line:
                current_section = keyword
                break

        # Identificar subseção
        if line.startswith('-'):
            current_subsection = line.replace('-', '').replace(':', '').strip()
            continue

        # Procurar por padrões de equipamento[descrição]
        if '[' in line and ']' in line:
            try:
                equipamento = line.split('[')[0].strip()
                descricao = line.split('[')[1].split(']')[0].strip()

                data.append({
                    'classificacao': current_section,
                    'tipo_equipamento': current_subsection,
                    'equipamento': equipamento,
                    'descricao': descricao,
                    'enviado_por': enviado_por
                })
            except:
                continue

    return data


# Cache para dados processados
@st.cache_data
def process_uploaded_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df['Data'] = pd.to_datetime(df['Data'])
    return df


def main():
    st.title('Relatórios de Manutenção Solares ☀️⚒️')

    # Adicionar um pouco de CSS para melhorar a aparência
    st.markdown("""
        <style>
        .stDataFrame {
            width: 100%;
        }
        .dataframe {
            font-size: 14px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Upload do arquivo
    uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=['xlsx'])

    if uploaded_file is not None:
        try:
            df = process_uploaded_file(uploaded_file)

            # Mostrar range de datas disponíveis
            min_date = df['Data'].min().date()
            max_date = df['Data'].max().date()

            # Seletor de intervalo de datas
            start_date, end_date = st.date_input(
                "Selecione o período para análise",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            # Filtrar dados pelo período selecionado (convertendo start_date e end_date para datetime)
            filtered_df = df[(df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)]

            if not filtered_df.empty:
                st.write(f"### Mensagens do período de {start_date} a {end_date}")

                # Lista para armazenar todos os dados processados
                all_data = []

                # Para cada mensagem do período
                for _, row in filtered_df.iterrows():
                    # Verificar se o texto é uma string antes de processar
                    if isinstance(row['Texto'], str):
                        # Processar o texto da mensagem
                        parsed_data = parse_message(
                            row['Texto'],
                            row['Enviado por']
                        )
                        all_data.extend(parsed_data)

                if all_data:
                    # Criar DataFrame com todos os dados processados
                    consolidated_df = pd.DataFrame(all_data)

                    # Reorganizar as colunas
                    column_order = [
                        'classificacao',
                        'tipo_equipamento',
                        'equipamento',
                        'descricao',
                        'enviado_por'
                    ]
                    consolidated_df = consolidated_df[column_order]

                    # Adicionar o campo de filtro por tipo de equipamento
                    tipos_equipamento = consolidated_df['tipo_equipamento'].unique()
                    selected_tipo_equipamento = st.sidebar.selectbox(
                        'Tipo de Equipamento',
                        ['Todos os Tipos'] + list(tipos_equipamento),
                        help="Selecione o tipo de equipamento para filtrar os resultados"
                    )

                    # Filtrar por tipo de equipamento
                    if selected_tipo_equipamento != 'Todos os Tipos':
                        consolidated_df = consolidated_df[
                            consolidated_df['tipo_equipamento'] == selected_tipo_equipamento]

                    # Adicionar o campo de filtro por equipamento
                    equipamentos = consolidated_df['equipamento'].unique()
                    selected_equipamento = st.sidebar.selectbox(
                        'Equipamento',
                        ['Todos os Equipamentos'] + list(equipamentos),
                        help="Selecione o equipamento para filtrar os resultados"
                    )

                    # Filtrar por equipamento
                    if selected_equipamento != 'Todos os Equipamentos':
                        consolidated_df = consolidated_df[consolidated_df['equipamento'] == selected_equipamento]

                    # Mostrar dados em diferentes tabs
                    tabs = st.tabs(
                        ['Todas as Atividades', 'Corretiva', 'Preventiva', 'Contenção Vegetal', 'Lavagem de Módulos',
                         'Materiais'])

                    with tabs[0]:
                        st.write("### Todas as Atividades")
                        st.dataframe(
                            consolidated_df,
                            hide_index=True,
                            use_container_width=True
                        )

                    for tab, classificacao in zip(tabs[1:],
                                                  ['CORRETIVA', 'PREVENTIVA', 'CONTENÇÃO VEGETAL', 'LAVAGEM DE MÓDULOS',
                                                   'MATERIAIS']):
                        with tab:
                            df_filtered = consolidated_df[consolidated_df['classificacao'] == classificacao]
                            if not df_filtered.empty:
                                st.dataframe(
                                    df_filtered,
                                    hide_index=True,
                                    use_container_width=True,
                                )
                            else:
                                st.write("Sem registros nesta classificação")

                    # Adicionar algumas estatísticas
                    st.write("### Estatísticas")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Total de Registros", len(consolidated_df))

                    with col2:
                        st.metric("Tipos de Equipamento",
                                  len(consolidated_df['tipo_equipamento'].unique()))

                    # Adicionar gráfico de distribuição por classificação
                    st.write("### Distribuição por Classificação")
                    classificacao_count = consolidated_df['classificacao'].value_counts()
                    st.bar_chart(classificacao_count)

                else:
                    st.write("Não foram encontrados dados para processar nas mensagens")
            else:
                st.write("Não há mensagens para o período selecionado")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")


if __name__ == "__main__":
    main()