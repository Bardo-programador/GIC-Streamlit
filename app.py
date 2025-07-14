import streamlit as st
import pandas as pd
import plotly.express as px
import api

st.title("Insights sobre Licitações e Contratos - Cidades Inteligentes")
st.markdown("""
Este app ajuda a explorar dados do PNCP focados em projetos de **cidades inteligentes**.
""")

# Carregar dados
@st.cache_data
def load_data():
    # Você pode trocar para um CSV gerado pelo seu scraper
    data = api.extract_data()
    df = pd.DataFrame(data)

    df['data_assinatura'] = pd.to_datetime(df['data_assinatura'], errors='coerce')
    df['ano'] = pd.to_datetime(df['data_assinatura'], errors='coerce').dt.year
    df['valor_global'] = pd.to_numeric(df['valor_global'], errors='coerce').fillna(0)
    df.to_csv("contratos.csv", header=True, index=False)
    
    return df

df = load_data()

# ---- FILTROS NA SIDEBAR
st.sidebar.header("🎛️ Filtros")

orgaos = st.sidebar.multiselect("Órgãos", sorted(df['orgao_nome'].dropna().unique()))
cidades = st.sidebar.multiselect("Municípios", sorted(df['municipio_nome'].dropna().unique()))
ufs = st.sidebar.multiselect("UF", sorted(df['uf'].dropna().unique()))
modalidades = st.sidebar.multiselect("Modalidade", sorted(df['modalidade_licitacao_nome'].dropna().unique()))
anos = st.sidebar.multiselect("Ano", sorted(df['ano'].dropna().unique()))
valor_min, valor_max = st.sidebar.slider("Valor Global (R$)", 
                                         float(df['valor_global'].min()), 
                                         float(df['valor_global'].max()), 
                                         (float(df['valor_global'].min()), float(df['valor_global'].max())))

# ---- FILTRAGEM
filtered_df = df.copy()
if orgaos:
    filtered_df = filtered_df[filtered_df['orgao_nome'].isin(orgaos)]
if cidades:
    filtered_df = filtered_df[filtered_df['municipio_nome'].isin(cidades)]
if ufs:
    filtered_df = filtered_df[filtered_df['uf'].isin(ufs)]
if modalidades:
    filtered_df = filtered_df[filtered_df['modalidade_licitacao_nome'].isin(modalidades)]
if anos:
    filtered_df = filtered_df[filtered_df['ano'].isin(anos)]

filtered_df = filtered_df[(filtered_df['valor_global'] >= valor_min) & (filtered_df['valor_global'] <= valor_max)]

# ---- MÉTRICAS
st.subheader("📈 Visão Geral")
col1, col2, col3 = st.columns(3)
col1.metric("Número de registros", len(filtered_df))
col2.metric("Valor total (R$)", f"{filtered_df['valor_global'].sum():,.2f}")
col3.metric("Órgãos distintos", filtered_df['orgao_nome'].nunique())

# ---- GRÁFICOS
if not filtered_df.empty:
    st.subheader("💰 Valor global por órgão")
    fig1 = px.bar(filtered_df.groupby('orgao_nome')['valor_global'].sum().reset_index().sort_values('valor_global', ascending=False),
                  x='orgao_nome', y='valor_global',
                  labels={'orgao_nome':'Órgão', 'valor_global':'Valor Total (R$)'},
                  text_auto=True)
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🗺 Distribuição por município")
    fig2 = px.pie(filtered_df, names='municipio_nome', values='valor_global',
                  title="Participação no Valor Global por Município")
    st.plotly_chart(fig2, use_container_width=True)

# ---- TABELA DETALHADA
st.subheader("📝 Dados Detalhados")
st.dataframe(filtered_df[['data_assinatura','orgao_nome','municipio_nome','uf',
                          'modalidade_licitacao_nome','valor_global','description']].sort_values('data_assinatura', ascending=False))

# ---- DOWNLOAD
st.download_button("📥 Baixar dados filtrados (CSV)",
                   data=filtered_df.to_csv(index=False).encode('utf-8'),
                   file_name="dados_filtrados.csv",
                   mime='text/csv')

# ---- GLOSSÁRIO
with st.expander("📖 Glossário das Modalidades de Licitação"):
    st.markdown("""
    ## **Concorrência**  
    Usada para contratos de maior vulto, sem restrição de participação. É o processo licitatório mais amplo, utilizado para obras e serviços acima dos limites legais.

    ## **Tomada de Preços**  
    Para licitações de valores intermediários. Só podem participar empresas previamente cadastradas ou que atendam às condições até 3 dias antes da proposta.

    ## **Convite**  
    Modalidade mais simples, usada para valores menores. A Administração convida no mínimo 3 fornecedores do ramo.

    ## **Pregão Presencial**  
    Licitação para aquisição de bens e serviços comuns, com disputa de lances em sessão presencial.

    ## **Pregão Eletrônico**  
    Semelhante ao presencial, mas realizado via internet, aumentando a competitividade e transparência. Muito usado para compras públicas.

    ## **Concurso**  
    Destina-se à escolha de trabalho técnico, científico ou artístico, mediante prêmios ou remuneração.

    ## **Leilão**  
    Usado para vender bens móveis inservíveis, produtos apreendidos ou imóveis para pagar dívidas.

    ## **Dispensa**  
    A licitação é dispensada por lei em certas hipóteses, como pequenos valores ou situações emergenciais.

    ## **Inexigibilidade**  
    Quando é impossível haver competição, como contratação de profissional de notória especialização ou fornecedor exclusivo.

    ## **Regime Diferenciado de Contratação (RDC)**  
    Modalidade criada por lei para tornar contratações mais céleres, usada principalmente em obras de infraestrutura e grandes eventos.

    ## **Diálogo Competitivo**  
    Modalidade recente, utilizada em contratações complexas, permitindo a Administração dialogar com participantes para definir soluções.

    ### ⚠️ **Observação:**  
    Muitas bases do PNCP registram o pregão como `Pregão - Eletrônico` ou `Pregão Presencial`.  
    Além disso, `Dispensa` e `Inexigibilidade` não são modalidades típicas, mas sim formas legais de contratação direta.
    """)