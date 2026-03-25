import streamlit as st
from pathlib import Path
from PIL import Image
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from collections import defaultdict
import pandas as pd

background_color = '#f5f5f5'
tick_font = dict(size=20, color='black')
axis_font = dict(size=30, color='black')
legend_font = dict(size=16, color='black')

def show_image (sites_config, sensors_config, condition, df_dct, mode = 'SensorToGroundComparison'): 
    base_dir = Path(__file__).resolve().parent / "Database" / "Sites" 
    st.markdown("<h2 style='text-align: center;'>Observation Details</h2>", unsafe_allow_html=True)
    sensor = st.selectbox("Select Sensor", list(df_dct.keys()))
    site = st.selectbox("Select Site", list(df_dct[sensor].keys()))
    df = df_dct[sensor][site]
    df['datetime_str'] = df['date'].astype(str) + ' ' + df['sens_time'].astype(str)
    df['date_sens_id'] = df['date'].astype(str) + '_' + df['sens_id'].astype(str)
    datetime_list = df['datetime_str'].tolist()
    sens_datetime_str = st.selectbox("Select Scene Date & Time", datetime_list, index=len(datetime_list) - 1)
    row = df[df['datetime_str'] == sens_datetime_str]
    date_sens_id = row.iloc[0]['date_sens_id']
    img_path = base_dir / sites_config[site]["network"] / site / mode / sensor / "Images" / f"{date_sens_id}.png"
    image = Image.open(img_path)
    st.image(image, caption=f'{sensor}', use_container_width=True)

def polar_angle_plot(df_dct):
    st.markdown("<h2 style='text-align: center;'>View and Sun Angles</h2>", unsafe_allow_html=True)
    sensors = list(df_dct.keys())
    num_sensors = len(sensors)
    num_cols = 2
    num_rows = (num_sensors + 1) // num_cols  # round up

    fig = make_subplots(
        rows=num_rows, cols=num_cols,
        specs=[[{'type': 'polar'}] * num_cols for _ in range(num_rows)],
        subplot_titles=sensors,
        horizontal_spacing=0.05,
        vertical_spacing=0.1
    )

    for idx, inst in enumerate(sensors):
        row = idx // num_cols + 1
        col = idx % num_cols + 1
        vza, vaa, sza, saa = [], [], [], []
        for site_df in df_dct[inst].values():
            if not site_df.empty:
                vza.extend(site_df.get('VZA', []))
                vaa.extend(site_df.get('VAA', []))
                sza.extend(site_df.get('SZA', []))
                saa.extend(site_df.get('SAA', []))

        # View angle (blue)
        fig.add_trace(go.Scatterpolar(
            r=vza,
            theta=vaa,
            mode='markers',
            marker=dict(color='blue', size=5),
            showlegend=(False),
            name="View Angles"
        ), row=row, col=col)

        # Sun angle (red)
        fig.add_trace(go.Scatterpolar(
            r=sza,
            theta=saa,
            mode='markers',
            marker=dict(color='red', size=5),
            showlegend=(False),
            name="Sun Angles"
        ), row=row, col=col)

        fig.update_polars(
            dict(
                bgcolor=background_color,
                radialaxis=dict(
                    range=[0, 80],
                    showline=True,
                    linecolor='black',
                    gridcolor='lightgray',
                    tickfont=tick_font
                ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,
                    linecolor='black',
                    gridcolor='lightgray',
                    tickfont=tick_font
                )
            ),
            row=row,
            col=col
        )

    fig.update_layout(
        height=300 * num_rows,
        margin=dict(t=30, b=30, r=30, l=30),
        paper_bgcolor=background_color,
        plot_bgcolor=background_color,
        font=axis_font,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(240, 240, 240, 0.5)',
            font=legend_font
        )
    )
    st.plotly_chart(fig, use_container_width=True)

def time_series_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols):
    bands = get_bands(sensors_config)

    st.markdown("<h2 style='text-align: center;'>Time Series</h2>", unsafe_allow_html=True)    
    col1, col2 = st.columns(2)
    with col1: metric = st.selectbox("Select the metric", ["ratio", "sens_refl", "rcn_refl"], index=0)
    with col2: band = st.selectbox("Select the band", bands, index=0)
        
    fig = go.Figure()

    for sensor, site_dct in df_dct.items():
        for site, df in site_dct.items():
            label = next(
                (
                    f"{bid}_{b['name']}_{b['cw']}nm"
                    for bid, b in sensors_config[sensor]['bands'].items()
                    if b['name'] == band
                ),
                None
            )

            if not label: continue

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df[f'{metric}_{label}'],
                mode='markers',
                name=f"{sensor} @ {site}",
                marker=dict(
                    size=15,
                    color=sensor_colors.get(sensor, "#1f77b4"),
                    symbol=site_symbols.get(site, "circle"),
                    line=dict(color='gold', width=1)
                ),
                opacity=1.0,
                customdata=df[[
                    'sens_id',
                    f'sens_refl_{label}',
                    f'rcn_refl_{label}',
                    f'ratio_{label}',
                    'P', 'T', 'WV', 'O3', 'AOD', 'Ang', 'VZA'
                ]],
                hovertemplate=(
                    "<b>Date:</b> %{x|%Y-%m-%d}<br>" +
                    "<b>ID:</b> %{customdata[0]}<br>" +
                    "<b>Sensor Reflectance:</b> %{customdata[1]:.4f}<br>" +
                    "<b>RCN Reflectance:</b> %{customdata[2]:.4f}<br>" +
                    "<b>Ratio:</b> %{customdata[3]:.4f}<br>" +
                    "<b>P:</b> %{customdata[4]:.2f}<br>" +
                    "<b>T:</b> %{customdata[5]:.2f}<br>" +
                    "<b>WV:</b> %{customdata[6]:.2f}<br>" +
                    "<b>O₃:</b> %{customdata[7]:.2f}<br>" +
                    "<b>AOD:</b> %{customdata[8]:.2f}<br>" +
                    "<b>Ångström:</b> %{customdata[9]:.2f}<br>" +
                    "<b>View Angle:</b> %{customdata[10]:.2f}<br>"
                ),
                legendgroup=f"sensor_{sensor}",
                showlegend=True
            ))

    if metric == "ratio":
        fig.add_shape(
            type='line',
            x0=0, x1=1, xref='x domain',
            y0=1, y1=1, yref='y',
            line=dict(color='red', dash='dash')
        )
    
    all_dates = [df['date'] for site_dct in df_dct.values() for df in site_dct.values()]
    all_dates = pd.concat(all_dates)
    all_dates = pd.to_datetime(all_dates)
    min_date = all_dates.min()
    max_date = all_dates.max()
    x_min_extended = min_date - pd.DateOffset(months=3)
    x_max_extended = max_date + pd.DateOffset(months=15)
    
    fig.update_layout(
        xaxis=dict(
            title=dict(text='Date', font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor='black',
            range=[x_min_extended, x_max_extended],
            type='date'
        ),
        yaxis=dict(
            title=dict(text=f'{metric}', font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor='black'
        ),
        margin=dict(t=0, b=0, r=0, l=0),
        height=1000,
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="right",
            x=1,
            groupclick="toggleitem",
            borderwidth=1,
            font=legend_font,
            bgcolor='rgba(240, 240, 240, 0.5)',
        ),
        plot_bgcolor=background_color,
    )

    st.plotly_chart(fig, use_container_width=True)
    return fig

def get_bands(sensors_config):
    cw_by_band = defaultdict(list)
    for sensor in sensors_config.values():
        for band in sensor['bands'].values():
            cw_by_band[band['name']].append(band['cw'])
            
    avg_cw = {band_name: sum(cws) / len(cws) for band_name, cws in cw_by_band.items()}
    sorted_band_names = sorted(avg_cw, key=lambda b: avg_cw[b])
    return sorted_band_names

def get_plot_style(df_dct):
    """
    Build Streamlit controls for sensor colors and site symbols.

    Returns
    -------
    sensor_colors : dict
        {sensor: color_hex}
    site_symbols : dict
        {site: plotly_marker_symbol}
    """
    sensors = list(df_dct.keys())
    sites = sorted(
        {
            site
            for _, site_dct in df_dct.items()
            for site in site_dct.keys()
        }
    )

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    marker_symbol_options = [
        "circle", "square", "diamond", "cross", "x",
        "triangle-up", "triangle-down", "triangle-left", "triangle-right",
        "pentagon", "hexagon", "star", "hourglass", "bowtie"
    ]

    sensor_color_defaults = {
        sensor: default_colors[i % len(default_colors)]
        for i, sensor in enumerate(sensors)
    }

    site_symbol_defaults = {
        site: marker_symbol_options[i % len(marker_symbol_options)]
        for i, site in enumerate(sites)
    }

    st.markdown("### Plot style")

    st.markdown("#### Instrument colors")
    sensor_colors = {}
    color_cols = st.columns(min(8, max(1, len(sensors))))
    for i, sensor in enumerate(sensors):
        with color_cols[i % len(color_cols)]:
            sensor_colors[sensor] = st.color_picker(
                f"{sensor}",
                value=sensor_color_defaults[sensor],
                key=f"color_{sensor}"
            )

    st.markdown("#### Site marker symbols")
    site_symbols = {}
    symbol_cols = st.columns(min(8, max(1, len(sites))))
    for i, site in enumerate(sites):
        with symbol_cols[i % len(symbol_cols)]:
            default_idx = marker_symbol_options.index(site_symbol_defaults[site])
            site_symbols[site] = st.selectbox(
                f"{site}",
                marker_symbol_options,
                index=default_idx,
                key=f"symbol_{site}"
            )

    return sensor_colors, site_symbols