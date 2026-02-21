import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Configuración de la página
st.set_page_config(page_title="Alzheimer & Aging Stats", layout="wide")

# --- FUNCIONES DE LIMPIEZA ---

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
        # Detectar delimitador automáticamente
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
        
        # Limpieza de valores numéricos
        for col in ['Data_Value', 'Low_Confidence_Limit', 'High_Confidence_Limit']:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Procesar geolocalización
        if 'Geolocation' in df.columns:
            coords = df['Geolocation'].apply(extract_coords)
            df[['lat', 'lon']] = pd.DataFrame(coords.tolist(), index=df.index)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

# --- EJECUCIÓN DEL DASHBOARD ---

df = load_data()

if df is not None:
    st.title("🧠 Dashboard: Salud Cognitiva y Envejecimiento")

    # --- VALIDACIÓN DE COLUMNAS (Para evitar el KeyError) ---
    # En tu dataset, la edad suele estar en 'Stratification1' cuando 'StratificationCategory1' es 'Age Group'
    col_edad = 'Stratification1' if 'Stratification1' in df.columns else 'Age Group'
    col_tema = 'Topic' if 'Topic' in df.columns else 'Question'

    # --- BARRA LATERAL ---
    st.sidebar.header("⚙️ Configuración Global")
    
    # Filtro de Tema
    temas = sorted(df[col_tema].dropna().unique())
    tema_sel = st.sidebar.selectbox("1. Selecciona el Tema:", temas)

    # Filtro de Edad (Buscamos los valores de edad en Stratification1)
    # Filtramos el dataframe para obtener solo los valores que pertenecen a la categoría de edad
    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Stratification1'].dropna().unique())
    
    if not edades: # Si no encuentra nada, usa la columna general
        edades = sorted(df[col_edad].dropna().unique())
        
    edad_sel = st.sidebar.selectbox("2. Grupo de Edad:", edades)

    # Filtrado base para el mapa
    df_mapa = df[(df[col_tema] == tema_sel) & (df[col_edad] == edad_sel)]

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["🌍 Mapa Nacional", "📊 Comparativa de Estados", "📄 Datos Detallados"])

    with tab1:
        st.subheader(f"Intensidad de: {tema_sel}")
        
        df_geo = df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value'].mean().reset_index()

        if not df_geo.empty:
            fig_choropleth = px.choropleth(
                df_geo,
                locations='LocationAbbr',
                locationmode="USA-states",
                color='Data_Value',
                scope="usa",
                color_continuous_scale="Reds",
                labels={'Data_Value': '% Prevalencia'},
                hover_name='LocationDesc'
            )
            fig_choropleth.update_layout(geo_scope='usa', margin={"r":0,"t":0,"l":0,"b":0}, height=500)
            st.plotly_chart(fig_choropleth, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para generar el mapa con estos filtros.")

    with tab2:
        st.subheader("Comparativa entre Estados")
        estados_sel = st.multiselect(
            "Selecciona estados:", 
            options=sorted(df_mapa['LocationDesc'].unique()),
            default=sorted(df_mapa['LocationDesc'].unique())[:3] if len(df_mapa) > 0 else None
        )
        
        df_filtered = df_mapa[df_mapa['LocationDesc'].isin(estados_sel)]

        if not df_filtered.empty:
            c1, c2 = st.columns(2)
            with c1:
                # Usamos Stratification2 para ver el desglose (Raza/Sexo) si existe
                eje_x = 'Stratification2' if 'Stratification2' in df.columns else 'Stratification1'
                fig_bar = px.bar(df_filtered, x=eje_x, y='Data_Value', color='LocationDesc',
                                 barmode='group', title="Desglose por Categoría")
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                st.write("**Tabla Comparativa**")
                st.dataframe(df_filtered[['LocationDesc', eje_x, 'Data_Value']], use_container_width=True)
        else:
            st.info("Selecciona estados en el menú de arriba para comparar.")

    with tab3:
        st.subheader("Vista de Datos")
        st.dataframe(df_mapa, use_container_width=True)

else:
    st.error("Archivo no encontrado o error en la carga.")
