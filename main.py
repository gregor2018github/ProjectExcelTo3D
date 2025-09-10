"""
SCRIPT DESCRIPTION:
This script creates a 3D chart from the results of the fault group analysis. It will look into three different columns and build an interactive 3D scatter plot with plotly in the browser.

SCRIPT STEPS:
1. Identify all files in the project base folder and present them to the user.
2. Let the user choose a file via the terminal.
3. Load the chosen file into a pandas DataFrame.
4. Let the user decide which ordinal columns to keep in text format and which ones to convert to integer.
5. Let the user select X, Y, Z columns and a color-coding column from the DataFrame.
6. Build a Dash app that renders an interactive Plotly 3D scatter plot from the selected columns.
7. Open the default web browser to the Dash app and run the server locally.
"""

# IMPORTS

import data_processor   

# MAIN

def main():
    # identify all files in base folder and show them to the user to choose from
    all_files = data_processor.identify_files_in_base_folder()
    selection = data_processor.choose_file_by_terminal(all_files)

    # load data
    df = data_processor.open_file_to_df(selection)
    print(f"Dataframe loaded with following dimensions: Rows: {df.shape[0]}, Columns: {df.shape[1]}")

    # make user choose which columns to keep in text format and which ones to convert to integer
    df = data_processor.change_ordinal_cols_by_terminal(df)

    # make user select the columns and color coding to display
    x_col_start, y_col_start, z_col_start, color_coding_start = data_processor.choose_columns_by_terminal(df)

    # build and run dash app
    app = data_processor.build_dash_app(df, x_col_start, y_col_start, z_col_start, color_coding_start)
    print("\nDash app running at http://127.0.0.1:8050")
    data_processor.open_browser_with_dash_app(app)
    app.run(debug=False)


if __name__ == "__main__":
    main()