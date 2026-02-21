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
    # Asegúrate de que el nombre coincida con tu archivo
    file_path = "Alzheimer's_Disease_and_Healthy_Aging_Data_20260221.csv"
    try:
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

    # --- BARRA LATERAL ---
    st.sidebar.header("⚙️ Configuración Global")
    
    col_tema = 'Topic' if 'Topic' in df.columns else 'Question'
    temas = sorted(df[col_tema].dropna().unique())
    tema_sel = st.sidebar.selectbox("1. Selecciona el Tema:", temas)

    # Filtro de Edad (Basado en Stratification1)
    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Stratification1'].dropna().unique())
    if not edades:
        edades = sorted(df['Stratification1'].dropna().unique())
    edad_sel = st.sidebar.selectbox("2. Grupo de Edad (para Mapa y Comparativa):", edades)

    # Filtrado base
    df_mapa = df[(df[col_tema] == tema_sel) & (df['Stratification1'] == edad_sel)]

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Mapa Nacional", "📊 Comparativa Estados", "👫 Análisis de Género", "📄 Datos"])

    with tab1:
        st.subheader(f"Intensidad de: {tema_sel}")
        df_geo = df_mapa.groupby(['LocationAbbr', 'LocationDesc'])['Data_Value'].mean().reset_index()
        if not df_geo.empty:
            fig_choropleth = px.choropleth(
                df_geo, locations='LocationAbbr', locationmode="USA-states",
                color='Data_Value', scope="usa", color_continuous_scale="Reds",
                hover_name='LocationDesc'
            )
            fig_choropleth.update_layout(geo_scope='usa', margin={"r":0,"t":0,"l":0,"b":0}, height=500)
            st.plotly_chart(fig_choropleth, use_container_width=True)

    with tab2:
        st.subheader("Comparativa entre Estados")
        estados_sel = st.multiselect("Selecciona estados:", 
                                     options=sorted(df_mapa['LocationDesc'].unique()),
                                     default=sorted(df_mapa['LocationDesc'].unique())[:3] if len(df_mapa)>0 else None)
        df_filtered = df_mapa[df_mapa['LocationDesc'].isin(estados_sel)]
        if not df_filtered.empty:
            fig_bar = px.bar(df_filtered, x='Stratification1', y='Data_Value', color='LocationDesc', barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("👫 Prevalencia por Edad y Género")
        st.markdown("Análisis del impacto basado en la distinción por sexo.")

        # LÓGICA QUE SOLICITASTE:
        # 1. Filtramos los datos para el tema seleccionado que tengan info de Género
        prevalence_data = df[df[col_tema] == tema_sel]
        
        gender_age_summary = prevalence_data[prevalence_data['Stratification2'].isin(['Female', 'Male'])] \
                                .groupby(['Stratification1', 'Stratification2'])['Data_Value'] \
                                .mean().reset_index()

        if not gender_age_summary.empty:
            # Recreamos tu barplot de Seaborn pero en Plotly para que sea interactivo
            fig_gender = px.bar(
                gender_age_summary, 
                x='Stratification1', 
                y='Data_Value', 
                color='Stratification2',
                barmode='group',
                color_discrete_map={'Female': 'darkorange', 'Male': 'royalblue'},
                labels={'Data_Value': 'Prevalencia (%)', 'Stratification1': 'Grupo de Edad', 'Stratification2': 'Género'},
                title=f'% Deterioro Cognitivo por Edad y Género ({tema_sel})'
            )
            fig_gender.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_gender, use_container_width=True)

            # "Display" de la tabla resumen
            st.write("**Promedio de prevalencia por grupo de edad y género:**")
            st.dataframe(gender_age_summary, use_container_width=True)
        else:
            st.warning("No hay datos de género (Male/Female) disponibles para este tema.")

    with tab4:
        st.subheader("Vista de Datos")
        st.dataframe(df_mapa, use_container_width=True)

else:
    st.error("Error al cargar el dataset.")
