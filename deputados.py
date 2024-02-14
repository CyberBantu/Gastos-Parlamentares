import streamlit as st
import requests
import pandas as pd


# Função para pegar dados

url = "https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura=57&ordem=ASC&ordenarPor=nome"
resp = requests.get(url).json()
dados = pd.json_normalize(resp['dados'])

# Ajustando tamanho da pagina
st.set_page_config(layout="wide")


st.title("Painel de Gastos de Deputados Federais - Legislatura 2022.")
st.caption('Fonte - Camara dos Deputados / Elaborado por Christian Basilio - Dados Marginais')
st.info("Os gastos parlamentares listados abaixo referem-se aos últimos 6 meses.")

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
        st.text(f"Partido: {tabela_deputado['siglaPartido'].iloc[0]}")
        st.text(f"Estado: {tabela_deputado['siglaUf'].iloc[0]}")
        st.text(f"Email: {tabela_deputado['email'].iloc[0]}")
        
        st.image(url_foto, width=150)

        # card com a soma do valorLiquido
        total_valor_liquido = dados_gastos['Valor Líquido'].str.replace('R$', '').str.replace(',', '').astype(float).sum()
        st.info(f"Total Valor Líquido: R$ {total_valor_liquido:.2f}")

        # Card de valor liquido
        soma_tipo_dispensa = dados_gastos.groupby('Tipo de Despesa')['Valor Líquido'].apply(lambda x: x.str.replace('R$', '').str.replace(',', '').astype(float).sum())
        st.info("Total Valor Líquido por Tipo de Despesa:")
        for tipo_despesa, total_valor in soma_tipo_dispensa.items():
            st.info(f"{tipo_despesa}: R$ {total_valor:.2f}")
        
        dados_gastos = dados_gastos.sort_values(by='Data do Documento', ascending=True)

        st.dataframe(dados_gastos)  
    else:
        st.warning(f"Não há dados de gastos para o deputado {deputy_name}")
else:
    st.warning(f"Não há informações para o deputado {deputy_name}")

st.caption('Elaborado por Christian Basilio (Dados Marginais)')


