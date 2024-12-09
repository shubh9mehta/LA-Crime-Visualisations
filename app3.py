import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster
import plotly.express as px
import calplot

# Load Data
@st.cache_data
def load_data():
    data = pd.read_csv("crime_data_cleaned.csv", low_memory=False)
    # Handle missing and invalid data
    data['date_occ'] = pd.to_datetime(data['date_occ'], errors='coerce')
    data['time_occ'] = pd.to_numeric(data['time_occ'], errors='coerce')
    data['crm_cd_desc'] = data['crm_cd_desc'].fillna("Unknown")
    data['vict_sex'] = data['vict_sex'].fillna("Unknown")
    data['area_name'] = data['area_name'].fillna("Unknown")
    data['vict_descent'] = data['vict_descent'].fillna("Unknown")
    data['crm_cd_2'] = data['crm_cd_2'].fillna("N/A")
    data['crm_cd_3'] = data['crm_cd_3'].fillna("N/A")
    data['crm_cd_4'] = data['crm_cd_4'].fillna("N/A")
    data['weapon_desc'] = data['weapon_desc'].fillna("Unknown")
    # Exclude rows with invalid coordinates
    data = data[(data['lat'] != 0) & (data['lon'] != 0)]
    return data

crime_data = load_data()

# Crime categories
violent_crimes = [
    "INTIMATE PARTNER - SIMPLE ASSAULT", "INTIMATE PARTNER - AGGRAVATED ASSAULT", "ROBBERY",
    "ASSAULT WITH DEADLY WEAPON, AGGRAVATED ASSAULT", "BATTERY - SIMPLE ASSAULT", "RAPE, FORCIBLE",
    "CHILD ABUSE (PHYSICAL) - SIMPLE ASSAULT", "KIDNAPPING", "STALKING", "CRIMINAL HOMICIDE"
]
property_crimes = [
    "VEHICLE - STOLEN", "BURGLARY FROM VEHICLE", "BIKE - STOLEN", "BURGLARY", "ARSON",
    "THEFT-GRAND ($950.01 & OVER)", "SHOPLIFTING-GRAND THEFT ($950.01 & OVER)"
]
cyber_white_collar_crimes = [
    "UNAUTHORIZED COMPUTER ACCESS", "THEFT OF IDENTITY", "CREDIT CARDS, FRAUD USE ($950.01 & OVER)",
    "HUMAN TRAFFICKING - COMMERCIAL SEX ACTS", "BUNCO, GRAND THEFT", "BRIBERY"
]
miscellaneous_crimes = [
    "TRESPASSING", "DISTURBING THE PEACE", "RESISTING ARREST", "FALSE POLICE REPORT",
    "WEAPONS POSSESSION/BOMBING", "INDECENT EXPOSURE"
]
# Map crimes to categories
crime_categories = {
    "Violent Crimes": violent_crimes,
    "Property Crimes": property_crimes,
    "Cyber/White-Collar Crimes": cyber_white_collar_crimes,
    "Miscellaneous/Other Crimes": miscellaneous_crimes  # Combined category
}

def map_category(crime_desc):
    for category, crimes in crime_categories.items():
        if crime_desc in crimes:
            return category
    return "Miscellaneous/Other Crimes"  # Default to combined category

# Apply category mapping
crime_data["Category"] = crime_data["crm_cd_desc"].apply(map_category)
# Sidebar Filters
st.sidebar.header("Filters")

def multiselect_with_summary(label, options, default):
    selected = st.sidebar.multiselect(label, options, default=default)
    if not selected:
        st.sidebar.warning(f"No {label} selected. Please select at least one option.")
    return selected

# Generate filter options
crime_types = multiselect_with_summary(
    "Select Crime Types", sorted(crime_data['crm_cd_desc'].unique()), sorted(crime_data['crm_cd_desc'].unique())
)

victim_sex = multiselect_with_summary(
    "Victim Gender", sorted(crime_data['vict_sex'].unique()), sorted(crime_data['vict_sex'].unique())
)

victim_descent = multiselect_with_summary(
    "Select Victim Descent", sorted(crime_data['vict_descent'].unique()), sorted(crime_data['vict_descent'].unique())
)

victim_age_range = st.sidebar.slider(
    "Victim Age Range", int(crime_data['vict_age'].min()), int(crime_data['vict_age'].max()),
    (int(crime_data['vict_age'].min()), int(crime_data['vict_age'].max()))
)

area_name = multiselect_with_summary(
    "Area Name", sorted(crime_data['area_name'].unique()), sorted(crime_data['area_name'].unique())
)

start_date = st.sidebar.date_input("Start Date", value=crime_data['date_occ'].min())
end_date = st.sidebar.date_input("End Date", value=crime_data['date_occ'].max())

if start_date > end_date:
    st.error("Start Date cannot be after End Date")

# Apply Filters to Data
filtered_data = crime_data[
    (crime_data['crm_cd_desc'].isin(crime_types)) &
    (crime_data['vict_sex'].isin(victim_sex)) &
    (crime_data['vict_descent'].isin(victim_descent)) &
    (crime_data['vict_age'].between(*victim_age_range)) &
    (crime_data['area_name'].isin(area_name)) &
    (crime_data['date_occ'] >= pd.Timestamp(start_date)) &
    (crime_data['date_occ'] <= pd.Timestamp(end_date))
]

# Add the 'week' column for weekly trends
filtered_data['week'] = filtered_data['date_occ'].dt.to_period('W').apply(lambda r: r.start_time)



if filtered_data.empty:
    st.warning("No data available for the selected filters. Please adjust your filters.")
else:
    # Layout
    st.title("Los Angeles Crime Dashboard")

    # Key Performance Indicators
    st.subheader("Key Performance Indicators")
    total_crimes = filtered_data.shape[0]
    category_counts = filtered_data["Category"].value_counts()
    
    # Total Crimes KPI
    st.markdown(f"<h3 style='text-align: center;'>Total Crimes: {total_crimes}</h3>", unsafe_allow_html=True)
    
    # Individual Category KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        if "Violent Crimes" in category_counts:
            st.metric(label="Violent Crimes", value=category_counts["Violent Crimes"])
    with col2:
        if "Property Crimes" in category_counts:
            st.metric(label="Property Crimes", value=category_counts["Property Crimes"])
    with col3:
        if "Cyber/White-Collar Crimes" in category_counts:
            st.metric(label="Cyber/White-Collar Crimes", value=category_counts["Cyber/White-Collar Crimes"])
    
    col4, _ = st.columns(2)
    with col4:
        if "Miscellaneous/Other Crimes" in category_counts:
            st.metric(label="Miscellaneous/Other Crimes", value=category_counts["Miscellaneous/Other Crimes"])



    # Heatmap and Other Visualizations
    heat_data = filtered_data[['lat', 'lon']].dropna().values.tolist()
    la_map = folium.Map(location=[34.05, -118.25], zoom_start=11)
    HeatMap(heat_data, radius=8, blur=10).add_to(la_map)
    st_folium(la_map)

    
    # Calendar Heatmap
    st.write("Calendar Heatmap of Crime Counts")
    calendar_counts = filtered_data.groupby(filtered_data['date_occ'].dt.date).size().sort_index()
    calendar_counts.index = pd.to_datetime(calendar_counts.index)

    fig_calendar, ax_calendar = calplot.calplot(
        calendar_counts,
        cmap='viridis'
    )
    st.pyplot(fig_calendar)

    # Crime Type Breakdown Bar Chart
    crime_breakdown = filtered_data["crm_cd_desc"].value_counts().reset_index()
    crime_breakdown.columns = ["Crime Type", "Count"]
    fig_crime_type = px.bar(
        crime_breakdown,
        x="Crime Type",
        y="Count",
        title="Crime Type Distribution",
        labels={"Crime Type": "Type of Crime", "Count": "Number of Crimes"}
    )
    st.plotly_chart(fig_crime_type, use_container_width=True)

    # Victim Gender Distribution Pie Chart
    victim_gender_dist = filtered_data['vict_sex'].value_counts().reset_index()
    victim_gender_dist.columns = ["Gender", "Count"]
    fig_gender_pie = px.pie(
        victim_gender_dist,
        names="Gender",
        values="Count",
        title="Victim Gender Distribution"
    )
    st.plotly_chart(fig_gender_pie, use_container_width=True)

    # Victim Age Group Pie Chart
    age_bins = [0, 18, 30, 45, 60, 100]
    age_labels = ['0-18', '19-30', '31-45', '46-60', '61+']
    filtered_data['age_group'] = pd.cut(filtered_data['vict_age'], bins=age_bins, labels=age_labels)
    age_dist = filtered_data['age_group'].value_counts().reset_index()
    age_dist.columns = ["Age Group", "Count"]
    fig_age_pie = px.pie(
        age_dist,
        names="Age Group",
        values="Count",
        title="Victim Age Distribution"
    )
    st.plotly_chart(fig_age_pie, use_container_width=True)

    # Victim Descent Distribution Bar Chart
    descent_dist = filtered_data['vict_descent'].value_counts().reset_index()
    descent_dist.columns = ["Descent", "Count"]

    fig_descent_bar = px.bar(
        descent_dist,
        x="Descent",
        y="Count",
        title="Victim Descent Distribution",
        labels={"Descent": "Descent", "Count": "Number of Victims"}
    )
    st.plotly_chart(fig_descent_bar, use_container_width=True)

    # Time-Series Plot for Monthly Trends by Crime Type
    st.subheader("Time-Series: Monthly Trends by Crime Type")
    selected_crime_types = st.multiselect(
        "Select Crime Type for Time-Series Plot",
        options=crime_types,
        default=crime_types[:5] if len(crime_types) > 5 else crime_types
    )

    crime_trends_by_type = filtered_data.groupby(
        [filtered_data['date_occ'].dt.to_period("M"), 'crm_cd_desc']
    ).size().reset_index(name="Count")
    crime_trends_by_type['date_occ'] = crime_trends_by_type['date_occ'].dt.to_timestamp()

    if "All" not in selected_crime_types:
        crime_trends_by_type = crime_trends_by_type[
            crime_trends_by_type["crm_cd_desc"].isin(selected_crime_types)
        ]

    fig_trends_by_type = px.line(
        crime_trends_by_type,
        x="date_occ",
        y="Count",
        color="crm_cd_desc",
        title="Monthly Crime Trends by Type",
        labels={"date_occ": "Date", "Count": "Number of Crimes", "crm_cd_desc": "Crime Type"}
    )
    st.plotly_chart(fig_trends_by_type, use_container_width=True)

    # Weekly Crime Trends by Crime Type
    st.subheader("Weekly Crime Trends by Type")
    weekly_crime_trends = filtered_data.groupby(
        [filtered_data["week"], "crm_cd_desc"]
    ).size().reset_index(name="Count")

    selected_crime_types = st.multiselect(
        "Select Crime Type for Weekly Trends",
        options=["All"] + list(filtered_data["crm_cd_desc"].unique()),
        default=["All"]
    )

    if "All" not in selected_crime_types:
        weekly_crime_trends = weekly_crime_trends[
            weekly_crime_trends["crm_cd_desc"].isin(selected_crime_types)
        ]

    fig_weekly_trends_by_type = px.line(
        weekly_crime_trends,
        x="week",
        y="Count",
        color="crm_cd_desc",
        title="Weekly Crime Trends by Type",
        labels={"week": "Week", "Count": "Number of Crimes", "crm_cd_desc": "Crime Type"}
    )
    st.plotly_chart(fig_weekly_trends_by_type, use_container_width=True)



    # Clustered Crime Map with Stratified Sampling
    st.subheader("Clustered Crime Map (Stratified Sampling)")

    # Define maximum number of points for sampling
    max_points = 100000
    crime_column = 'crm_cd_desc'

    if len(filtered_data) > max_points:
        # Stratified Sampling
        stratified_sample = (
            filtered_data.groupby(crime_column, group_keys=False)
            .apply(lambda x: x.sample(frac=min(1, max_points / len(filtered_data)), random_state=42))
        )
        st.warning(f"Rendering a stratified sample of {len(stratified_sample)} points out of {len(filtered_data)} total.")
    else:
        stratified_sample = filtered_data

    # Generate clustered crime map
    cluster_map = folium.Map(location=[34.05, -118.25], zoom_start=11)
    marker_cluster = MarkerCluster().add_to(cluster_map)

    for idx, row in stratified_sample.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=f"{row['crm_cd_desc']} ({row['date_occ'].date()})"
        ).add_to(marker_cluster)

    st_folium(cluster_map)

    st.success("Dashboard Rendered Successfully!")
    