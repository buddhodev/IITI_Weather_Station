import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IIT Indore Weather Station Dashboard",
    page_icon="IITI_S_Logo.jpg",  # Uses your uploaded logo for the browser tab favicon
    layout="wide"
)

# --- IIT INDORE OFFICIAL COBALT BLUE LIGHT-MODE BRANDING ENGINE ---
custom_theme_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Sanskrit&display=swap');

    /* STRICT LIGHT-MODE PROGRAMMATIC OVERRIDES */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #EBF2FA !important;
        color: #2C3E50 !important;
    }

    /* Target specific markdown and text paragraphs safely without breaking core icon engines */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
        color: #003396 !important;
    }

    .custom-blue-text {
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
        color: #003396 !important;
    }

    /* Universal Clean Metric Card Design - No pitch-black blocks */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border: 1px solid #D5D8DC !important;
    }
    
    /* Primary numeric metric color adjustment to IIT Indore Corporate Blue */
    div[data-testid="stMetricValue"] {
        color: #003396 !important;
        font-weight: bold !important;
        font-size: 1.8rem !important;
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
    }
    
    /* Custom metric structural labels changed from grey to clean Blue */
    div[data-testid="stMetricLabel"] p {
        color: #003396 !important;
        font-size: 1.05rem !important;
        font-weight: bold !important;
        margin-bottom: 0px !important;
    }

    /* Sidebar background panel custom styling tint */
    [data-testid="stSidebar"] {
        background-color: #F0F4F8 !important;
        border-right: 2px solid #003396;
    }
    
    /* Keep sidebar navigation settings easily readable in corporate theme tones */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #003396 !important;
        font-weight: bold !important;
    }
    
    /* Institutional Attribution Footer styling */
    .institutional-footer {
        width: 100%; 
        text-align: center; 
        color: #566573; 
        font-size: 0.95rem; 
        padding-top: 10px;
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
    }
    
    .institutional-footer strong {
        color: #003396 !important;
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
    }

    /* PERMANENT EXPANDER FIX: Protect summary container structure from custom font layout leakage */
    div[data-testid="stExpander"] details summary {
        font-family: system-ui, -apple-system, sans-serif !important;
    }

    /* Target ONLY the layout text paragraph inside the block to leave icons untouched */
    div[data-testid="stExpander"] details summary p {
        font-family: 'Tiro Devanagari Sanskrit', serif !important;
        color: #003396 !important;
        font-weight: bold !important;
        font-size: 1.05rem !important;
        display: inline !important;
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
    st.markdown('<p class="custom-blue-text">An interactive analysis app exploring microclimatic records from the IIT Indore Station.</p>', unsafe_allow_html=True)

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
    filtered_df = df[(df['Just_Date'] >= start_date) & (df['Just_Date'] <= end_date)].copy()
else:
    filtered_df = df.copy()
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
st.subheader(f"Weather Summary Overview Dashboard ({start_date} to {end_date})")
st.markdown('<p class="custom-blue-text">Here is the complete overview of all station parameters over your selected timeline window:</p>', unsafe_allow_html=True)

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
    st.markdown('<p class="custom-blue-text">This chart counts how often the wind blew from each compass direction over your selected timeframe.</p>', unsafe_allow_html=True)
    
    direction_chart = alt.Chart(filtered_df).mark_bar(color="#003396").encode(
        x=alt.X('Wind Direction:N', sort='-y', title="Wind Direction Categories"),
        y=alt.Y('count():Q', title="Total Frequency / Readings Count"),
        tooltip=['Wind Direction:N', 'count():Q']
    ).properties(
        width=900,
        height=400,
        title="Dominant Wind Profiles at IIT Indore"
    ).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit',
        labelColor='#003396',
        titleColor='#003396'
    ).configure_title(
        font='Tiro Devanagari Sanskrit',
        color='#003396'
    )
    
    st.altair_chart(direction_chart, use_container_width=True)

else:
    st.subheader(f"Detailed Timeline Chart: {selected_label}")
    st.caption("Pro-Tip: You can click and drag your mouse cursor horizontally over this timeline to sub-filter the distribution chart below!")

    brush = alt.selection_interval(encodings=['x'])

    # Chart A: Top Timeline Trend Graph - Colored in deep Cobalt Blue (#003396)
    timeline_chart = alt.Chart(filtered_df).mark_line(color="#003396", interpolate='monotone').encode(
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

    # Chart B: Bottom Distribution Histogram - Colored in Slate Gray (#566573)
    distribution_chart = alt.Chart(filtered_df).mark_bar(color="#566573").encode(
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
        titleFont='Tiro Devanagari Sanskrit',
        labelColor='#003396',
        titleColor='#003396'
    ).configure_title(
        font='Tiro Devanagari Sanskrit',
        color='#003396'
    )

    st.altair_chart(unified_interactive_chart, use_container_width=True)

# --- CUSTOM HOURLY PROFILER MATRIX ---
st.markdown("---")
st.subheader("Diurnal Parameter Cycle Inspector")

filtered_df['Hour'] = filtered_df['Timestamp'].dt.hour

# Safe evaluation to protect against trying to calculate numeric averages on categorical string data
if pd.api.types.is_numeric_dtype(filtered_df[target_column]):
    hourly_agg = filtered_df.groupby('Hour')[target_column].mean().reset_index()

    hourly_chart = alt.Chart(hourly_agg).mark_area(
        color="#003396",
        opacity=0.3,
        line={'color': '#003396'}
    ).encode(
        x=alt.X('Hour:Q', title="Hour of Day (24hr Clock)", scale=alt.Scale(domain=[0, 23])),
        y=alt.Y(f'{target_column}:Q', title=f"Mean {selected_label}"),
        tooltip=['Hour', f'{target_column}']
    ).properties(
        height=250,
        title=f"Average 24-Hour Diurnal Progression Signature for {selected_label}"
    ).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit',
        labelColor='#003396',
        titleColor='#003396'
    ).configure_title(
        font='Tiro Devanagari Sanskrit',
        color='#003396'
    )
else:
    # Alternative visualization fallback for Wind Direction categorical trend by Hour
    hourly_chart = alt.Chart(filtered_df).mark_rect().encode(
        x=alt.X('Hour:O', title="Hour of Day (24hr Clock)"),
        y=alt.X('Wind Direction:N', title="Wind Direction"),
        color=alt.Color('count():Q', scale=alt.Scale(scheme='blues'), title="Reading Count"),
        tooltip=['Hour', 'Wind Direction', 'count()']
    ).properties(
        height=250,
        title="Hourly Distribution Density Matrix for Wind Directions"
    ).configure_axis(
        labelFont='Tiro Devanagari Sanskrit',
        titleFont='Tiro Devanagari Sanskrit',
        labelColor='#003396',
        titleColor='#003396'
    ).configure_title(
        font='Tiro Devanagari Sanskrit',
        color='#003396'
    )

st.altair_chart(hourly_chart, use_container_width=True)

# --- CLEAN DATA VIEW / EXPORT ENGINE ---
st.markdown("---")
# Isolated wrapper structure successfully loads the toggle drop-down cleanly while honoring the light-theme default
with st.expander("View and Download Filtered Local Station Records"):
    st.dataframe(filtered_df.drop(columns=['Just_Date']))
    st.download_button(
        label="Download This Filtered Dataset (CSV)",
        data=filtered_df.drop(columns=['Just_Date']).to_csv(index=False).encode('utf-8'),
        file_name=f"IITI_Filtered_Data_{start_date}_to_{end_date}.csv",
        mime="text/csv"
    )

# --- INSTITUTIONAL ATTRIBUTION FOOTNOTE ---
st.markdown("---")
footer_html = """
<div class="institutional-footer">
    Created and Maintained by <strong>Buddhodev Ghosh</strong> (Doctoral Candidate Under <strong>Prof. G S Murthy</strong>, Sustainable Technologies Lab, IIT Indore)
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
