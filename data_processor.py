"""
SCRIPT DESCRIPTION:
This script holds functions for data processing.
"""

# IMPORTS

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Input, Output

# GENERAL FUNCTIONS

def identify_files_in_base_folder() -> list:
    """
    Identify all files in the base folder of the script that have the file endings .xlsx and .csv and return a list of found file names.
    """
    import os
    base_folder = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(base_folder) if os.path.isfile(os.path.join(base_folder, f)) and not f.startswith('.') and f.endswith(('.xlsx', '.csv'))]
    return files

def choose_file_by_terminal(files: list) -> None:
    """
    Give the user the option to choose a file by entering the corresponding number in the terminal. Returns the selected file name.
    """
    print("Found files: ")
    i = 1
    for f in files:
        print(f"({i}) - {f}")
        i += 1
    print("\nPlease choose a file by entering the corresponding number (e.g., 1):")
    while True:
        try:
            choice = int(input("Your choice: "))
            if 1 <= choice <= len(files):
                selected_file = files[choice - 1]
                print(f"You selected: {selected_file}")
                return selected_file
            else:
                print(f"Please enter a number between 1 and {len(files)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def choose_sheet_by_terminal(file_name: str) -> str:
    """
    If the given file is an excel file, give the user the option to choose a sheet by entering the corresponding number in the terminal.
    """

    xls = pd.ExcelFile(file_name)
    sheets = xls.sheet_names
    # if only one sheet available, automatically return it
    if len(sheets) == 1:
        return sheets[0]
    print("\nAvailable sheets in the Excel file:")
    for i, sheet in enumerate(sheets, start=1):
        print(f"({i}) - {sheet}")

    print("\nPlease choose a sheet by entering the corresponding number (e.g., 1):")
    while True:
        try:
            choice = int(input("Your choice: "))
            if 1 <= choice <= len(sheets):
                selected_sheet = sheets[choice - 1]
                print(f"You selected: {selected_sheet}")
                return selected_sheet
            else:
                print(f"Please enter a number between 1 and {len(sheets)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def open_file_to_df(file_name: str) -> pd.DataFrame:
    """
    Open a given file (either .xlsx or .csv) and return a pandas DataFrame of the found table.
    """
    if file_name.endswith('.xlsx'):
        selected_sheet = choose_sheet_by_terminal(file_name)
        return pd.read_excel(file_name, sheet_name=selected_sheet)
    elif file_name.endswith('.csv'):
        return pd.read_csv(file_name)
    else:
        raise ValueError("Unsupported file format. Please provide a .xlsx or .csv file.")

def choose_columns_by_terminal(df: pd.DataFrame) -> tuple:
    """
    Give the user the option to choose initiating settings for the 3D graph by entering the corresponding number in the terminal.
    """
    columns = df.columns
    print("\nAvailable columns in the data frame:")
    for i, col in enumerate(columns, start =1):
        print(f"({i}) - {col}")

    def _ask_for(column_role: str) -> str:
        prompt = f"\nPlease choose the {column_role} column by entering the corresponding number (e.g., 1): "
        while True:
            try:
                choice = int(input(prompt))
                if 1 <= choice <= len(columns):
                    selected = columns[choice - 1]
                    print(f"You selected for {column_role}: {selected}")
                    return selected
                else:
                    print(f"Please enter a number between 1 and {len(columns)}.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    
    x_col = _ask_for("X-Axis")
    y_col = _ask_for("Y-Axis")
    z_col = _ask_for("Z-Axis")
    color_col = _ask_for("Color-Coding")
    
    return x_col, y_col, z_col, color_col

def change_ordinal_cols_by_terminal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Let the user decide which ordinal columns to keep in text format and which ones to convert to integer.
    """
    columns = df.columns
    print("\nAvailable columns in the data frame:")
    for i, col in enumerate(columns, start=1):
        print(f"({i}) - {col} (dtype: {df[col].dtype})")

    print("\nFor each column, enter 't' to keep as text or 'n' to convert to numeric (integer/float).")
    
    for col in columns:
        
        # ask user for each column, only if it's object or categorical dtype
        if df[col].dtype in ['object', 'category']:
            while True:
                choice = input(f"Column '{col}': (t/n)? ").strip().lower()
                if choice == 't':
                    df[col] = df[col].astype(str).fillna('Unknown')
                    break
                elif choice == 'n':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    break
                else:
                    print("Invalid input. Please enter 't' or 'n'.")
        
        # fill NaN in columns that are already numeric
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
    
    return df

def change_data_types_to_numeric(df: pd.DataFrame, col_name: str):
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
    Supports both continuous (numeric) and discrete (categorical) color coding.
    """
    # Prepare arrays
    x_data = df[x_col]
    y_data = df[y_col]
    z_data = df[z_col]
    color_data = df[color_col]

    fig = go.Figure()

    # Determine if color column should be treated as numeric (continuous) or categorical (discrete)
    is_numeric_color = (
        pd.api.types.is_numeric_dtype(color_data)
        or pd.api.types.is_bool_dtype(color_data)
        or pd.api.types.is_datetime64_any_dtype(color_data)
        or pd.api.types.is_timedelta64_dtype(color_data)
    )

    if is_numeric_color:
        # Continuous color scale with colorbar
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
        fig.add_trace(go.Scatter3d(
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
        ))
    else:
        # Discrete categories: one trace per category with legend
        cats = pd.Categorical(color_data.fillna("Unknown"))
        unique_cats = list(cats.categories)
        palette = getattr(px.colors.qualitative, "Plotly", [
            "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
            "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
        ])
        color_map = {cat: palette[i % len(palette)] for i, cat in enumerate(unique_cats)}

        row_idx = np.arange(len(df))
        for cat in unique_cats:
            mask = (cats == cat)
            customdata = np.column_stack((row_idx[mask], np.array([cat] * int(mask.sum()))))
            hovertemplate = (
                "Row %{customdata[0]}"
                f"<br>{x_col}: %{{x}}"
                f"<br>{y_col}: %{{y}}"
                f"<br>{z_col}: %{{z}}"
                f"<br>{color_col}: %{{customdata[1]}}"
                "<extra></extra>"
            )
            fig.add_trace(go.Scatter3d(
                x=x_data[mask],
                y=y_data[mask],
                z=z_data[mask],
                mode="markers",
                marker=dict(size=3, color=color_map[cat], opacity=0.8),
                name=str(cat),
                customdata=customdata,
                hovertemplate=hovertemplate,
                showlegend=True
            ))

        # Add legend title for categorical color
        fig.update_layout(legend=dict(title=dict(text=color_col)))

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

def build_dash_app(df: pd.DataFrame, x_col_start: str, y_col_start: str, z_col_start: str, color_coding_start: str) -> Dash:
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
                value=color_coding_start,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("X-Axis", style=label_style),
            dcc.Dropdown(
                id="x-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=x_col_start,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("Y-Axis", style=label_style),
            dcc.Dropdown(
                id="y-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=y_col_start,
                clearable=False
            )
        ], style=dropdown_style),
        html.Div([
            html.Label("Z-Axis", style=label_style),
            dcc.Dropdown(
                id="z-col",
                options=[{"label": c, "value": c} for c in all_columns],
                value=z_col_start,
                clearable=False
            )
        ], style=dropdown_style),

        dcc.Graph(
            id="scatter-3d",
            figure=build_3d_figure(df, x_col_start, y_col_start, z_col_start, color_coding_start)
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