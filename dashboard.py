# ============================================================
# DASHBOARD - PROGRAMA DE BECAS
# Ministerio de Trabajo y Previsión Social
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard - Programa de Becas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def load_data():
    """Carga los datos procesados desde el archivo CSV"""
    try:
        # Reemplaza con la ruta a tu archivo CSV exportado desde R
        df = pd.read_csv("becarios_filtrados.csv")
        return df
    except FileNotFoundError:
        # Datos de ejemplo (para demostración)
        st.warning("Archivo de datos no encontrado. Usando datos de ejemplo.")
        return create_sample_data()

def create_sample_data():
    """Crea datos de ejemplo para demostración"""
    np.random.seed(123)
    n = 500
    data = {
        'Sexo': np.random.choice(['MUJER', 'HOMBRE'], n),
        'Edad_Corregida': np.random.randint(18, 25, n),
        'Duracion_Dias': np.random.randint(30, 180, n),
        'Absorcion_Laboral': np.random.choice(['Sí', 'No'], n, p=[0.35, 0.65]),
        'Nivel_Educativo_Cat': np.random.choice(['Primaria', 'Básico', 'Diversificado', 'Universitario'], n),
        'Departamento_Corregido': np.random.choice(['Guatemala', 'Quetzaltenango', 'Escuintla', 'Chimaltenango', 'Petén', 'Sololá', 'Totonicapán', 'Sacatepéquez'], n),
        'Pueblo de Pertenencia': np.random.choice(['Mestizo', 'Ladino', 'Maya', 'Xinka'], n),
        'Puesto': np.random.choice(['Asistente Administrativo', 'Gestor de Cobros', 'Receptor Pagador', 'Auxiliar de Limpieza', 'Encargado de Pasillo', 'Asesor de Créditos'], n)
    }
    return pd.DataFrame(data)

# ============================================================
# FUNCIONES DE ANÁLISIS
# ============================================================
def calcular_indicadores(df):
    """Calcula los indicadores clave del programa"""
    total = len(df)
    absorbidos = sum(df['Absorcion_Laboral'] == 'Sí')
    tasa_absorcion = (absorbidos / total) * 100 if total > 0 else 0
    
    # Indicadores por categoría
    por_sexo = df.groupby('Sexo')['Absorcion_Laboral'].apply(lambda x: (x == 'Sí').mean() * 100).reset_index()
    por_nivel = df.groupby('Nivel_Educativo_Cat')['Absorcion_Laboral'].apply(lambda x: (x == 'Sí').mean() * 100).reset_index()
    por_depto = df.groupby('Departamento_Corregido')['Absorcion_Laboral'].apply(lambda x: (x == 'Sí').mean() * 100).reset_index()
    por_puesto = df.groupby('Puesto')['Absorcion_Laboral'].apply(lambda x: (x == 'Sí').mean() * 100).reset_index()
    
    return {
        'total': total,
        'absorbidos': absorbidos,
        'tasa_absorcion': tasa_absorcion,
        'por_sexo': por_sexo,
        'por_nivel': por_nivel,
        'por_depto': por_depto,
        'por_puesto': por_puesto
    }

# ============================================================
# SIDEBAR - FILTROS
# ============================================================
def crear_filtros(df):
    """Crea los filtros interactivos en el sidebar"""
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por sexo
    sexo_options = ['Todos'] + list(df['Sexo'].unique())
    sexo_selected = st.sidebar.multiselect(
        "Sexo",
        sexo_options,
        default=['Todos']
    )
    
    # Filtro por departamento
    depto_options = ['Todos'] + list(df['Departamento_Corregido'].unique())
    depto_selected = st.sidebar.multiselect(
        "Departamento",
        depto_options,
        default=['Todos']
    )
    
    # Filtro por nivel educativo
    nivel_options = ['Todos'] + list(df['Nivel_Educativo_Cat'].unique())
    nivel_selected = st.sidebar.multiselect(
        "Nivel Educativo",
        nivel_options,
        default=['Todos']
    )
    
    # Filtro por absorción
    absorcion_options = ['Todos', 'Sí', 'No']
    absorcion_selected = st.sidebar.radio(
        "Absorción Laboral",
        ['Todos', 'Sí', 'No'],
        index=0
    )
    
    # Filtro por edad
    edad_min = int(df['Edad_Corregida'].min())
    edad_max = int(df['Edad_Corregida'].max())
    edad_range = st.sidebar.slider(
        "Rango de Edad",
        edad_min,
        edad_max,
        (edad_min, edad_max)
    )
    
    return {
        'sexo': sexo_selected,
        'depto': depto_selected,
        'nivel': nivel_selected,
        'absorcion': absorcion_selected,
        'edad': edad_range
    }

def aplicar_filtros(df, filtros):
    """Aplica los filtros seleccionados al dataframe"""
    df_filtered = df.copy()
    
    # Filtro por sexo
    if filtros['sexo'] and 'Todos' not in filtros['sexo']:
        df_filtered = df_filtered[df_filtered['Sexo'].isin(filtros['sexo'])]
    
    # Filtro por departamento
    if filtros['depto'] and 'Todos' not in filtros['depto']:
        df_filtered = df_filtered[df_filtered['Departamento_Corregido'].isin(filtros['depto'])]
    
    # Filtro por nivel educativo
    if filtros['nivel'] and 'Todos' not in filtros['nivel']:
        df_filtered = df_filtered[df_filtered['Nivel_Educativo_Cat'].isin(filtros['nivel'])]
    
    # Filtro por absorción
    if filtros['absorcion'] != 'Todos':
        df_filtered = df_filtered[df_filtered['Absorcion_Laboral'] == filtros['absorcion']]
    
    # Filtro por edad
    df_filtered = df_filtered[
        (df_filtered['Edad_Corregida'] >= filtros['edad'][0]) &
        (df_filtered['Edad_Corregida'] <= filtros['edad'][1])
    ]
    
    return df_filtered

# ============================================================
# VISUALIZACIONES
# ============================================================
def crear_kpi_indicadores(df):
    """Crea los KPI principales"""
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df)
    absorbidos = sum(df['Absorcion_Laboral'] == 'Sí')
    tasa = (absorbidos / total) * 100 if total > 0 else 0
    edad_promedio = df['Edad_Corregida'].mean()
    
    with col1:
        st.metric("👥 Total Becarios", f"{total:,}")
    with col2:
        st.metric("✅ Absorbidos", f"{absorbidos:,}")
    with col3:
        st.metric("📈 Tasa de Absorción", f"{tasa:.1f}%")
    with col4:
        st.metric("🎂 Edad Promedio", f"{edad_promedio:.1f} años")

def crear_mapa_calor_correlacion(df):
    """Crea mapa de calor de correlaciones"""
    # Seleccionar variables numéricas
    cols_numericas = ['Edad_Corregida', 'Duracion_Dias']
    
    # Codificar variables categóricas para correlación
    df_corr = df.copy()
    df_corr['Sexo_Cod'] = (df_corr['Sexo'] == 'HOMBRE').astype(int)
    df_corr['Absorcion_Cod'] = (df_corr['Absorcion_Laboral'] == 'Sí').astype(int)
    
    # Niveles educativos codificados
    nivel_map = {'Primaria': 1, 'Básico': 2, 'Diversificado': 3, 'Universitario': 4}
    df_corr['Nivel_Cod'] = df_corr['Nivel_Educativo_Cat'].map(nivel_map)
    
    # Matriz de correlación
    corr_matrix = df_corr[['Edad_Corregida', 'Duracion_Dias', 'Sexo_Cod', 'Absorcion_Cod', 'Nivel_Cod']].corr()
    
    # Crear heatmap con Plotly
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        text=corr_matrix.round(2).values,
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title='Mapa de Calor - Matriz de Correlación (Spearman)',
        height=500,
        width=600
    )
    
    return fig

def crear_mapa_guatemala(df):
    """Crea un mapa de calor de Guatemala por departamento"""
    # Coordenadas aproximadas para departamentos de Guatemala
    depto_coords = {
        'Guatemala': {'lat': 14.6349, 'lon': -90.5069},
        'Quetzaltenango': {'lat': 14.8347, 'lon': -91.5181},
        'Escuintla': {'lat': 14.3038, 'lon': -90.7848},
        'Chimaltenango': {'lat': 14.6620, 'lon': -90.8193},
        'Petén': {'lat': 16.9138, 'lon': -89.8910},
        'Sololá': {'lat': 14.7700, 'lon': -91.1830},
        'Totonicapán': {'lat': 14.9180, 'lon': -91.3610},
        'Sacatepéquez': {'lat': 14.5566, 'lon': -90.7283},
        'Quiché': {'lat': 15.0467, 'lon': -91.1488},
        'Jalapa': {'lat': 14.6349, 'lon': -89.9853},
        'Jutiapa': {'lat': 14.2918, 'lon': -89.8956},
        'San Marcos': {'lat': 14.9610, 'lon': -91.7960},
        'Suchitepéquez': {'lat': 14.5335, 'lon': -91.5067},
        'Retalhuleu': {'lat': 14.5361, 'lon': -91.6824},
        'Totonicapán': {'lat': 14.9120, 'lon': -91.3610},
        'Alta Verapaz': {'lat': 15.5041, 'lon': -90.3108},
        'Baja Verapaz': {'lat': 15.0644, 'lon': -90.2671},
        'Chiquimula': {'lat': 14.8000, 'lon': -89.5500},
        'El Progreso': {'lat': 14.8500, 'lon': -90.0667},
        'Huehuetenango': {'lat': 15.3167, 'lon': -91.4667},
        'Izabal': {'lat': 15.5000, 'lon': -89.0000},
        'Santa Rosa': {'lat': 14.2500, 'lon': -90.3000},
        'Zacapa': {'lat': 14.9667, 'lon': -89.5333},
    }
    
    # Calcular tasa de absorción por departamento
    depto_absorcion = df.groupby('Departamento_Corregido')['Absorcion_Laboral'].apply(
        lambda x: (x == 'Sí').mean() * 100
    ).reset_index()
    depto_absorcion.columns = ['Departamento', 'Tasa_Absorcion']
    
    # Agregar coordenadas
    depto_absorcion['Lat'] = depto_absorcion['Departamento'].map(
        lambda x: depto_coords.get(x, {'lat': None, 'lon': None})['lat']
    )
    depto_absorcion['Lon'] = depto_absorcion['Departamento'].map(
        lambda x: depto_coords.get(x, {'lat': None, 'lon': None})['lon']
    )
    
    # Eliminar departamentos sin coordenadas
    depto_absorcion = depto_absorcion.dropna(subset=['Lat', 'Lon'])
    
    # Crear mapa de burbujas
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=depto_absorcion['Lat'],
        lon=depto_absorcion['Lon'],
        mode='markers+text',
        marker=go.scattermapbox.Marker(
            size=depto_absorcion['Tasa_Absorcion'] * 0.5 + 10,
            color=depto_absorcion['Tasa_Absorcion'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Tasa de Absorción (%)")
        ),
        text=depto_absorcion['Departamento'],
        textposition='top center',
        hovertext=depto_absorcion.apply(
            lambda x: f"{x['Departamento']}<br>Tasa: {x['Tasa_Absorcion']:.1f}%",
            axis=1
        ),
        hoverinfo='text'
    ))
    
    fig.update_layout(
        title='Mapa de Absorción por Departamento',
        mapbox=dict(
            style='carto-positron',
            center=dict(lat=15.5, lon=-90.5),
            zoom=6.5
        ),
        height=600,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def crear_grafico_absorcion_puesto(df):
    """Crea gráfico de barras de absorción por puesto"""
    puesto_data = df.groupby('Puesto').agg(
        Total=('Puesto', 'count'),
        Absorbidos=('Absorcion_Laboral', lambda x: (x == 'Sí').sum()),
        Tasa=('Absorcion_Laboral', lambda x: (x == 'Sí').mean() * 100)
    ).reset_index()
    
    # Ordenar por tasa y tomar top 10
    puesto_data = puesto_data.sort_values('Tasa', ascending=False).head(10)
    
    fig = px.bar(
        puesto_data,
        x='Tasa',
        y='Puesto',
        orientation='h',
        color='Tasa',
        color_continuous_scale='RdYlGn',
        text=puesto_data['Tasa'].apply(lambda x: f'{x:.1f}%'),
        title='Top 10 Puestos por Tasa de Absorción'
    )
    
    fig.update_layout(
        xaxis_title='Tasa de Absorción (%)',
        yaxis_title='',
        height=450,
        showlegend=False
    )
    
    fig.update_traces(textposition='outside')
    
    return fig

def crear_grafico_absorcion_depto(df):
    """Crea gráfico de barras de absorción por departamento"""
    depto_data = df.groupby('Departamento_Corregido').agg(
        Total=('Departamento_Corregido', 'count'),
        Absorbidos=('Absorcion_Laboral', lambda x: (x == 'Sí').sum()),
        Tasa=('Absorcion_Laboral', lambda x: (x == 'Sí').mean() * 100)
    ).reset_index()
    
    depto_data = depto_data.sort_values('Tasa', ascending=False)
    
    fig = px.bar(
        depto_data,
        x='Departamento_Corregido',
        y='Tasa',
        color='Tasa',
        color_continuous_scale='RdYlGn',
        text=depto_data['Tasa'].apply(lambda x: f'{x:.1f}%'),
        title='Tasa de Absorción por Departamento'
    )
    
    fig.update_layout(
        xaxis_title='Departamento',
        yaxis_title='Tasa de Absorción (%)',
        height=450,
        showlegend=False
    )
    
    fig.update_traces(textposition='outside')
    
    return fig

def crear_grafico_distribucion_edad(df):
    """Crea histograma de distribución de edad"""
    fig = px.histogram(
        df,
        x='Edad_Corregida',
        color='Absorcion_Laboral',
        barmode='group',
        title='Distribución de Edad por Absorción Laboral',
        color_discrete_map={'Sí': '#2ECC71', 'No': '#E74C3C'},
        nbins=10
    )
    
    fig.update_layout(
        xaxis_title='Edad (años)',
        yaxis_title='Frecuencia',
        height=400,
        bargap=0.1
    )
    
    return fig

def crear_grafico_duracion_vs_absorcion(df):
    """Crea boxplot de duración vs absorción"""
    fig = px.box(
        df,
        x='Absorcion_Laboral',
        y='Duracion_Dias',
        color='Absorcion_Laboral',
        title='Duración de Beca vs Absorción Laboral',
        color_discrete_map={'Sí': '#2ECC71', 'No': '#E74C3C'}
    )
    
    fig.update_layout(
        xaxis_title='Absorción Laboral',
        yaxis_title='Duración (días)',
        height=400,
        showlegend=False
    )
    
    return fig

def crear_grafico_nivel_educativo(df):
    """Crea gráfico de absorción por nivel educativo"""
    nivel_data = df.groupby('Nivel_Educativo_Cat').agg(
        Total=('Nivel_Educativo_Cat', 'count'),
        Absorbidos=('Absorcion_Laboral', lambda x: (x == 'Sí').sum()),
        Tasa=('Absorcion_Laboral', lambda x: (x == 'Sí').mean() * 100)
    ).reset_index()
    
    # Ordenar por nivel educativo
    orden_niveles = ['Primaria', 'Básico', 'Diversificado', 'Universitario']
    nivel_data['Nivel_Educativo_Cat'] = pd.Categorical(
        nivel_data['Nivel_Educativo_Cat'],
        categories=orden_niveles,
        ordered=True
    )
    nivel_data = nivel_data.sort_values('Nivel_Educativo_Cat')
    
    fig = px.bar(
        nivel_data,
        x='Nivel_Educativo_Cat',
        y='Tasa',
        color='Tasa',
        color_continuous_scale='RdYlGn',
        text=nivel_data['Tasa'].apply(lambda x: f'{x:.1f}%'),
        title='Tasa de Absorción por Nivel Educativo'
    )
    
    fig.update_layout(
        xaxis_title='Nivel Educativo',
        yaxis_title='Tasa de Absorción (%)',
        height=400,
        showlegend=False
    )
    
    fig.update_traces(textposition='outside')
    
    return fig

def crear_grafico_sexo(df):
    """Crea gráfico de absorción por sexo"""
    sexo_data = df.groupby('Sexo').agg(
        Total=('Sexo', 'count'),
        Absorbidos=('Absorcion_Laboral', lambda x: (x == 'Sí').sum()),
        Tasa=('Absorcion_Laboral', lambda x: (x == 'Sí').mean() * 100)
    ).reset_index()
    
    fig = px.pie(
        sexo_data,
        values='Total',
        names='Sexo',
        title='Distribución por Sexo',
        color='Sexo',
        color_discrete_map={'MUJER': '#E74C3C', 'HOMBRE': '#3498DB'}
    )
    
    fig.update_layout(height=400)
    
    return fig

# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
def main():
    # Cargar datos
    df = load_data()
    
    # Título principal
    st.title("📊 Programa de Becas - Dashboard de Análisis")
    st.markdown("---")
    
    # Filtros
    filtros = crear_filtros(df)
    df_filtrado = aplicar_filtros(df, filtros)
    
    # Mostrar número de registros filtrados
    st.sidebar.markdown("---")
    st.sidebar.metric("Registros filtrados", f"{len(df_filtrado):,}")
    
    # ============================================================
    # SECCIÓN 1: KPI INDICADORES
    # ============================================================
    st.header("🎯 Indicadores Clave")
    crear_kpi_indicadores(df_filtrado)
    
    st.markdown("---")
    
    # ============================================================
    # SECCIÓN 2: VISUALIZACIONES PRINCIPALES
    # ============================================================
    st.header("📈 Análisis de Absorción Laboral")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de absorción por puesto
        fig_puesto = crear_grafico_absorcion_puesto(df_filtrado)
        st.plotly_chart(fig_puesto, use_container_width=True)
    
    with col2:
        # Gráfico de absorción por departamento
        fig_depto = crear_grafico_absorcion_depto(df_filtrado)
        st.plotly_chart(fig_depto, use_container_width=True)
    
    # ============================================================
    # SECCIÓN 3: DISTRIBUCIONES
    # ============================================================
    st.header("📊 Distribuciones y Comparaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por edad
        fig_edad = crear_grafico_distribucion_edad(df_filtrado)
        st.plotly_chart(fig_edad, use_container_width=True)
    
    with col2:
        # Duración vs absorción
        fig_duracion = crear_grafico_duracion_vs_absorcion(df_filtrado)
        st.plotly_chart(fig_duracion, use_container_width=True)
    
    # ============================================================
    # SECCIÓN 4: NIVEL EDUCATIVO Y SEXO
    # ============================================================
    col1, col2 = st.columns(2)
    
    with col1:
        # Nivel educativo
        fig_nivel = crear_grafico_nivel_educativo(df_filtrado)
        st.plotly_chart(fig_nivel, use_container_width=True)
    
    with col2:
        # Distribución por sexo
        fig_sexo = crear_grafico_sexo(df_filtrado)
        st.plotly_chart(fig_sexo, use_container_width=True)
    
    # ============================================================
    # SECCIÓN 5: MAPA DE CALOR Y MAPA
    # ============================================================
    st.header("🗺️ Mapas de Calor y Geográfico")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Mapa de calor de correlaciones
        fig_heatmap = crear_mapa_calor_correlacion(df_filtrado)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        # Mapa de Guatemala
        try:
            fig_mapa = crear_mapa_guatemala(df_filtrado)
            st.plotly_chart(fig_mapa, use_container_width=True)
        except Exception as e:
            st.warning(f"Error al generar el mapa: {e}")
    
    # ============================================================
    # SECCIÓN 6: TABLA DE DATOS
    # ============================================================
    st.header("📋 Datos Filtrados")
    
    # Mostrar tabla con opción de descarga
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Botón de descarga
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv,
        file_name="datos_becarios_filtrados.csv",
        mime="text/csv"
    )

# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    main()
