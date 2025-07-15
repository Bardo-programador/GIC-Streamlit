import streamlit as st
import pandas as pd
import plotly.express as px
import api


st.markdown("""
Este app ajuda a explorar dados do [PNCP](https://www.gov.br/pncp/pt-br) focados em projetos de **cidades inteligentes**.
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
with st.sidebar:
    st.image("img/logo.jpeg", width=200)
    st.header("🎛️ Filtros")

    orgaos = st.multiselect("Órgãos", sorted(df['orgao_nome'].dropna().unique()))
    cidades = st.multiselect("Municípios", sorted(df['municipio_nome'].dropna().unique()))
    ufs = st.multiselect("UF", sorted(df['uf'].dropna().unique()))
    modalidades = st.multiselect("Modalidade", sorted(df['modalidade_licitacao_nome'].dropna().unique()))
    anos = st.multiselect("Ano", sorted(df['ano'].dropna().unique()))
    valor_min, valor_max = st.slider("Valor Global (R$)", 
                                            float(df['valor_global'].min()), 
                                            float(df['valor_global'].max()), 
                                            (float(df['valor_global'].min()), float(df['valor_global'].max())))

# ---- FILTRAGEM
filtered_df = df.copy()
filtered_df["valor_global_por_milhao"] = filtered_df["valor_global"] / 1000000

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
col1, col2, col3, col4 = st.columns(4)
col1.metric("Número de registros", len(filtered_df))
col2.metric("Valor total (Milhão)", f"R${filtered_df['valor_global_por_milhao'].sum():,.3f}")
col3.metric("Órgãos distintos", filtered_df['orgao_nome'].nunique())
col4.metric("Municípios distintos", filtered_df['municipio_nome'].nunique())

# ---- GRÁFICOS
if not filtered_df.empty:
    st.subheader("💰 Top 10 orgãos com maior gasto")
    fig1 = px.bar(filtered_df.groupby('orgao_nome')['valor_global_por_milhao'].sum().reset_index().sort_values('valor_global_por_milhao', ascending=False).head(10),
                  x='orgao_nome', y='valor_global_por_milhao',
                  labels={'orgao_nome':'Órgão', 'valor_global_por_milhao':'Valor Total (em milhão)'},
                  text_auto=True)
    fig1.update_layout(xaxis_tickangle=-45)
    fig1.update_traces(
    texttemplate='%{y:,.3f}',  # formata com milhar
    textposition='outside',      # ou 'auto' / 'inside'
    hovertemplate='%{label}<br>Valor Global: R$%{value:,.3f} milhão ' # formata texto da barra
    )

    fig1.update_layout(
    yaxis_tickformat=',',       # também remove o K do eixo Y
    uniformtext_minsize=8,
    uniformtext_mode='hide'
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🗺 Distribuição por município")
    fig2 = px.pie(filtered_df, names='municipio_nome', values='valor_global',
                  labels={'municipio_nome':'Município', 'valor_global':'Valor Total (R$)'},  
                  title="Participação no Valor Global por Município", subtitle="")
    fig2.update_traces(hovertemplate='%{label}<br>Participação: %{percent}',
                        textinfo='none')  # aqui você controla o texto
    st.plotly_chart(fig2, use_container_width=True)

# ---- TABELA DETALHADA
st.subheader("📝 Dados Detalhados")
st.dataframe(filtered_df[['data_assinatura','orgao_nome','municipio_nome','uf',
                          'modalidade_licitacao_nome','valor_global','description']].sort_values('data_assinatura', ascending=False))

# ---- DOWNLOAD
st.download_button("📥 Baixar dados filtrados (CSV)",
                   data=filtered_df.to_csv(index=False).encode('utf-8'),
                   file_name="data.csv",
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