import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import io

st.cache_data.clear()
# Título de la app
st.title("📊 Mapa de Mortalidad Materna en Costa Rica (Tasa de mortalidad materna por cada 100 000 nacidos vivos).")

# Cargar datos con caché
@st.cache_data
def cargar_geojson():
    return gpd.read_file("costaricacantonesv10.geojson")

@st.cache_data
def cargar_excel():
    return pd.read_excel("df_merge.xlsx")

# Cargar datasets
try:
    gdf = cargar_geojson()
    df = cargar_excel()
except Exception as e:
    st.error(f"Ocurrió un error cargando los archivos: {e}")
    st.stop()

# Filtrar años desde 2014
df = df[df['year'] >= 2014]

# Sidebar para filtros
st.sidebar.title("Filtros 📌")

# Selección de año para el mapa
anios_disponibles = sorted(df['year'].unique())
anio_seleccionado = st.sidebar.selectbox("Selecciona un año para el mapa", anios_disponibles)

# Selección de cantones y años para estadísticas
cantones_disponibles = sorted(df['canton'].unique())
cantones_seleccionados = st.sidebar.multiselect("Selecciona cantones", cantones_disponibles, default=cantones_disponibles[:5])
anios_seleccionados = st.sidebar.multiselect("Selecciona años", anios_disponibles, default=anios_disponibles)

# ===============================
# MAPA INTERACTIVO
# ===============================

st.subheader("🗺️ Mapa Interactivo")

df_filtrado = df[df['year'] == anio_seleccionado]
gdf_merged = gdf.merge(df_filtrado, how="left", left_on="NAME_2", right_on="canton")

# Crear mapa base
m = folium.Map(location=[9.7489, -83.7534], zoom_start=8)

# Función para colorear según tasa
def color_por_tasa(tasa):
    if pd.isnull(tasa):
        return 'gray'
    elif tasa == 0:
        return 'green'
    elif tasa < 20:
        return 'orange'
    else:
        return 'red'

# Añadir polígonos al mapa
for _, row in gdf_merged.iterrows():
    color = color_por_tasa(row['tasa_mortalidad_maternapor_cienmil'])
    folium.GeoJson(
        row['geometry'],
        style_function=lambda feature, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=folium.Tooltip(f"""
            <strong>Cantón:</strong> {row['NAME_2']}<br>
            <strong>Tasa Mortalidad Materna:</strong> {row['tasa_mortalidad_maternapor_cienmil'] if not pd.isnull(row['tasa_mortalidad_maternapor_cienmil']) else 'Sin datos'}<br>
            <strong>Defunciones Maternas:</strong> {row['cantidad_defunciones_maternas'] if not pd.isnull(row['cantidad_defunciones_maternas']) else 'Sin datos'}
        """)
    ).add_to(m)

# Mostrar mapa
st_folium(m, width=800, height=600)

# Leyenda
st.markdown("""
**🟢 Tasa = 0**  
**🟠 Tasa entre 0 y 20**  
**🔴 Tasa mayor a 20**  
**⚪ Sin dato**
""")

# ===============================
# DESCARGA DE DATOS
# ===============================
# Filtrar datos según selección
df_seleccion = df[(df['canton'].isin(cantones_seleccionados)) & (df['year'].isin(anios_seleccionados))]

st.write("### 📥 Descargar datos filtrados")
if not df_seleccion.empty:
    buffer = io.StringIO()
    df_seleccion.to_csv(buffer, index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=buffer.getvalue(),
        file_name="datos_filtrados.csv",
        mime="text/csv"
    )
else:
    st.write("No hay datos para descargar.")
