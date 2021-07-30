import smartsheet
import json

smart = smartsheet.Smartsheet()

## returns id of all sheets
def get_all_sheets(smart):
    all_sheets = []
    # get all sheets
    response = smart.Sheets.list_sheets(include_all=True)
    sheets = response.data

    # loop over sheets to get id's
    for a_sheet in sheets:
        # example sheet: {"accessLevel": "OWNER", "createdAt": "2021-07-29T20:43:04+00:00Z", "id": 5473133349103492, "modifiedAt": "2021-07-30T14:04:39+00:00Z", "name": "projects", "permalink": "https://app.smartsheet.com/sheets/jfCMVXQ6jQF4H8PWJ3jGhJf75pxjwvX3VXv9CXV1"}
        all_sheets.append(a_sheet.id)

    return all_sheets

## returns dict of sheet data to feed ldif
def get_sheet_data(smart, da_sheets):
    all_columns = {}
    fact_sheet_output = {}
    for a_sheet in da_sheets:
        sheet_data = smart.Sheets.get_sheet(a_sheet) 
        # populate dict of column id:name 
        for a_column in sheet_data.columns:
            all_columns[str(a_column.id)] = a_column.title

        # build dict for each row
        for a_row in sheet_data.rows:
            row_data = {}
            row_data['type'] = 'Project'
            all_cells = a_row.cells
            for a_cell in all_cells:
                try:
                    row_data[all_columns[str(a_cell._column_id)]] = a_cell._value
                except KeyError:
                    pass

        fact_sheet_output.update(row_data)

    return fact_sheet_output

if __name__ == '__main__':
    da_sheets = get_all_sheets(smart)
    get_sheet_data(smart, da_sheets)