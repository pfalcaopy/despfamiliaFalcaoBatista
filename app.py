import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
from io import BytesIO

st.set_page_config(page_title="Feedback Dashboard", layout="wide")
st.title("📋 Despesas da Família Falcão Batista")

# --- TABS ---
aba_formulario, aba_dashboard = st.tabs(["📝 Formulário", "📊 Análise de Dados"])

with aba_formulario:
    st.subheader("📋 Preencha o formulário abaixo")
    components.iframe(
        src="https://docs.google.com/forms/d/e/1FAIpQLSd2dWPuYi-3y0uoIPQvYIK4m2MyY6ig5QxOFOUTwjYhUyhX3A/viewform?embedded=true",
        width=500,
        height=2500,
        scrolling=True
    )

with aba_dashboard:
    st.subheader("📊 Resumo de despesas")  

    # --- LEITURA DO CSV ---
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBkpKdCzmIo75NeXMB3yZNwao619HoP47aeflTbibUTfplVOkXAiBJjEzqjqChkYPsWm0a2Ip8p-AA/pub?gid=802273684&single=true&output=csv"

    @st.cache_data
    def carregar_dados(url):
        df = pd.read_csv(url)
        df['Competência'] = pd.to_datetime(df['Competência'], errors='coerce')
        df['Ano'] = df['Competência'].dt.year
        df['Mês'] = df['Competência'].dt.strftime('%B')

        meses_portugues = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril',
            'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto',
            'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        df['Mês'] = df['Mês'].replace(meses_portugues)

        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
        df['Participantes'] = pd.to_numeric(df['Participantes'], errors='coerce')
        df['Valor p/ Cada'] = df['Valor'] / df['Participantes']
        return df

    df = carregar_dados(csv_url)

    # --- FILTROS ---
    st.markdown("")
    st.markdown("### 🎯 Filtros")
    col1, col2 = st.columns(2)
    with col1:
        anos = sorted(df['Ano'].dropna().unique(), reverse=True)
        ano_selecionado = st.selectbox("Selecione o Ano", anos)
    with col2:
        meses = df['Mês'].dropna().unique()
        mes_selecionado = st.selectbox("Selecione o Mês", meses)
    
    st.markdown("-------------------------------------")

    # --- FILTRA DADOS ---
    df_filtrado = df[(df['Ano'] == ano_selecionado) & (df['Mês'] == mes_selecionado)].copy()

    # --- TRATAMENTO DE VALORES ---
    df_filtrado['Valor'] = pd.to_numeric(df_filtrado['Valor'], errors='coerce')
    df_filtrado['Valor p/ Cada'] = pd.to_numeric(df_filtrado['Valor p/ Cada'], errors='coerce')

    valor_total = df_filtrado['Valor'].sum()
    valor_total_pessoa = df_filtrado['Valor p/ Cada'].sum()
    participantes = int(df_filtrado['Participantes'].iloc[0]) if not df_filtrado.empty else 0

    # --- CÓPIA PARA EXIBIÇÃO ---
    df_exibicao = df_filtrado.copy()
    df_exibicao['Valor'] = df_exibicao['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_exibicao['Valor p/ Cada'] = df_exibicao['Valor p/ Cada'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    meses_portugues = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril',
        'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto',
        'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    df_exibicao['Competência'] = df_exibicao['Competência'].dt.strftime('%B/%Y').replace(meses_portugues, regex=True)

    colunas_ordenadas = ['Despesa','Fornecedor','Competência','Valor','Valor p/ Cada','Parcela','Observação']
    df_exibicao = df_exibicao[colunas_ordenadas]
    df_exibicao = df_exibicao.rename(columns={'Valor': 'Valor Total', 'Valor p/ Cada': 'Valor p/ Cada'})

    # --- CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"### 📊 Valor Total")
        st.metric('', f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    with col2:
        st.markdown("### 📊 Valor para Cada")
        st.metric('', f"R$ {valor_total_pessoa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    with col3:
        st.markdown("### 👥 Participantes")
        st.metric('', f'Dividido por {participantes} 👤')
    with col4:
        st.markdown("")

    st.markdown("-------------------------------------")

    # --- GRAFICOS ---
    st.markdown("### 📈 Gráfico de Despesas")

    df_grafico_desp = df_filtrado.groupby('Despesa')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=False)
    df_grafico_for = df_filtrado.groupby('Fornecedor')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=False)

    grafico_desp = alt.Chart(df_grafico_desp).mark_bar().encode(
        y=alt.Y('Despesa', sort='-x', title=''),
        x=alt.X('Valor', title='Valor Total (R$)'),
        color=alt.Color('Despesa', legend=None)
    ).properties(title="Despesas por Categoria")

    texto_desp = alt.Chart(df_grafico_desp).mark_text(
        align='left',
        baseline='middle',
        dx=3
    ).encode(
        y=alt.Y('Despesa', sort='-x'),
        x='Valor',
        text=alt.Text('Valor', format=',.2f')
    )

    grafico_for = alt.Chart(df_grafico_for).mark_bar().encode(
        y=alt.Y('Fornecedor', sort='-x', title=''),
        x=alt.X('Valor', title='Valor Total (R$)'),
        color=alt.Color('Fornecedor', legend=None)
    ).properties(title="Despesas por Fornecedor")

    texto_for = alt.Chart(df_grafico_for).mark_text(
        align='left',
        baseline='middle',
        dx=3
    ).encode(
        y=alt.Y('Fornecedor', sort='-x'),
        x='Valor',
        text=alt.Text('Valor', format=',.2f')
    )

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(grafico_desp + texto_desp, use_container_width=True)
    with col2:
        st.altair_chart(grafico_for + texto_for, use_container_width=True)

    st.markdown("-------------------------------------")

    # --- TABELA ---
    st.markdown("### 📋 Despesas do mês")
    st.dataframe(df_exibicao, use_container_width=True)

    # --- EXPORTAR COMO CSV (substituindo PDF) ---
    st.markdown("### 📤 Exportar")

    csv = df_exibicao.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Baixar resumo em CSV",
        data=csv,
        file_name="resumo_despesas.csv",
        mime="text/csv"
    )

    st.markdown("-------------------------------------")

