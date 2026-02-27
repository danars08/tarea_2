import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ---------------- CONFIGURACIÓN ----------------

st.set_page_config(
    page_title="Informe: Salud Cognitiva y Envejecimiento",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #F5F7F9; }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #E6E9EF;
    }
    h1, h2, h3 {
        color: #1E3A8A;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .question-box {
        background-color: #EEF2FF;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #1E3A8A;
        margin-bottom: 15px;
        font-size: 0.95rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- FUNCIONES ----------------

def extract_coords(point_str):
    try:
        if pd.isna(point_str) or str(point_str).strip() == "":
            return None, None
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(point_str))
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0])
    except:
        return None, None
    return None, None


@st.cache_data
def load_data():
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')

        cols_to_fix = ['Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']
        for col in cols_to_fix:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)

        return df

    except Exception as e:
        st.error(f"Error en la carga de datos: {e}")
        return None


# ---------------- APLICACIÓN ----------------

df = load_data()

if df is not None:

    # Título
    st.title("Informe Nacional: Salud Cognitiva y Envejecimiento")

    # Resumen Ejecutivo
    st.markdown("""
    **Resumen Ejecutivo**

    Este informe presenta un análisis descriptivo de la prevalencia autoreportada de dificultad cognitiva funcional en Estados Unidos,
    utilizando el dataset oficial *Alzheimer’s Disease and Healthy Aging Data* del CDC (2026).
    
    El estudio explora la evolución temporal, brechas demográficas y diferencias estatales,
    proporcionando una visión integral del fenómeno en adultos de 50 años en adelante.
    """)

    st.divider()

    # Sidebar
    st.sidebar.markdown("### Integrantes del Proyecto")
    st.sidebar.markdown("""
    * Valentina Torres
    * Melanie Paola Perez 
    * Natalia Sojo 
    * Dana Valentina Ramirez
    """)
    st.sidebar.divider()

    st.sidebar.header("Parámetros de Análisis")

    col_tema = 'Topic' if 'Topic' in df.columns else 'Question'
    temas = sorted(df[col_tema].dropna().unique())
    tema_sel = st.sidebar.selectbox("Seleccione el Tema de Análisis:", temas)

    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Stratification1'].dropna().unique())
    if not edades:
        edades = sorted(df['Stratification1'].dropna().unique())

    edad_sel = st.sidebar.selectbox("Seleccione el Grupo Etario:", edades)

    df_base_tema = df[df[col_tema] == tema_sel]
    df_mapa = df_base_tema[df_base_tema['Stratification1'] == edad_sel]

    # Indicadores
    col1, col2, col3, col4 = st.columns(4)
    avg_val = df_mapa['Data_Value'].mean()

    col1.metric("Prevalencia Promedio", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
    col2.metric("Total de Registros", len(df_mapa))
    col3.metric("Estados Analizados", df_mapa['LocationAbbr'].nunique())
    col4.metric("Actualización", "Feb 2026")

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Evolución Temporal",
        "Análisis Demográfico",
        "Comparativo Estatal",
        "Mapa de Prevalencia",
        "Metodología",
        "Base de Datos"
    ])

    # ---------------- TAB 1 ----------------
    with tab1:
        st.subheader("Tendencia Temporal de la Prevalencia")

        st.markdown('<div class="question-box"><b>Pregunta que responde:</b> ¿Cómo ha evolucionado la prevalencia de dificultad cognitiva funcional en el tiempo para el grupo seleccionado?</div>', unsafe_allow_html=True)

        df_trend = (
            df_mapa.groupby("YearStart")["Data_Value"]
            .mean()
            .reset_index()
            .sort_values("YearStart")
        )

        if not df_trend.empty:
            fig_trend = px.line(
                df_trend,
                x="YearStart",
                y="Data_Value",
                markers=True,
                labels={"YearStart": "Año", "Data_Value": "Prevalencia (%)"}
            )
            fig_trend.update_traces(line=dict(color="#1E3A8A", width=3))
            st.plotly_chart(fig_trend, use_container_width=True)

    # ---------------- TAB 2 ----------------
    with tab2:
        st.subheader("Brechas de Prevalencia por Edad y Género")

        st.markdown('<div class="question-box"><b>Pregunta que responde:</b> ¿Existen diferencias en la prevalencia según edad y género?</div>', unsafe_allow_html=True)

        gender_data = (
            df_base_tema[
                df_base_tema['Stratification2'].isin(['Female', 'Male'])
            ]
            .groupby(['Stratification1', 'Stratification2'])['Data_Value']
            .mean()
            .reset_index()
        )

        if not gender_data.empty:
            fig_gen = px.bar(
                gender_data,
                x='Stratification1',
                y='Data_Value',
                color='Stratification2',
                barmode='group',
                color_discrete_map={
                    'Female': '#EC4899',
                    'Male': '#1E40AF'
                },
                labels={'Data_Value': 'Prevalencia (%)', 'Stratification1': 'Edad'}
            )
            st.plotly_chart(fig_gen, use_container_width=True)

    # ---------------- TAB 3 ----------------
    with tab3:
        st.subheader("Ranking Estatal de Prevalencia")

        st.markdown('<div class="question-box"><b>Pregunta que responde:</b> ¿Qué estados presentan los niveles más altos y más bajos de prevalencia?</div>', unsafe_allow_html=True)

        df_ranking = (
            df_mapa.groupby('LocationDesc')['Data_Value']
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        if not df_ranking.empty:
            fig_rank = px.bar(
                df_ranking.head(10),
                x='Data_Value',
                y='LocationDesc',
                orientation='h',
                color='Data_Value',
                color_continuous_scale="Blues"
            )
            fig_rank.update_layout(showlegend=False)
            st.plotly_chart(fig_rank, use_container_width=True)

    # ---------------- TAB 4 ----------------
    with tab4:
        st.subheader("Distribución Geográfica de la Prevalencia")

        st.markdown('<div class="question-box"><b>Pregunta que responde:</b> ¿Cómo se distribuye geográficamente la prevalencia en Estados Unidos?</div>', unsafe_allow_html=True)

        df_geo = (
            df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value']
            .mean()
            .reset_index()
        )

        if not df_geo.empty:
            fig_map = px.choropleth(
                df_geo,
                locations='LocationAbbr',
                locationmode="USA-states",
                color='Data_Value',
                scope="usa",
                color_continuous_scale="Blues",
                labels={'Data_Value': 'Prevalencia (%)'},
                hover_name='LocationDesc'
            )
            st.plotly_chart(fig_map, use_container_width=True)

    # ---------------- TAB 5 ----------------
    with tab5:
        st.header("Metodología y Sostenibilidad de Datos")

        st.markdown("""
        **Origen:** Centers for Disease Control and Prevention (CDC)  
        **Dataset:** Alzheimer's Disease and Healthy Aging Data  
        **Fecha de acceso:** Febrero 2026  
        """)

    # ---------------- TAB 6 ----------------
    with tab6:
        st.subheader("Explorador de Datos del Informe")
        st.dataframe(df_mapa, use_container_width=True)

        st.divider()
        st.markdown("""
        <div style="text-align: center; color: #6B7280; font-size: 0.8em;">
        Informe Técnico - Alzheimer’s Disease and Healthy Aging Data<br>
        Elaborado por: Valentina Torres, Melanie Paola Perez, Natalia Sojo y Dana Valentina Ramirez.
        </div>
        """, unsafe_allow_html=True)
