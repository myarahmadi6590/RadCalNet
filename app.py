import os, warnings
import streamlit as st
warnings.filterwarnings("ignore")
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from get_config      import get_config
from db_authenticate import check_password
from db_setup        import setup_page
from db_filter       import filter_condition
from db_functions    import get_dataframes
from db_plot         import show_image, get_plot_style, polar_angle_plot, plot_matchup_count, plot_mean_ratio_per_instrument, plot_mean_ratio_per_site, time_series_plot

if not check_password():
    st.stop()

sites_config, sensors_config = get_config()
setup_page()
left_sidebar, mainbar, right_sidebar = st.columns([1, 3, 1])
with left_sidebar: condition = filter_condition(sites_config, sensors_config)
df_dct, stat_dct = get_dataframes(sites_config, sensors_config, condition)
with right_sidebar: sensor_colors, site_symbols = get_plot_style(df_dct)
with right_sidebar: plot_matchup_count(stat_dct, sensor_colors)
with right_sidebar: show_image (sites_config, sensors_config, condition, df_dct)
with left_sidebar: polar_angle_plot(df_dct, sensor_colors)
with mainbar: plot_mean_ratio_per_instrument(stat_dct, sensors_config, sensor_colors)
with mainbar: plot_mean_ratio_per_site(stat_dct, sensors_config, site_symbols)
with mainbar: time_series_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols)