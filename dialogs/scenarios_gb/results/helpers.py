from pathlib import Path
import pandas as pd
from ..dataclasses import ScenarioResult
from .constants import (
    RESULT_CSV_MANDATORY_COLUMNS,
    RESULT_CSV_MANDATORY_ID_EXPLOITATION_COLUMN,
    RESULT_CSV_MANDATORY_NUMERIC_COLUMNS,
)
from ..dataclasses import ScenarioResult


def analyse_results_directory(results_directory: Path) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    # loop trough all the files in the directory and subdirectories
    for file in results_directory.glob("**/*.csv"):
        # read the csv file
        # if the file is empty, skip it
        if file.stat().st_size == 0:
            continue
        try:
            df = pd.read_csv(
                file,
                delimiter=";",
                dtype={RESULT_CSV_MANDATORY_ID_EXPLOITATION_COLUMN: str},
            )
            # if the file is empty, skip it
            if df.empty:
                continue
            # check if the mandatory fields exist
            if not has_mandatory_columns(df.columns.to_list()):
                # print(f"File {file} does not have the mandatory columns")
                continue  # check if the mandatory fields exists and the expected types are correct
            # check if the column id_exploitation is equal to the id_exploitation parameter
            # only work with the first row
            data_row = df.iloc[0]

            # check if all the columns are of numeric type if not exit the file loop
            for column in RESULT_CSV_MANDATORY_NUMERIC_COLUMNS:
                if not pd.api.types.is_numeric_dtype(data_row[column].dtype):
                    break
            else:
                # create a ScenarioResult object and append to the results list
                result = ScenarioResult(
                    id_exploitation=str(
                        data_row[RESULT_CSV_MANDATORY_ID_EXPLOITATION_COLUMN]
                    ),
                    scenario_name=str(data_row["scenario"]),
                    tx_boisement_externe=float(data_row["tx_boisement_externe"]),
                    tx_boisement_interne=float(data_row["tx_boisement_interne"]),
                    surface=float(data_row["surface"]),
                    surface_arbre=float(data_row["surface_arbre"]),
                    surface_boisement=float(data_row["surface_boisement"]),
                    surface_haie=float(data_row["surface_haie"]),
                    surface_massif=float(data_row["surface_massif"]),
                    delta_gb=float(data_row["delta_gb"]),
                    delta_seuil_gb=float(data_row["delta_seuil_gb"]),
                )
                results.append(result)
        except FileNotFoundError:
            print(f"File {file} not found")
            continue
        except IOError:
            print(f"Could not read file {file}")
            continue

    return results


def has_mandatory_columns(columns: list[str]) -> bool:
    # check if all the mandatory columns are at least in the columns list

    return all(column in columns for column in RESULT_CSV_MANDATORY_COLUMNS)
    # missing_columns = [
    #     column for column in RESULT_CSV_MANDATORY_COLUMNS if column not in columns
    # ]
    # if missing_columns:
    #     print(f"Missing mandatory columns: {missing_columns}")
    #     return False
    # return True
