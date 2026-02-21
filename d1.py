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
    st.sidebar.header("⚙️ Configuración")
    
    col_tema = 'Topic' if 'Topic' in df.columns else 'Question'
    temas = sorted(df[col_tema].dropna().unique())
    tema_sel = st.sidebar.selectbox("Selecciona el Tema:", temas)

    # Edad para el Mapa
    df_solo_edad = df[df['StratificationCategory1'] == 'Age Group']
    edades = sorted(df_solo_edad['Stratification1'].dropna().unique())
    if not edades:
        edades = sorted(df['Stratification1'].dropna().unique())
    edad_sel = st.sidebar.selectbox("Grupo de Edad (para Mapa):", edades)

    # Filtrado base para cálculos
    df_base_tema = df[df[col_tema] == tema_sel]
    df_mapa = df_base_tema[df_base_tema['Stratification1'] == edad_sel]

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Mapa Nacional", "🏆 Ranking Top/Bottom", "👫 Análisis de Género", "📄 Datos"])

    with tab1:
        st.subheader(f"Distribución Geográfica: {tema_sel}")
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
        st.subheader("📊 Ranking de Estados (Extremos)")
        st.write(f"Análisis automático de los estados con mayores y menores índices para: **{tema_sel}**")

        # Calculamos promedios por estado para el ranking
        df_ranking = df_mapa.groupby('LocationDesc')['Data_Value'].mean().sort_values(ascending=False).reset_index()

        if not df_ranking.empty:
            top_5 = df_ranking.head(5)
            bottom_5 = df_ranking.tail(5)

            col_a, col_b = st.columns(2)
            
            with col_a:
                st.error("🔺 Top 5: Valores más Altos")
                fig_top = px.bar(top_5, x='Data_Value', y='LocationDesc', orientation='h',
                                 color='Data_Value', color_continuous_scale='Reds',
                                 labels={'Data_Value': '% Prevalencia', 'LocationDesc': 'Estado'})
                fig_top.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

            with col_b:
                st.success("🔹 Bottom 5: Valores más Bajos")
                fig_bot = px.bar(bottom_5, x='Data_Value', y='LocationDesc', orientation='h',
                                 color='Data_Value', color_continuous_scale='Blues',
                                 labels={'Data_Value': '% Prevalencia', 'LocationDesc': 'Estado'})
                fig_bot.update_layout(showlegend=False, yaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_bot, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para generar el ranking.")

    with tab3:
        st.subheader("👫 Prevalencia por Edad y Género")
        # Tu lógica de género personalizada
        gender_age_summary = df_base_tema[df_base_tema['Stratification2'].isin(['Female', 'Male'])] \
                                .groupby(['Stratification1', 'Stratification2'])['Data_Value'] \
                                .mean().reset_index()

        if not gender_age_summary.empty:
            fig_gender = px.bar(
                gender_age_summary, x='Stratification1', y='Data_Value', color='Stratification2',
                barmode='group', color_discrete_map={'Female': 'darkorange', 'Male': 'royalblue'},
                title=f'% Impacto por Género ({tema_sel})'
            )
            st.plotly_chart(fig_gender, use_container_width=True)
            st.write("**Resumen de Datos:**")
            st.dataframe(gender_age_summary, use_container_width=True)

    with tab4:
        st.subheader("Explorador de Datos")
        st.dataframe(df_mapa, use_container_width=True)

else:
    st.error("Error al cargar el dataset.")
