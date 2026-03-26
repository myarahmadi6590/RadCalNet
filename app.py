import os, warnings, sys
import streamlit as st
warnings.filterwarnings("ignore")
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, "/home/myarahma")


from get_config   import get_config
from db_setup     import setup_page
from db_filter    import filter_condition
from db_functions import get_dataframes, excel_save
from db_plot      import show_image, get_plot_style, polar_angle_plot, plot_matchup_count, plot_mean_ratio_per_instrument, plot_mean_ratio_per_site, time_series_plot

sites_config, sensors_config = get_config()
setup_page()
left_sidebar, mainbar, right_sidebar = st.columns([1, 3, 1])
with left_sidebar: condition = filter_condition(sites_config, sensors_config)
df_dct, stat_dct = get_dataframes(sites_config, sensors_config, condition)
with left_sidebar: excel_save(df_dct)
with right_sidebar: sensor_colors, site_symbols = get_plot_style(df_dct)
with right_sidebar: plot_matchup_count(stat_dct, sensor_colors)
with right_sidebar: show_image (sites_config, sensors_config, condition, df_dct)
with left_sidebar: polar_angle_plot(df_dct, sensor_colors)
with mainbar: plot_mean_ratio_per_instrument(stat_dct, sensors_config, sensor_colors)
with mainbar: plot_mean_ratio_per_site(stat_dct, sensors_config, site_symbols)

with mainbar: time_series_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols)
# with mainbar: intercomparison_plot (df_dct, plot_config, stat_dct)


# # from update import update
# from get_config import get_config

# from panel_functions import plot_settings, filter_conditions, plot_rsr, polar_angle_plot, intercomparison_plot, time_series_plot, mean_plot, sensitivity_plot, export_excel
# from panel_functions import show_image
# from functions import get_dataframes

# PLANET_TOA_instruments_config, GEE_TOA_instruments_config, NSD_TOA_instruments_config, USGSEE_TOA_instruments_config, sites_config, plot_config = get_config()
# instruments_config = {**NSD_TOA_instruments_config, **GEE_TOA_instruments_config}





# left_sidebar, mainbar, right_sidebar = st.columns([1, 3, 1])

# with left_sidebar: condition_1 = plot_settings(plot_config, sites_config, instruments_config)
# with right_sidebar: condition_2 = filter_conditions()
# condition = {**condition_1, **condition_2}
# df_dct, stat_dct = get_dataframes(instruments_config, plot_config, condition)
# with left_sidebar: export_excel(df_dct)
# with left_sidebar: plot_rsr(instruments_config, plot_config, condition)
# with right_sidebar: show_image (df_dct, condition, instruments_config)
# with left_sidebar: polar_angle_plot(df_dct)
# with mainbar: intercomparison_plot (df_dct, plot_config, stat_dct)
# with mainbar: time_series_plot(df_dct, plot_config, condition)
# with mainbar: mean_plot (plot_config, condition, stat_dct)
# with mainbar: sensitivity_plot(df_dct, plot_config, condition)