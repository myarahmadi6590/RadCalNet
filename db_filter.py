import streamlit as st
import datetime

def filter_condition(sites_config, sensors_config):
    st.header("Plot Settings")
    overall_condition = {"start_date": str(st.date_input("Start Date", value=datetime.date(2013, 1, 1))),
                         "end_date": str(st.date_input("End Date", value=datetime.date.today())),
                         "time_diff": st.number_input("Max Time Difference (s)", value=900, step=100),
                         "VZA": st.number_input("Sensor View Angle Threshold", value=90),
                         "sites": sorted(st.multiselect("Select Sites", list(sites_config.keys()), default=["RVUS", "GONA"])),
                         "sensors": sorted(st.multiselect("Select sensors", list(sensors_config.keys()), default=["LANDSAT8_OLI", "LANDSAT9_OLI"])),
                         "remove_outliers": st.checkbox("Remove Outliers", value=False)}
    
    st.subheader("Site Conditions")
    st.markdown("Define acceptable conditions **at the site location** (%).")
    site_conditions = {}
    site_col1, site_col2 = st.columns(2)
    with site_col1:
        clear_min = st.number_input(
            "Minimum clear (%)",
            min_value=0,
            max_value=100,
            value=100,
            step=1,
            key="site_clear_min"
        )
        site_conditions["clear"] = (clear_min, 100)
    with site_col2:
        cloud_max = st.number_input(
            "Maximum cloud (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            key="site_cloud_max"
        )
        site_conditions["cloud"] = (0, cloud_max)
        
    st.subheader("Atmospheric Conditions")
    st.markdown("Specify the range of acceptable values for atmospheric parameters.")
    atm_conditions = {}
    atm_cfg = {"P": (0, 1100, (650, 1050), 1),
               "T": (230, 400, (250, 370), 1),
               "WV": (0.0, 10.0, (0.0, 10.0), 0.1),
               "O3": (-500, 500, (-490, 490), 1),
               "AOD": (0.0, 2.0, (0.0, 1.9), 0.1),
               "Ang": (0.0, 4.0, (0.0, 4.0), 0.1)
               }
    atm_col1, atm_col2, atm_col3 = st.columns(3)
    atm_cols = [atm_col1, atm_col2, atm_col3]
    for i, (k, (min_v, max_v, val, step)) in enumerate(atm_cfg.items()):
        with atm_cols[i % 3]:
            atm_conditions[k] = st.slider(k, min_v, max_v, val, step=step, key=k)

    return {**overall_condition, 'site_conditions': site_conditions, 'atm_conditions': atm_conditions}