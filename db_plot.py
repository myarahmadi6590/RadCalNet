import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from collections import defaultdict
import pandas as pd
import numpy as np
from matplotlib.colors import ListedColormap
from pathlib import Path
from PIL import Image

background_color = '#f5f5f5'
tick_font = dict(size=20, color='black')
axis_font = dict(size=30, color='black')
legend_font = dict(size=16, color='black')

# Remove Plotly's screenshot / save-image button
PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["toImage"],
}

def add_watermark(fig, text=""):
    fig.add_annotation(
        text=text,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        textangle=-35,
        font=dict(
            size=120,
            color="rgba(80,80,80,0.35)",
            family="Arial Black"
        ),
        align="center",
    )

def show_image (sites_config, condition, df_dct, mode = 'SensorToGroundComparison'): 
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

def polar_angle_plot(df_dct, sensor_colors):
    st.markdown("<h2 style='text-align: center;'>View and Sun Angles</h2>", unsafe_allow_html=True)

    sensors = list(df_dct.keys())
    num_sensors = len(sensors)
    num_cols = 3
    num_rows = (num_sensors + num_cols - 1) // num_cols

    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        specs=[[{'type': 'polar'}] * num_cols for _ in range(num_rows)],
        horizontal_spacing=0.08,
        vertical_spacing=0.12
    )

    def hex_to_rgba(hex_color, alpha=0.35):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"rgba(200,200,200,{alpha})"
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    for idx, sensor in enumerate(sensors):
        row = idx // num_cols + 1
        col = idx % num_cols + 1

        vza, vaa, sza, saa = [], [], [], []
        for site_df in df_dct[sensor].values():
            if not site_df.empty:
                vza.extend(site_df.get("VZA", []))
                vaa.extend(site_df.get("VAA", []))
                sza.extend(site_df.get("SZA", []))
                saa.extend(site_df.get("SAA", []))

        sensor_bg = hex_to_rgba(sensor_colors.get(sensor, "#cccccc"))

        fig.add_trace(
            go.Scatterpolar(
                r=vza,
                theta=vaa,
                mode="markers",
                marker=dict(color="blue", size=5, opacity=0.85),
                name="View Angles",
                legendgroup="view_angles",
                showlegend=(idx == 0)
            ),
            row=row,
            col=col
        )

        fig.add_trace(
            go.Scatterpolar(
                r=sza,
                theta=saa,
                mode="markers",
                marker=dict(color="#b8860b", size=5, opacity=0.9),
                name="Sun Angles",
                legendgroup="sun_angles",
                showlegend=(idx == 0)
            ),
            row=row,
            col=col
        )

        fig.update_polars(
            dict(
                bgcolor=sensor_bg,
                radialaxis=dict(
                    range=[0, 80],
                    tickvals=[0, 20, 40, 60, 80],
                    tickfont=dict(size=10),
                    gridcolor="#bfbfbf",
                    gridwidth=1.5,
                    linecolor="#666",
                    linewidth=1.2,
                    showline=True
                ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,
                    tickfont=dict(size=11),
                    gridcolor="#bfbfbf",
                    gridwidth=1.5,
                    linecolor="#666",
                    linewidth=1.2,
                    showline=True
                )
            ),
            row=row,
            col=col
        )

        # Add sensor label below each subplot
        fig.add_annotation(
            text=sensor,
            x=(col - 0.5) / num_cols,
            y=1 - (row / num_rows) - 0.1,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14),
            xanchor="center",
            yanchor="top"
        )
        
        

    fig.update_layout(
        height=320 * num_rows,
        margin=dict(t=80, b=60, r=20, l=20),
        paper_bgcolor=background_color,
        plot_bgcolor=background_color,
        font=dict(size=12),
        legend=dict(
            orientation="h",
            x=0.5,
            y=1.15,
            xanchor="center",
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="lightgray",
            borderwidth=1,
            font=legend_font
        )
    )

    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def _get_plot_band_colors(sensors_config):
    bands, band_colors_raw = get_bands(sensors_config)
    band_colors = {
        band: f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{a})"
        for band, (r, g, b, a) in band_colors_raw.items()
    }
    return bands, band_colors


def _compute_band_stats(stat_dct, bands, group_by="instrument"):
    instruments = list(stat_dct.keys())
    sites = list(next(iter(stat_dct.values())).keys())

    if group_by == "instrument":
        outer_items = instruments
        inner_items = sites
    else:
        outer_items = sites
        inner_items = instruments

    band_stats = {}

    for band in bands:
        means_dict, stds_dict = {}, {}

        for outer in outer_items:
            stats_list = []

            for inner in inner_items:
                inst, site = (outer, inner) if group_by == "instrument" else (inner, outer)
                band_data = stat_dct[inst][site].get(band)

                if band_data is None:
                    continue

                overall = band_data["overall"]
                stats_list.append((
                    overall["mean_ratio"],
                    overall["std_ratio"],
                    overall["num_acquisitions"],
                ))

            mean, std = combine_mean_std(stats_list) if stats_list else (np.nan, np.nan)
            means_dict[outer] = mean
            stds_dict[outer] = std

        band_stats[band] = {
            "means": means_dict,
            "stds": stds_dict,
        }

    return band_stats


def _add_band_backgrounds(fig, bands, band_colors, opacity=0.25):
    for i, band in enumerate(bands):
        fig.add_shape(
            type="rect",
            x0=i - 0.5,
            x1=i + 0.5,
            y0=0,
            y1=1,
            xref="x",
            yref="y domain",
            fillcolor=band_colors[band],
            opacity=opacity,
            line=dict(width=0),
            layer="below",
        )


def plot_matchup_count(stat_dct, sensor_colors):
    st.markdown("<h2 style='text-align: center;'>Overpass Matchup Summary</h2>", unsafe_allow_html=True)

    sensors = list(stat_dct.keys())
    sites = list(next(iter(stat_dct.values())).keys())

    fig = go.Figure()

    for site in sites:
        counts = []
        for sensor in sensors:
            first_band = next(iter(stat_dct[sensor][site]))
            count = stat_dct[sensor][site][first_band]["overall"]["num_acquisitions"]
            counts.append(count)

        color_list = [sensor_colors.get(sensor, "gray") for sensor in sensors]

        fig.add_trace(
            go.Bar(
                x=sensors,
                y=counts,
                name=site,
                text=[site] * len(sensors),
                textposition="outside",
                marker=dict(
                    color=color_list,
                    line=dict(color='black', width=2),
                ),
                showlegend=False,
                textfont=dict(color='black'),
            )
        )

    fig.update_layout(
        barmode="group",
        height=500,
        hovermode="closest",
        margin=dict(t=40, b=0, r=0, l=0),
        xaxis=dict(
            title=dict(text="Instrument", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
        ),
        yaxis=dict(
            title=dict(text="Matchup Count", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
        ),
    )
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def plot_mean_ratio_per_instrument(stat_dct, sensors_config, sensor_colors, offset_scale=0.1):
    sensors_config = {k: v for k, v in sensors_config.items() if k in stat_dct}
    st.markdown("<h2 style='text-align: center;'>Intercomparison Summary</h2>", unsafe_allow_html=True)
    instruments = list(stat_dct.keys())
    bands, band_colors = _get_plot_band_colors(sensors_config)
    band_stats = _compute_band_stats(stat_dct, bands, group_by="instrument")

    fig = go.Figure()
    _add_band_backgrounds(fig, bands, band_colors, opacity=0.35)

    n_inst = len(instruments)

    for j, inst in enumerate(instruments):
        offset = (j - (n_inst - 1) / 2) * offset_scale
        x_vals = [i + offset for i in range(len(bands))]
        y_vals = [band_stats[band]["means"].get(inst, np.nan) for band in bands]
        err_vals = [band_stats[band]["stds"].get(inst, np.nan) for band in bands]

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                error_y=dict(type="data", array=err_vals, visible=True),
                mode="markers",
                name=inst,
                marker=dict(
                    size=11,
                    color=sensor_colors.get(inst, "gray"),
                    symbol="circle",
                    line=dict(color="black", width=1),
                ),
            )
        )

    fig.add_hline(y=1, line_dash="dash", line_color="red")

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(bands))),
        ticktext=bands,
        title_text="Band",
    )

    fig.update_layout(
        height=500,
        hovermode="closest",
        margin=dict(t=40, b=0, r=0, l=0),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="right",
            x=0.99,
            groupclick="toggleitem",
            borderwidth=1,
            font=legend_font,
            bgcolor="rgba(240, 240, 240, 0.5)",
            title=dict(text="<b>Instruments</b>"),
        ),
        xaxis=dict(
            title=dict(text="Band", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
            range=[min(x_vals) - 1, max(x_vals) + 1.5],
        ),
        yaxis=dict(
            title=dict(text="Mean Ratio per Instrument", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
        ),
    )
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def plot_mean_ratio_per_site(stat_dct, sensors_config, site_symbols, offset_scale=0.1):
    sensors_config = {k: v for k, v in sensors_config.items() if k in stat_dct}
    sites = list(next(iter(stat_dct.values())).keys())
    bands, band_colors = _get_plot_band_colors(sensors_config)
    band_stats = _compute_band_stats(stat_dct, bands, group_by="site")

    fig = go.Figure()
    _add_band_backgrounds(fig, bands, band_colors, opacity=0.35)

    n_sites = len(sites)

    for j, site in enumerate(sites):
        offset = (j - (n_sites - 1) / 2) * offset_scale
        x_vals = [i + offset for i in range(len(bands))]
        y_vals = [band_stats[band]["means"].get(site, np.nan) for band in bands]
        err_vals = [band_stats[band]["stds"].get(site, np.nan) for band in bands]

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                error_y=dict(type="data", array=err_vals, visible=True),
                mode="markers",
                name=site,
                marker=dict(
                    size=11,
                    color="gray",
                    symbol=site_symbols.get(site, "circle"),
                    line=dict(color="black", width=1),
                ),
            )
        )

    fig.add_hline(y=1, line_dash="dash", line_color="red")

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(bands))),
        ticktext=bands,
        title_text="Band",
    )

    fig.update_layout(
        height=500,
        hovermode="closest",
        margin=dict(t=40, b=0, r=0, l=0),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="right",
            x=0.99,
            groupclick="toggleitem",
            borderwidth=1,
            font=legend_font,
            bgcolor="rgba(240, 240, 240, 0.5)",
            title=dict(text="<b>Sites</b>"),
        ),
        xaxis=dict(
            title=dict(text="Band", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
            range=[min(x_vals) - 1, max(x_vals) + 1.5],
        ),
        yaxis=dict(
            title=dict(text="Mean Ratio per Site", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor="black",
        ),
    )
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def time_series_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols):
    sensors_config = {k: v for k, v in sensors_config.items() if k in df_dct}
    bands, _ = get_bands(sensors_config)

    st.markdown("<h2 style='text-align: center;'>Time Series</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("Select the metric", ["ratio", "sens_refl", "rcn_refl"], index=0)
    with col2:
        band = st.selectbox("Select the band", bands, index=0)

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

            if not label:
                continue

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
                    "<b>Date:</b> %{x|%Y-%m-%d}<br>"
                    + "<b>ID:</b> %{customdata[0]}<br>"
                    + "<b>Sensor Reflectance:</b> %{customdata[1]:.4f}<br>"
                    + "<b>RCN Reflectance:</b> %{customdata[2]:.4f}<br>"
                    + "<b>Ratio:</b> %{customdata[3]:.4f}<br>"
                    + "<b>P:</b> %{customdata[4]:.2f}<br>"
                    + "<b>T:</b> %{customdata[5]:.2f}<br>"
                    + "<b>WV:</b> %{customdata[6]:.2f}<br>"
                    + "<b>O₃:</b> %{customdata[7]:.2f}<br>"
                    + "<b>AOD:</b> %{customdata[8]:.2f}<br>"
                    + "<b>Ångström:</b> %{customdata[9]:.2f}<br>"
                    + "<b>View Angle:</b> %{customdata[10]:.2f}<br>"
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
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    return

def average_plot (sensors_config, condition, stat_dct, sensor_colors):
    sensors_config = {k: v for k, v in sensors_config.items() if k in stat_dct}
    bands, _ = get_bands(sensors_config)
    st.markdown("<h2 style='text-align: center;'>Temporal Average Ratio Comparison</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_metric = st.selectbox(
            "Select the timestep",
            ["yearly", "monthly"],
            index=0,
            key="avg_time_metric"
        )
    
    with col2:
        site_metric = st.selectbox(
            "Select the site",
            ["combined sites"] + condition["sites"],
            index=0,
            key="avg_site_metric"
        )
    
    with col3:
        band = st.selectbox(
            "Select the band",
            bands,
            index=0,
            key="avg_band"
        )
    stat_dct = add_combined_sites(band, stat_dct)
    fig = go.Figure()
    for sensor in condition["sensors"]:
        try:
            df = stat_dct[sensor][site_metric][band][time_metric]
            if time_metric == "yearly": x = df['year']
            else:x = df['month'].dt.to_timestamp()
    
            fig.add_trace(go.Scatter(
                x=x,
                y=df['mean'],
                mode='lines+markers',
                name=f'{sensor}       ',
                marker=dict(
                    size=15,
                    color=sensor_colors.get(sensor, "#1f77b4"),
                    line=dict(color='gold', width=1)
                ),
                line=dict(width=3),
                error_y=dict(
                    type='data',
                    array=df['std'],
                    visible=True)))
        except: continue
    fig.update_layout(
        xaxis=dict(
            title=dict(text="Year" if time_metric == "yearly" else "Month", font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor='black',
        ),
        yaxis=dict(
            title=dict(text='Average Ratio', font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor='black'
        ),
        margin=dict(t=0, b=0, r=0, l=0),
        height=500,
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1,
            groupclick="toggleitem",
            borderwidth=1,
            font=legend_font,
            bgcolor='rgba(240, 240, 240, 0.5)',
        ),
        plot_bgcolor=background_color,
    )
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def sensitivity_plot(sensors_config, condition, df_dct, sensor_colors, site_symbols):
    sensors_config = {k: v for k, v in sensors_config.items() if k in df_dct}
    bands, _ = get_bands(sensors_config)
    st.markdown("<h2 style='text-align: center;'>Sensitivity Analysis</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        metric_1 = st.selectbox("Select the x axis", 
                                ["VZA", "VAA", "SZA", "SAA",
                                 "P", "T", "WV", "O3", "AOD", "Ang"] +
                                [f"Ratio {b}" for b in bands] + 
                                [f"Sensor Reflectance {b}" for b in bands] + 
                                [f"RadCalNet Reflectance {b}" for b in bands],
                                index=0)
    with col2:
        metric_2 = st.selectbox("Select the y axis", 
                                ["VZA", "VAA", "SZA", "SAA",
                                 "P", "T", "WV", "O3", "AOD", "Ang"] +
                                [f"Ratio {b}" for b in bands] + 
                                [f"Sensor Reflectance {b}" for b in bands] + 
                                [f"RadCalNet Reflectance {b}" for b in bands],
                                index=10)
    
    fig = go.Figure()

    for sensor, site_dct in df_dct.items():
        for site, df in site_dct.items():
            label1 = get_label(metric_1, sensors_config, sensor)
            label2 = get_label(metric_2, sensors_config, sensor)
            if not label1: continue
            if not label2: continue

            fig.add_trace(go.Scatter(
                x=df[label1],
                y=df[label2],
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
                    'date',
                    'sens_id',
                    'P', 'T', 'WV', 'O3', 'AOD', 'Ang', 'VZA'
                ]],
                hovertemplate=(
                    "<b>Date:</b> %{customdata[0]|%Y-%m-%d}<br>"
                    "<b>ID:</b> %{customdata[1]}<br>" +
                    "<b>P:</b> %{customdata[2]:.2f}<br>" +
                    "<b>T:</b> %{customdata[3]:.2f}<br>" +
                    "<b>WV:</b> %{customdata[4]:.2f}<br>" +
                    "<b>O₃:</b> %{customdata[5]:.2f}<br>" +
                    "<b>AOD:</b> %{customdata[6]:.2f}<br>" +
                    "<b>Ångström:</b> %{customdata[7]:.2f}<br>" +
                    "<b>View Angle:</b> %{customdata[8]:.2f}<br>"
                ),
                legendgroup=f"sensor_{sensor}",
                showlegend=True
            ))

    if 'Ratio' in metric_2:
        fig.add_shape(
            type='line',
            x0=0, x1=1, xref='x domain',
            y0=1, y1=1, yref='y1',
            line=dict(color='red', dash='dash')
        )
    
    fig.update_layout(
        xaxis=dict(
            title=dict(text=f'{metric_1}', font=axis_font),
            tickfont=tick_font,
            showgrid=True,
            zeroline=True,
            linecolor='black',
        ),
        yaxis=dict(
            title=dict(text=f'{metric_2}', font=axis_font),
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
            y=1,
            xanchor="right",
            x=1,
            groupclick="toggleitem",
            borderwidth=1,
            font=legend_font,
            bgcolor='rgba(240, 240, 240, 0.5)',
        ),
        plot_bgcolor=background_color,
    )
    add_watermark(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

def get_label(metric_str, sensors_config, sensor):
    mapping = {
        "Ratio ": "ratio",
        "Sensor Reflectance ": "sens_refl",
        "RadCalNet Reflectance ": "rcn_refl",
    }

    for prefix, metric in mapping.items():
        if metric_str.startswith(prefix):
            band = metric_str.replace(prefix, "")
            return next(
                (
                    f"{metric}_{bid}_{b['name']}_{b['cw']}nm"
                    for bid, b in sensors_config[sensor]['bands'].items()
                    if b['name'] == band
                ),
                None
            )
    return metric_str

def get_bands(sensors_config):
    cmap = create_wavelength_cmap()
    cw_by_band = defaultdict(list)
    for sensor in sensors_config.values():
        for band in sensor['bands'].values():
            cw_by_band[band['name']].append(band['cw'])
    avg_cw = {band: sum(cws) / len(cws) for band, cws in cw_by_band.items()}
    sorted_band_names = sorted(avg_cw, key=avg_cw.get)
    band_colors = {band: get_band_color(cmap, avg_cw[band]) for band in sorted_band_names}
    return sorted_band_names, band_colors


def get_band_color(cmap, wavelength, wl_min=400, wl_max=2500):
    x = (wavelength - wl_min) / (wl_max - wl_min)
    x = np.clip(x, 0, 1)
    return cmap(x)


def create_wavelength_cmap(wl_min=400, wl_max=2500, step=0.1):
    def vis_rgb(w):
        if w < 440:
            r, g, b = -(w - 440) / 40, 0, 1
        elif w < 490:
            r, g, b = 0, (w - 440) / 50, 1
        elif w < 510:
            r, g, b = 0, 1, -(w - 510) / 20
        elif w < 580:
            r, g, b = (w - 510) / 70, 1, 0
        elif w < 645:
            r, g, b = 1, -(w - 645) / 65, 0
        else:
            r, g, b = 1, 0, 0
        return tuple(c**0.8 for c in (r, g, b))

    def wl_rgb(w):
        if w <= 700:
            return vis_rgb(w)
        if w <= 1000:
            t = (w - 700) / 300
            return (1 - 0.5 * t, 0.2 - 0.1 * t, 0.6 + 0.2 * t)
        if w <= 1700:
            t = (w - 1000) / 700
            return (0.2, 0.7 + 0.1 * t, 0.9 - 0.5 * t)
        t = (w - 1700) / 800
        return (0.72 - 0.32 * t, 0.46 - 0.06 * t, 0.20 + 0.25 * t)

    wls = np.arange(wl_min, wl_max + step, step)
    return ListedColormap([wl_rgb(w) for w in wls], name="wavelength_cmap")


def combine_mean_std(stats_list):
    if len(stats_list) == 1:
        return stats_list[0][0], stats_list[0][1]

    stats_list = [
        (float(m), float(s), int(n))
        for m, s, n in stats_list
        if n > 0 and not (np.isnan(m) or np.isnan(s) or np.isnan(n))
    ]
    if not stats_list:
        return np.nan, np.nan

    total_count = sum(n for _, _, n in stats_list)
    mean = sum(m * n for m, _, n in stats_list) / total_count
    pooled_var = (
        sum((n - 1) * s**2 for _, s, n in stats_list)
        + sum(n * (m - mean)**2 for m, _, n in stats_list)
    ) / (total_count - 1)
    return mean, np.sqrt(pooled_var)


def get_plot_style(df_dct):
    sensors = list(df_dct.keys())
    sites = sorted({s for d in df_dct.values() for s in d})

    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    symbol_map = {
        "circle": "●",
        "square": "■",
        "diamond": "◆",
        "cross": "✚",
        "x": "✖",
        "triangle-up": "▲",
        "triangle-down": "▼",
        "triangle-left": "◀",
        "triangle-right": "▶",
        "pentagon": "⬟",
        "hexagon": "⬢",
        "star": "★",
        "hourglass": "⌛",
        "bowtie": "⋈",
    }

    st.markdown("<h2 style='text-align: center;'>Plot Style</h2>", unsafe_allow_html=True)

    sensor_colors = {}
    cols = st.columns(min(6, len(sensors)))

    for i, s in enumerate(sensors):
        with cols[i % len(cols)]:
            sensor_colors[s] = st.color_picker(
                s,
                default_colors[i % len(default_colors)],
                key=f"color_{s}"
            )

    site_symbols = {}
    cols = st.columns(min(6, len(sites)))
    symbol_keys = list(symbol_map.keys())
    symbol_labels = list(symbol_map.values())

    for i, site in enumerate(sites):
        with cols[i % len(cols)]:
            choice = st.selectbox(
                site,
                symbol_labels,
                index=i % len(symbol_labels),
                key=f"symbol_{site}"
            )
            site_symbols[site] = symbol_keys[symbol_labels.index(choice)]

    return sensor_colors, site_symbols

def add_combined_sites(band, stat_dct):
    for instrument in stat_dct:
        site_data = stat_dct[instrument]
        all_sites = list(site_data.keys())
        for time_metric in ['yearly', 'monthly']:
            all_dfs = []
            for site in all_sites:
                df = site_data[site][band].get(time_metric)
                if df is not None:
                    df = df.copy()
                    df["site"] = site
                    all_dfs.append(df)
            if not all_dfs: continue
            df_all = pd.concat(all_dfs)
            group_col = "year" if time_metric == "yearly" else "month"
            pooled_rows = []
            for time_val, group in df_all.groupby(group_col):
                means = group["mean"].values
                stds = group["std"].values
                counts = group["count"].values
                total_n = np.sum(counts)
                pooled_mean = np.sum(counts * means) / total_n
                within_var = np.sum((counts - 1) * stds**2)
                between_var = np.sum(counts * (means - pooled_mean)**2)
                pooled_std = np.sqrt((within_var + between_var) / (total_n - 1))
                pooled_rows.append({
                    group_col: time_val,
                    "mean": pooled_mean,
                    "std": pooled_std,
                    "count": total_n})
            pooled_df = pd.DataFrame(pooled_rows)
            if "combined sites" not in stat_dct[instrument]: 
                stat_dct[instrument]["combined sites"] = {}
                stat_dct[instrument]["combined sites"][band] = {}
            stat_dct[instrument]["combined sites"][band][time_metric] = pooled_df    
    return stat_dct