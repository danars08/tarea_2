import streamlit as st
import pandas as pd
import plotly.express as px
import re
import io

# Configuración de la página
st.set_page_config(page_title="Dashboard Alzheimer & Aging", layout="wide")

# --- FUNCIONES DE APOYO ---

def extract_coords(point_str):
    """Extrae latitud y longitud del formato 'POINT (longitud latitud)'"""
    try:
        if pd.isna(point_str) or str(point_str).strip() == "":
            return None, None
        # Busca números decimales o enteros (incluyendo negativos)
        coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(point_str))
        if len(coords) >= 2:
            # En formato POINT de este dataset: [0] es Longitud, [1] es Latitud
            return float(coords[1]), float(coords[0]) 
    except:
        return None, None
    return None, None

@st.cache_data
def load_data():
    # Nombre exacto de tu archivo (asegúrate que la extensión sea .csv)
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    
    try:
        # Intentar detectar el separador automáticamente (coma, punto y coma, etc.)
        # engine='python' es más flexible con errores de formato
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        
        # Limpieza de Data_Value: Convertir "45,4" -> 45.4
        if 'Data_Value' in df.columns:
            if df['Data_Value'].dtype == 'object':
                df['Data_Value'] = df['Data_Value'].astype(str).str.replace(',', '.')
            df['Data_Value'] = pd.to_numeric(df['Data_Value'], errors='coerce')
        
        # Extraer Coordenadas
        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)
            
        # Limpiar límites de confianza numéricos
        for col in ['Low_Confidence_Limit', 'High_Confidence_Limit']:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df
    except Exception as e:
        st.error(f"Error crítico al leer el archivo: {e}")
        return None

# --- LÓGICA DE LA APP ---

df = load_data()

if df is not None:
    # --- TÍTULO ---
    st.title("🧠 Dashboard de Salud Cognitiva y Envejecimiento")
    st.info("Datos analizados del BRFSS sobre Alzheimer y deterioro cognitivo.")

    # --- BARRA LATERAL (Filtros Globales) ---
    st.sidebar.header("🔍 Filtros de Visualización")
    
    # Filtro de Tema
    temas_disponibles = sorted(df['Topic'].dropna().unique())
    tema_sel = st.sidebar.selectbox("Selecciona un Tema:", temas_disponibles)

    # Filtro de Estado
    estados_disponibles = sorted(df['LocationDesc'].dropna().unique())
    estados_sel = st.sidebar.multiselect(
        "Selecciona Estados:", 
        options=estados_disponibles,
        default=estados_disponibles[:3] # Selecciona los 3 primeros por defecto
    )

    # Filtrar el DataFrame
    mask = (df['Topic'] == tema_sel) & (df['LocationDesc'].isin(estados_sel))
    df_filtered = df[mask]

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    with m1:
        avg_val = df_filtered['Data_Value'].mean()
        st.metric("Prevalencia Media", f"{avg_val:.2f}%" if not pd.isna(avg_val) else "N/A")
    with m2:
        st.metric("Total Registros", len(df_filtered))
    with m3:
        st.metric("Estados Filtrados", len(estados_sel))

    st.divider()

    # --- MAPA DE CALOR ---
    st.subheader("📍 Mapa de Calor: Distribución Geográfica")
    # Solo filas con coordenadas y valor
    df_map = df_filtered.dropna(subset=['lat', 'lon', 'Data_Value'])
    
    if not df_map.empty:
        fig_map = px.density_mapbox(
            df_map, 
            lat='lat', lon='lon', z='Data_Value', 
            radius=25,
            center=dict(lat=37.09, lon=-95.71), # Centro de USA
            zoom=3,
            mapbox_style="carto-positron",
            color_continuous_scale="Reds",
            labels={'Data_Value': 'Valor %'}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No hay datos geográficos para mostrar en el mapa con los filtros actuales.")

    # --- GRÁFICOS ---
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Comparativa por Estratificación")
        if not df_filtered.empty:
            # Agrupamos por estratificación para un gráfico más limpio
            fig_bar = px.bar(
                df_filtered, 
                x='Stratification1', 
                y='Data_Value', 
                color='LocationDesc',
                barmode='group',
                labels={'Data_Value': '% de Prevalencia', 'Stratification1': 'Categoría'},
                template="plotly_white"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("📈 Rango de Confianza (Bajo vs Alto)")
        if not df_filtered.empty:
            fig_scatter = px.scatter(
                df_filtered,
                x='Low_Confidence_Limit',
                y='High_Confidence_Limit',
                color='LocationDesc',
                hover_data=['Stratification1'],
                labels={'Low_Confidence_Limit': 'Límite Inferior', 'High_Confidence_Limit': 'Límite Superior'}
            )
            # Línea de referencia y = x
            fig_scatter.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="gray", dash="dash"))
            st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TABLA DE DATOS ---
    with st.expander("📄 Ver Datos Detallados"):
        st.dataframe(df_filtered.drop(columns=['lat', 'lon'], errors='ignore'), use_container_width=True)

else:
    st.warning("No se pudo cargar el dataset. Revisa el nombre del archivo y su ubicación.")
