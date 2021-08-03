import smartsheet
import json

smart = smartsheet.Smartsheet()

## base json and field mapping
base_json = {
    "connectorType": "Smartsheet Test",
    "connectorId": "smartSheet",
	"connectorVersion": "1.0.0",
	"lxVersion": "1.0.0",
	"description": "",
	"processingDirection": "inbound",
	"processingMode": "partial",
	"customFields": {},
	"content": []
}

field_mapper = {
    'Due Date': 'dueDate',
    'Task Name': 'taskName',
    'Assigned To': 'assignedTo'
}

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
def get_sheet_data(smart, all_sheets, base_json, field_mapper):
    all_columns = {}
    fact_sheet_output = {}
    i = 1

    for a_sheet in all_sheets:
        sheet_data = smart.Sheets.get_sheet(a_sheet) 
        # populate dict of column id:name 
        for a_column in sheet_data.columns:
            all_columns[str(a_column.id)] = a_column.title

        # build dict for each row
        for a_row in sheet_data.rows:
            row_data = {}
            row_data['type'] = 'Project'
            row_data['id'] = 'PROJ-'+str(i)
            row_data['data'] = {}
            all_cells = a_row.cells
            for a_cell in all_cells:
                try:
                    if all_columns[str(a_cell._column_id)] in field_mapper:
                        row_data['data'][field_mapper[all_columns[str(a_cell._column_id)]]] = a_cell._value
                    else:
                        row_data['data'][all_columns[str(a_cell._column_id)]] = a_cell._value
                except KeyError:
                    pass

            base_json['content'].append(row_data)
            i += 1

    return base_json

if __name__ == '__main__':
    all_sheets = get_all_sheets(smart)
    ldif = get_sheet_data(smart, all_sheets, base_json, field_mapper)
    with open('smartsheet_ldif.json', 'w') as fp:
        json.dump(ldif, fp)