import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuración de la página
st.set_page_config(page_title="Dashboard Alzheimer & Aging", layout="wide")

# Función para extraer coordenadas de la columna Geolocation
def extract_coords(point_str):
    """Extrae lat y lon del formato 'POINT (lon lat)'"""
    try:
        if pd.isna(point_str): return None, None
        # Busca números (incluyendo negativos y decimales)
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(point_str))
        if len(coords) >= 2:
            # En el formato POINT, el primero suele ser Longitud y el segundo Latitud
            return float(coords[1]), float(coords[0]) 
    except:
        return None, None
    return None, None

@st.cache_data
def load_data():
    # Nombre exacto de tu archivo
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    df = pd.read_csv(file_path)
    
    # 1. Limpieza de Data_Value (manejo de comas y conversión a número)
    if df['Data_Value'].dtype == 'object':
        df['Data_Value'] = df['Data_Value'].astype(str).str.replace(',', '.')
        df['Data_Value'] = pd.to_numeric(df['Data_Value'], errors='coerce')
    
    # 2. Procesar Geolocalización para el mapa
    if 'Geolocation' in df.columns:
        df['lat'], df['lon'] = zip(*df['Geolocation'].map(extract_coords))
    
    # 3. Limpiar límites de confianza por si acaso
    for col in ['Low_Confidence_Limit', 'High_Confidence_Limit']:
        if df[col].dtype == 'object':
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    return df

try:
    df = load_data()

    st.title("🧠 Dashboard de Salud Cognitiva y Envejecimiento")
    st.markdown("Análisis interactivo de datos basados en el dataset de Alzheimer y Envejecimiento Saludable.")

    # --- BARRA LATERAL ---
    st.sidebar.header("Configuración de Filtros")
    
    all_states = sorted(df['LocationDesc'].unique())
    estados = st.sidebar.multiselect(
        "Selecciona Estados:",
        options=all_states,
        default=["Florida", "Illinois", "Georgia", "Arizona"] # Algunos de tus ejemplos
    )

    all_topics = df['Topic'].unique()
    tema = st.sidebar.selectbox("Selecciona un Tema:", options=all_topics)

    # Filtrado dinámico
    df_filtered = df[(df['LocationDesc'].isin(estados)) & (df['Topic'] == tema)]

    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    val_medio = df_filtered['Data_Value'].mean()
    col1.metric("Prevalencia Media", f"{val_medio:.1f}%" if not pd.isna(val_medio) else "N/A")
    col2.metric("Registros filtrados", len(df_filtered))
    col3.metric("Estados en vista", len(estados))

    st.divider()

    # --- MAPA DE CALOR ---
    st.subheader("📍 Mapa de Calor de Prevalencia")
    df_map = df_filtered.dropna(subset=['lat', 'lon', 'Data_Value'])
    
    if not df_map.empty:
        fig_map = px.density_mapbox(
            df_map, 
            lat='lat', lon='lon', z='Data_Value', 
            radius=30,
            center=dict(lat=37.09, lon=-95.71), 
            zoom=3,
            mapbox_style="carto-positron",
            color_continuous_scale="Viridis",
            title=f"Distribución de: {tema}"
        )
        fig_map.update_layout(height=500, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No hay datos de coordenadas para los filtros seleccionados.")

    # --- GRÁFICOS INFERIORES ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Desglose por Estratificación")
        fig_bar = px.bar(
            df_filtered, 
            x='Stratification1', y='Data_Value', color='LocationDesc',
            barmode='group',
            labels={'Data_Value': '%', 'Stratification1': 'Categoría'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Datos en el tiempo / Rango de Confianza")
        fig_box = px.box(
            df_filtered, 
            x='LocationAbbr', y='Data_Value', 
            points="all", 
            color='LocationAbbr',
            title="Variación de valores por Estado"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # --- TABLA ---
    with st.expander("Ver tabla de datos completa"):
        st.write(df_filtered)

except Exception as e:
    st.error(f"Error: {e}")
    st.info(f"Asegúrate de que el archivo '{file_path}' esté en la misma carpeta.")
