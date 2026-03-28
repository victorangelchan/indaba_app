import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
from PIL import Image

# ==========================
# CONFIGURACIÓN DE LA APP
# ==========================
st.set_page_config(page_title="INTERFAZ DE CONSULTAS INDABA", layout="wide")
st.title("INTERFAZ DE CONSULTAS INDABA")

# ==========================
# LOGO
# ==========================
logo = Image.open("INDABA_LOGO_2026.png")
st.sidebar.image(logo, width=200)

# ==========================
# CARGAR DATOS Y TRADUCIR IDs
# ==========================
@st.cache_data
def load_data():
    conn = sqlite3.connect("INDABA.db")
    
    carriers = pd.read_sql_query("SELECT * FROM CARRIERS", conn)
    services = pd.read_sql_query("SELECT * FROM SERVICES", conn)
    invoices = pd.read_sql_query("SELECT * FROM INVOICES", conn)
    
    conn.close()

    invoices = invoices.merge(
        carriers[['CARRIER_ID', 'CARRIER_NAME']],
        on='CARRIER_ID',
        how='left'
    )
    
    invoices = invoices.merge(
        services[['SERVICE_ID', 'SERVICE_NAME']],
        on='SERVICE_ID',
        how='left'
    )
    
    invoices['DATE_INVOICE'] = pd.to_datetime(
        invoices['DATE_INVOICE'],
        errors='coerce'
    )
    
    return invoices

df = load_data()

# ==========================
# FILTROS
# ==========================
st.sidebar.header("Filtros de búsqueda")

carrier_filter = st.sidebar.multiselect("Carrier", options=df['CARRIER_NAME'].dropna().unique())
from_country_filter = st.sidebar.multiselect("From Country", options=df['FROM_COUNTRY'].dropna().unique())
to_country_filter = st.sidebar.multiselect("To Country", options=df['TO_COUNTRY'].dropna().unique())
program_filter = st.sidebar.multiselect("Program", options=df['PROGRAM'].dropna().unique())
status_filter = st.sidebar.multiselect("Status", options=df['STATUS'].dropna().unique())
service_filter = st.sidebar.multiselect("Service", options=df['SERVICE_NAME'].dropna().unique())
item_filter = st.sidebar.multiselect("Item", options=df['ITEM'].dropna().unique())

order_number_filter = st.sidebar.text_input("Order Number")
invoice_number_filter = st.sidebar.text_input("Invoice Number")
tracking_number_filter = st.sidebar.text_input("Tracking Number")

date_range = st.sidebar.date_input("Rango Fecha Invoice", [])
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = None

# ==========================
# APLICAR FILTROS
# ==========================
df_filtered = df.copy()

if carrier_filter:
    df_filtered = df_filtered[df_filtered['CARRIER_NAME'].isin(carrier_filter)]
if from_country_filter:
    df_filtered = df_filtered[df_filtered['FROM_COUNTRY'].isin(from_country_filter)]
if to_country_filter:
    df_filtered = df_filtered[df_filtered['TO_COUNTRY'].isin(to_country_filter)]
if program_filter:
    df_filtered = df_filtered[df_filtered['PROGRAM'].isin(program_filter)]
if status_filter:
    df_filtered = df_filtered[df_filtered['STATUS'].isin(status_filter)]
if service_filter:
    df_filtered = df_filtered[df_filtered['SERVICE_NAME'].isin(service_filter)]
if item_filter:
    df_filtered = df_filtered[df_filtered['ITEM'].isin(item_filter)]
if order_number_filter:
    df_filtered = df_filtered[df_filtered['ORDER_NUMBER'].str.contains(order_number_filter, case=False, na=False)]
if invoice_number_filter:
    df_filtered = df_filtered[df_filtered['INVOICE_NUMBER'].str.contains(invoice_number_filter, case=False, na=False)]
if tracking_number_filter:
    df_filtered = df_filtered[df_filtered['TRACKING_NUMBER'].str.contains(tracking_number_filter, case=False, na=False)]
if start_date and end_date:
    df_filtered = df_filtered[
        (df_filtered['DATE_INVOICE'] >= pd.to_datetime(start_date)) &
        (df_filtered['DATE_INVOICE'] <= pd.to_datetime(end_date))
    ]

# ==========================
# RESULTADOS
# ==========================
st.subheader(f"Resultados: {len(df_filtered)} registros encontrados")
st.dataframe(df_filtered)

# ==========================
# GRÁFICAS DE COST
# ==========================
st.subheader("Gráficas de Cost")

group_options = [
    "DATE_INVOICE",
    "CARRIER_NAME",
    "FROM_COUNTRY",
    "TO_COUNTRY",
    "PROGRAM",
    "ITEM"
]

group_by_option = st.selectbox("Agrupar por", group_options)

df_grouped = df_filtered.groupby(group_by_option)['COST'].sum().reset_index()

bars = alt.Chart(df_grouped).mark_bar().encode(
    x=group_by_option,
    y='COST',
    tooltip=[group_by_option, 'COST']
)

text = bars.mark_text(
    align='center',
    baseline='bottom',
    dy=-2
).encode(
    text=alt.Text('COST:Q', format=".2f")
)

chart = (bars + text).interactive()

st.altair_chart(chart, use_container_width=True)


#--- PARA ACTUALIZAR BD
#git add INDABA.db
#git commit -m "Auto update BD"
#git push