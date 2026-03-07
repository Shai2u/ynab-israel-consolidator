
from etl_sources.mizrachi_reader import load_mizrachi_tables


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> None:
    loaded_tables = load_mizrachi_tables(folder=path_to_folder, recursive=False)
    print(f"Loaded files: {len(loaded_tables)}")

    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")

# STEP: parse date
# STEP: split inflow/outflow
# TODO: handle installment rows


if __name__ == "__main__":
    path_to_folder = r'C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_mizrachi'
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)