import datetime, joblib
import pandas as pd
from pathlib import Path
import io
import streamlit as st
import numpy as np

def get_dataframes(sites_config, sensors_config, condition, mode = 'SensorToGroundComparison'):
    base_dir = Path(__file__).resolve().parent / "Database" / "Sites" 
    df_dct = {}
    stat_dct = {}
    for sensor in condition['sensors']:     
        site_dct = {}
        site_stat_dct = {}
        for site in condition['sites']:  
            sensor_dir = base_dir / sites_config[site]["network"] / site / mode / sensor
            df = joblib.load(sensor_dir / "Files" / "df.pkl")
            df = apply_condition(df, condition)      
            df = df.reset_index(drop=True)    
            stat = get_stat (df)
            site_dct [site] = df
            site_stat_dct [site] = stat
        df_dct[sensor] = site_dct
        stat_dct[sensor] = site_stat_dct
    return df_dct, stat_dct

def apply_condition(df, condition): 
    start_date = datetime.datetime.strptime(condition['start_date'], "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(condition['end_date'], "%Y-%m-%d").date()
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df = df[df['time_diff'] <= condition['time_diff']]
    if not df['VZA'].isna().all(): df = df[df['VZA'] <= condition['VZA']]     
    df = apply_quality_condition(df, condition['site_conditions'])
    df = apply_atmospheric_condition(df, condition['atm_conditions'])
    if condition['remove_outliers']: df = outlier_removal(df)
    return df

def apply_quality_condition(df, site_conditions):
    for condition, threshold in site_conditions.items():
        site_col = f'site_{condition}'
        if not df[site_col].isna().all():
            col = site_col
            value = threshold
        else:
            continue
        df = df[(df[col] >= value[0]) & (df[col] <= value[1])]
    return df

def apply_atmospheric_condition(df, atm_conditions):
    for condition, threshold in atm_conditions.items():
        df = df[(df[condition] >= threshold[0]) & (df[condition] <= threshold[1])]
    return df

def outlier_removal(df):
    ratio_cols = [col for col in df.columns if col.startswith('ratio_') and not col.startswith('ratio_unc_')]
    final_mask = pd.Series(False, index=df.index)
    for column in ratio_cols:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        col_mask = df[column].between(lower_bound, upper_bound)
        final_mask |= col_mask
    return df[final_mask].reset_index(drop=True)

def get_stat(df):
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.to_period('M')
    ratio_cols = [col for col in df.columns if col.startswith('ratio_') and not col.startswith('ratio_unc_')]
    stat = {}
    for rto_col in ratio_cols:
        band_name = rto_col.split('_')[2]
        ratios = df[rto_col].values
        mean_ratio = np.mean(ratios)
        std_ratio = np.std(ratios)
        num_acquisitions = len(ratios)
        yearly_stats = df.groupby('year')[rto_col].agg(['mean', 'std', 'count']).reset_index()
        monthly_stats = df.groupby('month')[rto_col].agg(['mean', 'std', 'count']).reset_index()
        stat[band_name] = {'overall': {'mean_ratio': mean_ratio,
                                       'std_ratio': std_ratio,
                               'num_acquisitions': num_acquisitions},
                           'yearly': yearly_stats,
                           'monthly': monthly_stats}
    return stat

def excel_save(df_dct):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Create xlsxwriter formats
        def make_fmt(bg_color):
            return workbook.add_format({
                "bg_color": bg_color,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "border_color": "#DDDDDD",
            })

        def make_cell_fmt(bg_color):
            return workbook.add_format({
                "bg_color": bg_color,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "border_color": "#DDDDDD",
            })

        default_header_fmt = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#DDDDDD",
        })

        default_cell_fmt = workbook.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#DDDDDD",
        })

        style_map = {
            "sens_id": ("#F5F5F5"),
            "sens_time": ("#EDE7F6"),
            "rcn_time": ("#EDE7F6"),
            "time_diff": ("#EDE7F6"),
            "site_": ("#F5F5F5"),
            "metadata_cloud": ("#F5F5F5"),
            "SAA": ("#FFF9C4"),
            "SZA": ("#FFF9C4"),
            "VAA": ("#FFF9C4"),
            "VZA": ("#FFF9C4"),
            "ratio": ("#E8F5E9"),
            "ratio_unc": ("#A5D6A7"),
            "P": ("#F5F5F5"),
            "T": ("#F5F5F5"),
            "WV": ("#F5F5F5"),
            "O3": ("#F5F5F5"),
            "AOD": ("#F5F5F5"),
            "Ang": ("#F5F5F5"),
            "AU": ("#F5F5F5"),
            "sens_refl": ("#E3F2FD"),
            "sens_refl_unc": ("#BBDEFB"),
            "refl_std": ("#90CAF9"),
            "rcn_refl": ("#FFEBEE"),
            "rcn_refl_unc": ("#EF9A9A"),
        }

        header_formats = {k: make_fmt(v) for k, v in style_map.items()}
        cell_formats = {k: make_cell_fmt(v) for k, v in style_map.items()}
        sorted_keys = sorted(style_map.keys(), key=len, reverse=True)

        for sensor, site_dfs in df_dct.items():
            for site, df in site_dfs.items():
                sheet_name = f"{sensor}_{site}"[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                ws = writer.sheets[sheet_name]

                # Freeze panes at B2
                ws.freeze_panes(1, 1)

                for col_idx, col_name in enumerate(df.columns):
                    header_val = str(col_name or "")

                    # Match style by prefix
                    matched_key = None
                    for key in sorted_keys:
                        if header_val.startswith(key):
                            matched_key = key
                            break

                    header_fmt = header_formats.get(matched_key, default_header_fmt)
                    cell_fmt = cell_formats.get(matched_key, default_cell_fmt)

                    # Rewrite header with style
                    ws.write(0, col_idx, header_val, header_fmt)

                    # Apply style to whole column data area
                    max_len = max(
                        len(header_val),
                        df.iloc[:, col_idx].astype(str).map(len).max() if not df.empty else 0
                    )

                    if "sens_id" in header_val:
                        width = max_len + 15
                    else:
                        width = max_len + 5

                    ws.set_column(col_idx, col_idx, width, cell_fmt)

    output.seek(0)

    st.download_button(
        label="📥 Download Data",
        data=output.getvalue(),
        file_name="RadCalNet_All_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )