from typing import List

import schema
import sheets
import os
import pathlib


# TODO put this dang function in one place!
def get_tsv_files():
    path = "tests/data"
    files = [f"{path}/{f}" for f in os.listdir(path) if pathlib.Path(f).suffix == ".tsv"]
    return files


def check_delta(test: str, delta: List[schema.Delta]):
    diff = "\n".join(
        [d.debug() for d in delta if d.diff != schema.Difference.OldName and d.diff != schema.Difference.Columns]
    )
    if len(diff) > 0:
        print(f"\n{test}")
        print(diff)


def test_col_name():
    assert schema.col_name(0) == "A"
    assert schema.col_name(1) == "B"
    assert schema.col_name(26) == "AA"
    assert schema.col_name(27) == "AB"
    assert schema.col_name(26 * 2) == "BA"


def test_col_desc():
    assert schema.col_desc(0) == "column 'A'"
    assert schema.col_desc(1) == "column 'B'"
    assert schema.col_desc(26) == "column 'AA'"
    assert schema.col_desc(27) == "column 'AB'"
    assert schema.col_desc(26 * 2) == "column 'BA'"


def test_parse_schema(test_schema):
    """SchemaSheet should parse all schema."""
    test_schema = test_schema.strip()
    actual = schema.SchemaSheet(lines=test_schema)
    assert isinstance(actual, schema.SchemaSheet)
    assert len(actual.tabs) > 0
    lines = actual.to_lines()
    assert test_schema == lines


def test_to_lines():
    line = "tab:col1,col2~old2"
    tab = schema.SchemaTab(line=line)
    lines = tab.to_lines()
    assert line == lines


def test_import_compare(test_schema):
    files = get_tsv_files()
    data = schema.import_schema(files)
    assert len(data) == len(files)
    imported = schema.SchemaSheet(lines="\n".join(data))
    actual = schema.SchemaSheet(lines=test_schema)
    delta = actual.compare(imported)
    check_delta("Schema vs. TSVs", delta)
    # There are currently 4 missing tabs amd 5 column renames
    assert len(delta) == 9


def test_model_compare(test_schema):
    """SchemaSheet should compare all schema."""
    model = sheets.get_model_schema()
    actual = schema.SchemaSheet(lines=test_schema)
    delta = actual.compare(model)
    check_delta("Schema vs. Model", delta)
    assert len(delta) == 12  # TODO resolve all these schema differences.


def test_sheet_compare(create_test_sheet, cred_file, test_schema):
    """SchemaSheet should read parse all schema."""
    spreadsheet_id = create_test_sheet["spreadsheetId"]
    reader = schema.SchemaReader(spreadsheet_id=spreadsheet_id, cred_file=cred_file)
    actual = schema.SchemaSheet(lines=test_schema)
    model = sheets.get_model_schema()
    delta = actual.compare(reader.schema)
    url = create_test_sheet["spreadsheetUrl"]
    check_delta(f"Schema vs. Sheet {url}", delta)
    delta2 = model.compare(reader.schema)
    check_delta(f"Model vs. Sheet {url}", delta2)
    assert len(delta) == 9  # TODO resolve all these schema differences
    assert len(delta2) == 2
