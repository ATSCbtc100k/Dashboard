import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Configuración de la página en modo ancho
st.set_page_config(layout="wide")

st.title("Dashboard de Armes Blanques")

# Función para leer el Google Sheet y el archivo Excel
#@st.cache_data(ttl=600)  # El TTL (time to live) se puede ajustar según tus necesidades
def load_data():
    # Conexión al Google Sheet
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="dadesdaga", usecols=list(range(6)), ttl=5)
    df = df.dropna(how="all")
    df['dia'] = pd.to_datetime(df['dia'], errors='coerce')  # Convertir a fecha, ignorando errores
    
    # Leer el archivo Excel
    unitats_df = pd.read_excel('unitats.xlsx')
    
    # Unir los DataFrames por el campo que identifica las unidades
    df = df.merge(unitats_df[['unitat', 'Latitud', 'Longitud']], on='unitat', how='left')
    
    return df

# Cargar los datos
df = load_data()

# Sidebar para seleccionar rango de fechas
start_date = st.sidebar.date_input("Fecha de inicio", value=df['dia'].min())
end_date = st.sidebar.date_input("Fecha de fin", value=df['dia'].max())

# Filtro por 'regio'
regio_options = df['regio'].unique().tolist()
selected_regio = st.sidebar.selectbox("Selecciona una Regió", options=["Totes"] + regio_options)

# Botón para borrar filtros
if st.sidebar.button("Esborrar Filtres"):
    start_date = df['dia'].min()  # Restablecer a la fecha mínima
    end_date = df['dia'].max()  # Restablecer a la fecha máxima
    selected_regio = "Totes"  # Restablecer a la opción por defecto

# Filtrar el DataFrame original según las fechas seleccionadas y la 'regio' (si aplica)
filtered_df = df[(df['dia'] >= pd.Timestamp(start_date)) & (df['dia'] <= pd.Timestamp(end_date))]
if selected_regio != "Totes":
    filtered_df = filtered_df[filtered_df['regio'] == selected_regio]

# Agrupar los datos filtrados por 'regio' para el gráfico 1
regioarmes = filtered_df.groupby('regio')['num_armes'].sum().reset_index()
regioarmes = regioarmes.sort_values(by='num_armes', ascending=False)

# Agrupar los datos filtrados por 'unitat' para el gráfico 2
unitatarmes = filtered_df.groupby('unitat')['num_armes'].sum().reset_index()
unitatarmes = unitatarmes.sort_values(by='num_armes', ascending=False)

# Mostrar los gráficos en dos columnas
col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(regioarmes, x="regio", y="num_armes", 
                   title="Número armes blanques per regió policial", 
                   labels={"regio": "Regió policial", "num_armes": "Número armes blanques"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(unitatarmes, x="unitat", y="num_armes", 
                   title="Número armes blanques per unitat", 
                   labels={"unitat": "Unitat", "num_armes": "Número armes blanques"})
    st.plotly_chart(fig2, use_container_width=True)

# Agrupar el DataFrame por 'unitat' para asegurar que cada unidad sea única en el mapa
grouped_df = filtered_df.groupby('unitat', as_index=False).agg({
    'Latitud': 'first',
    'Longitud': 'first',
    'num_armes': 'sum'
})

# Crear el mapa Folium
m = folium.Map(location=[41.3851, 2.1734], zoom_start=8)  # Centrado en Cataluña
marker_cluster = MarkerCluster().add_to(m)

# Agregar puntos al mapa
for idx, row in grouped_df.iterrows():
    if pd.notna(row['Latitud']) and pd.notna(row['Longitud']):
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=f"Unitat: {row['unitat']}<br>Número de Armes: {row['num_armes']}"
            ,icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)

# Mostrar el mapa en Streamlit
st.subheader("Mapa de Unitats Policials amb Número d'Armes")
st_folium(m, width=800, height=500)
