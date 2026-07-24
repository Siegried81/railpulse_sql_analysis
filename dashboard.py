import sqlite3
import pandas as pd
import streamlit as st

# Configure the Streamlit page layout
st.set_page_config(
    page_title="RailPulse Operations - Brussels-Central",
    page_icon="🚆",
    layout="wide",
)


# Connect to the SQLite database and query strictly for Brussels-Central
@st.cache_data
def load_data():
    conn = sqlite3.connect("data/railpulse.db")

    # Strict query targeting specifically Brussels-Central / Brussel-Centraal
    query = """
        SELECT 
            st.trip_id,
            st.stop_sequence,
            st.arrival_time,
            st.departure_time,
            st.stop_headsign AS stop_schedule_headsign,
            st.pickup_type,
            st.drop_off_type,
            st.shape_dist_traveled,
            s.stop_id,
            s.stop_code,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            s.zone_id,
            s.platform_code,
            t.route_id,
            t.service_id,
            t.trip_headsign,
            t.trip_short_name,
            t.direction_id,
            t.block_id
        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        WHERE s.stop_name = 'Bruxelles-Central' 
           OR s.stop_name = 'Brussel-Centraal'
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


try:
    data = load_data()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# Dashboard Title
st.title("🚆 RailPulse Operational Dashboard - Bruxelles-Central")
st.markdown(
    "Comprehensive analysis of station timetables, arrival/departure schedules, and routing metadata for Brussels-Central."
)

if data.empty:
    st.warning(
        "No records found for Bruxelles-Central. Please make sure you have imported the GTFS data."
    )
    st.stop()

# Main Key Performance Indicators (KPIs)
col1, col2, col3 = st.columns(3)
with col1:
    total_stops = len(data)
    st.metric(label="Total Scheduled Stops", value=total_stops)
with col2:
    unique_trips = (
        data["trip_id"].nunique() if "trip_id" in data.columns else 0
    )
    st.metric(label="Unique Trips Tracked", value=unique_trips)
with col3:
    unique_routes = (
        data["route_id"].nunique() if "route_id" in data.columns else 0
    )
    st.metric(label="Associated Routes", value=unique_routes)

st.markdown("---")

# Analytical Visualizations / Overview
st.subheader("📊 Schedule Overview - Departures by Hour")
if "departure_time" in data.columns:
    try:
        data["hour"] = pd.to_datetime(
            data["departure_time"], format="%H:%M:%S", errors="coerce"
        ).dt.hour
        hourly_counts = data["hour"].value_counts().sort_index()
        st.bar_chart(hourly_counts)
        st.markdown("**Distribution of train departures by hour of the day.**")    
    except Exception:
        st.info("Departure times available in raw format.")
else:
    st.warning("Departure time column not available.")

# Raw Data Preview with all available columns
with st.expander(
    "🔍 View Complete Raw SQL Data Set"
):
    st.dataframe(data)