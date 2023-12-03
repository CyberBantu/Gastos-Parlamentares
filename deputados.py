import streamlit as st
import requests
import pandas as pd


# Função para pegar dados

url = "https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura=57&ordem=ASC&ordenarPor=nome"
resp = requests.get(url).json()
dados = pd.json_normalize(resp['dados'])

# Ajustando tamanho da pagina
st.set_page_config(layout="wide")


st.title("Painel de Gastos de Deputados do Brasil (2023)")

# Criando um selecionados
nomes_unicos = dados["nome"].unique()

# Criando seletor
deputy_name = st.selectbox("Selecione o nome de um deputado", nomes_unicos)

# Filtrando a base de dados
tabela_deputado = dados[dados["nome"] == deputy_name]

url_foto = tabela_deputado['urlFoto'].iloc[0]

# Verificando se há dados
if not tabela_deputado.empty:
    id_deputado = tabela_deputado['id'].iloc[0]

    # Configurando os dados
    url_gastos = f'https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas?ordem=ASC&ordenarPor=ano'
    resp_gastos = requests.get(url_gastos).json()



    # Verificando se há dados de gastos
    if 'dados' in resp_gastos and resp_gastos['dados']:
        dados_gastos = pd.json_normalize(resp_gastos['dados'])
        
        # Colocando os dados em DateTime
        dados_gastos['dataDocumento'] = pd.to_datetime(dados_gastos['dataDocumento']).dt.strftime('%d/%m/%Y')

        # Colocando na ordem correta
        dados_gastos = dados_gastos.sort_values(by='dataDocumento', ascending=True)


        # Filtrando a tabela que aparce
        dados_gastos = dados_gastos[['dataDocumento', 'tipoDespesa', 'tipoDocumento','nomeFornecedor', 'valorDocumento', 'valorLiquido']]
        
        dados_gastos['valorDocumento'] = dados_gastos['valorDocumento'].apply(lambda x: f'R$ {x:.2f}')
        dados_gastos['valorLiquido'] = dados_gastos['valorLiquido'].apply(lambda x: f'R$ {x:.2f}')
        
        # Renomeando as colunas
        dados_gastos = dados_gastos.rename(columns={
            'dataDocumento': 'Data do Documento',
            'tipoDespesa': 'Tipo de Despesa',
            'tipoDocumento': 'Tipo de Documento',
            'nomeFornecedor': 'Nome do Fornecedor',
            'valorDocumento': 'Valor do Documento',
            'valorLiquido': 'Valor Líquido'
        })

        # Criando a sidebar
        st.subheader(f"Informações de {deputy_name}")
        st.text(f"Partido: {dados['siglaPartido'].iloc[0]}")
        st.text(f"Partido: {dados['siglaUf'].iloc[0]}")
        st.text(f"UF: {dados['email'].iloc[0]}")
        st.image(url_foto, width=150)

        # Adicionando um card com a soma do valorLiquido
        total_valor_liquido = dados_gastos['Valor Líquido'].str.replace('R$', '').str.replace(',', '').astype(float).sum()
        st.info(f"Total Valor Líquido: R$ {total_valor_liquido:.2f}")

        # Adicionando um card com a soma do valorLiquido por Tipo de Despesa
        sum_by_tipo_despesa = dados_gastos.groupby('Tipo de Despesa')['Valor Líquido'].apply(lambda x: x.str.replace('R$', '').str.replace(',', '').astype(float).sum())
        st.info("Total Valor Líquido por Tipo de Despesa:")
        for tipo_despesa, total_valor in sum_by_tipo_despesa.items():
            st.info(f"{tipo_despesa}: R$ {total_valor:.2f}")

        st.table(dados_gastos)  # Exibe apenas os primeiros 10 registros, ajuste conforme necessário
    else:
        st.warning(f"Não há dados de gastos para o deputado {deputy_name}")
else:
    st.warning(f"Não há informações para o deputado {deputy_name}")

st.title('Painel de Agregação de Gastos')
st.text('Informações Agregadas por Partidos')

# Base de 02 de dezembro 2023 ------------------------------------
# Baixando a base 
base_0212 = pd.read_excel('base_gasto_parlamentar_0212.xlsx')


# juntando com dados

base_principal_0212 = base_0212.merge(dados, how='left', left_on='IdDeputado',right_on = 'id')

# calculo de gasto por partido
# Gasto por Partido
gasto_partido = base_principal_0212.groupby('siglaPartido')['valorLiquido'].agg(['sum', 'mean']).reset_index().sort_values(by='sum', ascending=True)

gasto_estado = base_principal_0212.groupby('siglaUf')['valorLiquido'].agg(['sum', 'mean']).reset_index().sort_values(by='sum', ascending=True)


# Fazendo a agregação
gasto_partido = (
    base_principal_0212.groupby('siglaPartido')['valorLiquido']
    .agg(['sum', 'mean'])
    .reset_index()
    .sort_values(by='sum', ascending=False)
)

# Renomear as colunas
gasto_partido.columns = ['siglaPartido', 'Total', 'Média']

# Formatação em reais
def em_reais(valor):
    return f'R$ {valor:.2f}'

# Fazendo a contagem de partios
count_partido = dados['siglaPartido'].value_counts()

base_consolidada = pd.merge(gasto_partido, count_partido, left_on='siglaPartido', right_index=True).rename(columns ={'count' : 'Total de Parlamentares'})

# Ultimas alterações
base_consolidada['Média de Gastos por Partido'] = base_consolidada['Total'] / base_consolidada['Total de Parlamentares']


base_consolidada['Total'] = base_consolidada['Total'].apply(em_reais)
base_consolidada['Média'] = base_consolidada['Média'].apply(em_reais)
base_consolidada['Média de Gastos por Partido'] = base_consolidada['Média de Gastos por Partido'].apply(em_reais)

st.table(base_consolidada)

st.text('Gasto Médio de Despesa de uso Parlamentar por Partido em 2023')
iframe_grafico_partido_media = "https://datawrapper.dwcdn.net/9nkSc/3/"
st.components.v1.iframe(iframe_grafico_partido_media, width=1366, height=700)

st.text('Média de Gastos de parlamentares por total de integrantes do Partido')
iframe_media_por_total_partido = 'https://datawrapper.dwcdn.net/jn81k/1/'
st.components.v1.iframe(iframe_media_por_total_partido, width=1366, height = 700)

