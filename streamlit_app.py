import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IIT Indore Weather Station Dashboard",
    page_icon="WQgH_yKt.jpg",  # Uses your uploaded logo for the browser tab favicon
    layout="wide"
)

# --- IIT INDORE OFFICIAL PALETTE BRANDING ENGINE ---
# Primary Teal: #008080 | Accent Amber: #D4AF37 | Light Slate Background: #F4F6F6
custom_theme_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Sanskrit&display=swap');

    /* Global typography settings */
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, div {
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
    }

    /* Primary Heading color accent modification */
    h1, h2, h3 {
        color: #006666 !important;
    }

    /* Custom modifications to the Streamlit Metric display cards */
    [data-testid="stMetricValue"] {
        color: #008080 !important;
        font-weight: bold;
    }
    
    [data-testid="stMetricLabel"] {
        color: #4A4A4A !important;
        font-size: 1.1rem !important;
    }

    /* Sidebar background panel custom styling tint */
    [data-testid="stSidebar"] {
        background-color: #E6F2F2 !important;
        border-right: 2px solid #008080;
    }
</style>
"""
st.markdown(custom_theme_css, unsafe_allow_html=True)

# Add the uploaded logo dynamically into the main dashboard page banner header
col_header_logo, col_header_title = st.columns([1, 10])
with col_header_logo:
    try:
        st.image("image_ad4426.png", width=90)
    except:
        pass
with col_header_title:
    st.title("IIT Indore Weather Dashboard")
    st.markdown("An interactive analysis app exploring microclimatic records from the IIT Indore Station.")

# --- LIVE DATA LOADING ENGINE FROM GOOGLE DRIVE ---
@st.cache_data(ttl=600)  # Refreshes the cache to pull new data every 10 minutes
def load_and_preprocess_data():
    share_url = "https://docs.google.com/spreadsheets/d/1OuNO5Er2ZbjF3fWpDj7c7hPxtfqFRXbWpGS7t-xAkMA/edit?usp=sharing"
    csv_url = share_url.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(csv_url)
    
    df.columns = df.columns.str.strip()
    
    def parse_custom_date(row):
        try:
            date_str = str(row['Date']).replace('IST', '').strip()
            full_str = f"{row['Year']} {date_str}"
            return pd.to_datetime(full_str, format="%Y %d-%b %H:%M:%S")
        except:
            return pd.NaT

    df['Timestamp'] = df.apply(parse_custom_date, axis=1)
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    df['Just_Date'] = df['Timestamp'].dt.date
    
    if 'Wind Direction' in df.columns:
        df['Wind Direction'] = df['Wind Direction'].astype(str).str.strip()
        
        # Translation dictionary for non-standard sensor headings
        direction_map = {
            "NN": "N",
            "EE": "E",
            "SS": "S",
            "WW": "W"
        }
        df['Wind Direction'] = df['Wind Direction'].replace(direction_map)
    
    metric_cols = ["Temperature", "Humidity", "Rain", "Wind Speed", "Solar Radiation"]
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    df = load_and_preprocess_data()
except Exception as e:
    st.error(f"Google Sheets Connection Error: Could not read data from the provided link. Details: {e}")
    st.stop()

# --- SIDEBAR INTERFACE & CONTROL FILTERS ---
st.sidebar.header("Dashboard Control Panel")

# 1. Custom Date Range Filter
st.sidebar.subheader("Filter Timeline Epoch")
min_available_date = df['Just_Date'].min()
max_available_date = df['Just_Date'].max()

default_start = max(min_available_date, max_available_date - timedelta(days=30))

date_range = st.sidebar.date_input(
    "Select Date Boundaries:",
    value=(default_start, max_available_date),
    min_value=min_available_date,
    max_value=max_available_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df['Just_Date'] >= start_date) & (df['Just_Date'] <= end_date)]
else:
    filtered_df = df
    start_date, end_date = min_available_date, max_available_date

# 2. Variable Selector Map
st.sidebar.subheader("Metric Graph Selector")
metric_options = {
    "Rainfall (mm)": "Rain",
    "Temperature (°C)": "Temperature",
    "Relative Humidity (%)": "Humidity",
    "Solar Radiation (W/m²)": "Solar Radiation",
    "Wind Speed (km/h)": "Wind Speed",
    "Wind Direction (Compass)": "Wind Direction"
}

selected_label = st.sidebar.selectbox("Select Climate Metric to Graph Below", list(metric_options.keys()))
target_column = metric_options[selected_label]

if filtered_df.empty:
    st.warning(f"No meteorological entries found between {start_date} and {end_date}. Please choose a wider window in the sidebar.")
    st.stop()

# --- HOME PAGE ALL-DETAILS SUMMARY SNAPSHOT ---
st.markdown("---")
st.subheader(f"📊 Weather Summary Overview Dashboard ({start_date} to {end_date})")
st.markdown("Here is the complete overview of all station parameters over your selected timeline window:")

card1, card2, card3, card4, card5 = st.columns(5)

with card1:
    st.metric(
        label="Total Rainfall", 
        value=f"{filtered_df['Rain'].sum():.1f} mm"
    )
with card2:
    st.metric(
        label="Average Temperature", 
        value=f"{filtered_df['Temperature'].mean():.1f} °C",
        delta=f"Max: {filtered_df['Temperature'].max():.1f} °C",
        delta_color="normal"
    )
with card3:
    st.metric(
        label="Average Humidity", 
        value=f"{filtered_df['Humidity'].mean():.1f} %"
    )
with card4:
    st.metric(
        label="Peak Solar Radiation", 
        value=f"{filtered_df['Solar Radiation'].max():.0f} W/m²",
        delta=f"Avg: {filtered_df['Solar Radiation'].mean():.0f}",
        delta_color="off"
    )
with card5:
    st.metric(
        label="Average Wind Speed", 
        value=f"{filtered_df['Wind Speed'].mean():.1f} km/h",
        delta=f"Max: {filtered_df['Wind Speed'].max():.1f}",
        delta_color="normal"
    )

# --- CONDITIONAL INTERACTIVE GRAPH SETUP ---
st.markdown("---")

if selected_label == "Wind Direction (Compass)":
    st.subheader(f"Wind Direction Frequency Distribution ({start_date} to {end_date})")
    st.markdown("This chart counts how often the wind blew from each compass direction over your selected timeframe.")
    
    # Styled with IIT Indore Brand Teal (#008080)
    direction_chart = alt.Chart(filtered_df).mark_bar(color="#008080").encode(
        x=alt.X('Wind Direction:N', sort='-y', title="Wind Direction Categories"),
        y=alt.Y('count():Q', title="Total Frequency / Readings Count"),
        tooltip=['Wind Direction:N', 'count():Q']
    ).properties(
        width=900,
        height=400,
        title="Dominant Wind Profiles at IIT Indore"
    ).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit'
    ).configure_title(
        font='Tiro Devanagari Sanskrit'
    )
    
    st.altair_chart(direction_chart, use_container_width=True)

else:
    st.subheader(f"Detailed Timeline Chart: {selected_label}")
    st.caption("Pro-Tip: You can click and drag your mouse cursor horizontally over this timeline to sub-filter the distribution chart below!")

    brush = alt.selection_interval(encodings=['x'])

    # Chart A: Top Timeline Trend Graph - Colored in deep IITI Teal (#006666)
    timeline_chart = alt.Chart(filtered_df).mark_line(color="#006666", interpolate='monotone').encode(
        x=alt.X('Timestamp:T', title="Timeline Axis"),
        y=alt.Y(f'{target_column}:Q', title=selected_label),
        tooltip=['Timestamp:T', f'{target_column}:Q']
    ).properties(
        width=900,
        height=300,
        title=f"Continuous Sensor Readings Over Time"
    ).add_params(
        brush
    )

    # Chart B: Bottom Distribution Histogram - Colored in coordinating IITI Gold/Amber (#D4AF37)
    distribution_chart = alt.Chart(filtered_df).mark_bar(color="#D4AF37").encode(
        x=alt.X(f'{target_column}:Q', bin=alt.Bin(maxbins=30), title=f"Value Scale Ranges ({selected_label})"),
        y=alt.Y('count()', title="Occurrences / Observations Count"),
        tooltip=['count()']
    ).properties(
        width=900,
        height=200,
        title=f"Isolated Regional Frequency Distribution"
    ).transform_filter(
        brush
    )

    unified_interactive_chart = alt.vconcat(timeline_chart, distribution_chart).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit'
    ).configure_title(
        font='Tiro Devanagari Sanskrit'
    )

    st.altair_chart(unified_interactive_chart, use_container_width=True)

# --- CUSTOM HOURLY PROFILER MATRIX ---
st.markdown("---")
st.subheader("Diurnal Parameter Cycle Inspector")

filtered_df['Hour'] = filtered_df['Timestamp'].dt.hour
hourly_agg = filtered_df.groupby('Hour')[target_column].mean().reset_index()

# Colored in an elegant, translucent blend of IITI Teal (#008080)
hourly_chart = alt.Chart(hourly_agg).mark_area(
    color="#008080",
    opacity=0.4,
    line={'color': '#006666'}
).encode(
    x=alt.X('Hour:Q', title="Hour of Day (24hr Clock)", scale=alt.Scale(domain=[0, 23])),
    y=alt.Y(f'{target_column}:Q', title=f"Mean {selected_label}"),
    tooltip=['Hour', f'{target_column}']
).properties(
    height=250,
    title=f"Average 24-Hour Diurnal Progression Signature for {selected_label}"
).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit'
).configure_title(
        font='Tiro Devanagari Sanskrit'
)

st.altair_chart(hourly_chart, use_container_width=True)

# --- CLEAN DATA VIEW / EXPORT ENGINE ---
st.markdown("---")
with st.expander("View and Download Filtered Local Station Records"):
    st.dataframe(filtered_df.drop(columns=['Just_Date']))
    st.download_button(
        label="Download This Filtered Dataset (CSV)",
        data=filtered_df.drop(columns=['Just_Date']).to_csv(index=False).encode('utf-8'),
        file_name=f"IITI_Filtered_Data_{start_date}_to_{end_date}.csv",
        mime="text/csv"
    )
