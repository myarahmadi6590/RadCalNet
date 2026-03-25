import os, warnings, sys
import streamlit as st
warnings.filterwarnings("ignore")
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, "/home/myarahma")


from get_config   import get_config
from db_setup     import setup_page
from db_filter    import filter_condition
from db_functions import get_dataframes, excel_save
from db_plot      import show_image, get_plot_style, polar_angle_plot, time_series_plot

sites_config, sensors_config = get_config()
setup_page()
left_sidebar, mainbar, right_sidebar = st.columns([1, 3, 1])
with left_sidebar: condition = filter_condition(sites_config, sensors_config)
df_dct = get_dataframes(sites_config, sensors_config, condition)
with left_sidebar: excel_save(df_dct)
with mainbar: sensor_colors, site_symbols = get_plot_style(df_dct)
with right_sidebar: show_image (sites_config, sensors_config, condition, df_dct)
with left_sidebar: polar_angle_plot(df_dct)
with mainbar: time_series_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols)
