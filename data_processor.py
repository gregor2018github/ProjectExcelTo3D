"""
SCRIPT DESCRIPTION:
This script holds functions for data processing.
"""

# IMPORTS

import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import config

# GENERAL FUNCTIONS

def identify_files_in_base_folder() -> list:
    """
    Identify all files in the base folder of the script that have the file endings .xlsx and .csv and return a list of found file names.
    """
    import os
    base_folder = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(base_folder) if os.path.isfile(os.path.join(base_folder, f)) and not f.startswith('.') and f.endswith(('.xlsx', '.csv'))]
    return files

def open_xlsx_to_df(file_name: str, sheet_name: str) -> pd.DataFrame:
    """
    Open a given tab from a given excel file and return a pandas DataFrame of the found table.
    """
    df = pd.read_excel(file_name, sheet_name=sheet_name)
    return df

def open_csv_to_df(file_name: str, sep: str) -> pd.DataFrame:
    """
    Open a CSV file with a certain separator and return a pandas DataFrame.
    """
    df = pd.read_csv(file_name, sep=sep)
    return df

def print_all_col_names_to_console(df: pd.DataFrame) -> None:
    """
    Print all column names and datatypes of the DataFrame to the console.
    """
    print("\nAll column names and datatypes:")
    for col in df.columns:
        print(f" - {col}: {df[col].dtype}")

def get_numeric_columns(df: pd.DataFrame) -> list:
    """
    Get all numeric columns from the DataFrame that can be used for plotting.
    """
    numeric_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_timedelta64_dtype(df[col]):
            numeric_cols.append(col)
    return numeric_cols

def prepare_column_data(df: pd.DataFrame, col_name: str):
    """
    Prepare column data for plotting by handling different data types.
    """
    if col_name not in df.columns:
        return df.iloc[:, 0]  # Fallback to first column
    
    col_data = df[col_name].copy()
    
    # Handle timedelta columns by converting to total seconds
    if pd.api.types.is_timedelta64_dtype(col_data):
        return col_data.dt.total_seconds()
    
    # Handle datetime columns by converting to timestamp (seconds)
    elif pd.api.types.is_datetime64_any_dtype(col_data):
        # Convert NaT to NaN-safe numeric
        ts = col_data.view('int64')  # nanoseconds
        ts = pd.Series(ts).where(~col_data.isna(), np.nan)
        return (ts // 10**9).astype(float)
    
    # Handle categorical/string columns by creating numeric codes
    elif col_data.dtype == 'object':
        col_data = col_data.fillna('Unknown')
        return pd.Categorical(col_data).codes.astype(float)
    
    # Numeric: fill NaN
    return col_data.astype(float).fillna(0.0)

def build_3d_figure(df: pd.DataFrame, x_col: str, y_col: str, z_col: str, color_col: str) -> go.Figure:
    """
    Build a 3D scatter plot figure for given column selections.
    Ensures axis titles, colorbar title, and tooltips reflect current selections.
    """
    # Prepare numeric arrays
    x_data = prepare_column_data(df, x_col)
    y_data = prepare_column_data(df, y_col)
    z_data = prepare_column_data(df, z_col)
    color_data = prepare_column_data(df, color_col)

    # Customdata: [row_index, color_value] to show color value in tooltip
    row_idx = np.arange(len(df))
    customdata = np.column_stack((row_idx, color_data))

    hovertemplate = (
        "Row %{customdata[0]}"
        f"<br>{x_col}: %{{x}}"
        f"<br>{y_col}: %{{y}}"
        f"<br>{z_col}: %{{z}}"
        f"<br>{color_col}: %{{customdata[1]}}"
        "<extra></extra>"
    )

    fig = go.Figure(data=[go.Scatter3d(
        x=x_data,
        y=y_data,
        z=z_data,
        mode="markers",
        marker=dict(
            size=3,
            color=color_data,
            colorscale="Viridis",
            colorbar=dict(title=dict(text=color_col)),
            opacity=0.8
        ),
        customdata=customdata,
        hovertemplate=hovertemplate,
        name="Data Points"
    )])

    fig.update_layout(
        title="3D Scatter Plot of Fault Groups - Interactive",
        autosize=False,
        width=1300,
        height=900,
        margin=dict(l=65, r=50, b=65, t=90),
        scene=dict(
            xaxis_title=x_col,
            yaxis_title=y_col,
            zaxis_title=z_col,
        )
    )
    return fig

def build_dash_app(df: pd.DataFrame) -> Dash:
    """
    Build and return a Dash app instance.
    """
    # Build Dash app
    app = Dash(__name__)
    all_columns = df.columns.tolist()

    dropdown_style = {"width": "24%", "display": "inline-block", "verticalAlign": "top", "marginRight": "1%"}
    label_style = {"display": "block", "fontWeight": "bold", "marginBottom": "6px"}

    app.layout = html.Div([
        html.Div([
            html.Label("Color-Coding", style=label_style),
            dcc.Dropdown(
                id="color-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=config.COLOR_CODING_DIMENSION,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("X-Axis", style=label_style),
            dcc.Dropdown(
                id="x-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=config.COLUMN_X,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("Y-Axis", style=label_style),
            dcc.Dropdown(
                id="y-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=config.COLUMN_Y,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("Z-Axis", style=label_style),
            dcc.Dropdown(
                id="z-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=config.COLUMN_Z,
                clearable=False
            )
        ], style=dropdown_style),

        dcc.Graph(
            id="scatter-3d",
            figure=build_3d_figure(df, config.COLUMN_X, config.COLUMN_Y, config.COLUMN_Z, config.COLOR_CODING_DIMENSION)
        )
    ])

    @app.callback(
        Output("scatter-3d", "figure"),
        Input("x-col", "value"),
        Input("y-col", "value"),
        Input("z-col", "value"),
        Input("color-col", "value"),
    )
    def update_figure(x_col, y_col, z_col, color_col):
        return build_3d_figure(df, x_col, y_col, z_col, color_col)
    
    return app

def open_browser_with_dash_app(app: Dash) -> None:
    """
    Open the default web browser and navigate to the local Dash app.
    """
    import webbrowser
    webbrowser.open("http://127.0.0.1:8050")