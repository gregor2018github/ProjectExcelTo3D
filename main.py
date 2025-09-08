"""
SCRIPT DESCRIPTION:
This script creates a 3D chart from the results of the fault group analysis. It will look into three different columns and build an interactive 3D scatter plot with plotly in the browser.

SCRIPT STEPS:
1. Load the excel file with the data to display.
"""

# IMPORTS

import config
import data_processor   
import user_interface

# MAIN

def main():
    # launch the user interface
    ui = user_interface.UserInterface()
    # identify all files in base folder
    all_files = data_processor.identify_files_in_base_folder()
    print("Found files: ")
    for f in all_files:
        print(f" - {f}")

    # load data

    # if xlsx file
    #print(f"\nLoading data from {SOURCE_FILE} - {SOURCE_SHEET}...")
    #df = open_xlsx_to_df(SOURCE_FILE, SOURCE_SHEET)
    #print(f"Dataframe loaded with following dimensions: Rows: {df.shape[0]}, Columns: {df.shape[1]}")

    # if csv file
    print(f"\nLoading data from {config.SOURCE_FILE_CSV}...")
    df = data_processor.open_csv_to_df(config.SOURCE_FILE_CSV, config.CSV_SEP)
    data_processor.print_all_col_names_to_console(df)

    # build and run dash app
    app = data_processor.build_dash_app(df)
    print("\nDash app running at http://127.0.0.1:8050")
    data_processor.open_browser_with_dash_app(app)
    app.run(debug=False)


if __name__ == "__main__":
    main()