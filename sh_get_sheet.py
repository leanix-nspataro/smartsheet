import smartsheet
from datetime import datetime
import json

smart = smartsheet.Smartsheet()

top_level = 'workspace'

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

## returns array of workspace data and sheet to workspace map
def get_all_workspaces(smart):
    sh_wkspc_map = {}
    all_wkspc = smart.Workspaces.list_workspaces()
    wkspc_arr = []

    for wkspc in all_wkspc.data:
        wkspc_arr.append([str(wkspc.id), wkspc.name])
        wkspc_data = smart.Workspaces.get_workspace(wkspc.id)
        # sheets and _sheets seem to be broken, works as dict
        wkspc_dict = wkspc_data.to_dict()

        # create map of sheets to workspaces
        for a_sheet in wkspc_dict['sheets']:
            str_id = str(a_sheet['id'])
            new_wkspc = {}
            new_wkspc[str_id] = {}
            new_wkspc[str_id]['wkspc_id'] = str(wkspc.id)
            new_wkspc[str_id]['wkspc_name'] = wkspc.name
            new_wkspc[str_id]['type'] = 'workspace'
            sh_wkspc_map.update(new_wkspc)

    return wkspc_arr, sh_wkspc_map


## returns id of all sheets
def get_all_sheets(smart, sht_wkspc_map):
    # get all sheets
    response = smart.Sheets.list_sheets(include_all=True)
    sheets = response.data
    all_sheets = []
    # loop over sheets to get id's
    for a_sheet in sheets:
        str_id = str(a_sheet.id)
        # example sheet: {"accessLevel": "OWNER", "createdAt": "2021-07-29T20:43:04+00:00Z", "id": 5473133349103492, "modifiedAt": "2021-07-30T14:04:39+00:00Z", "name": "projects", "permalink": "https://app.smartsheet.com/sheets/jfCMVXQ6jQF4H8PWJ3jGhJf75pxjwvX3VXv9CXV1"}
        row_data = {}
        row_data['type'] = 'Sheet'
        row_data['id'] = str_id
        row_data['data'] = {}
        row_data['data']['name'] = a_sheet.name
        row_data['data']['createdAt'] = a_sheet._created_at.value.strftime('%Y-%m-%d')
        if str_id in sht_wkspc_map:
            row_data['data']['parentId'] = sht_wkspc_map[str_id]['wkspc_id']
        all_sheets.append(row_data)

    return all_sheets

## returns dict of sheet data to feed ldif
def get_sheet_data(smart, all_sheets, field_mapper):
    all_columns = {}
    all_sheet_data = []
    i = 1

    for a_sheet in all_sheets:
        sheet_data = smart.Sheets.get_sheet(int(a_sheet['id'])) 
        # populate dict of column id:name 
        for a_column in sheet_data.columns:
            all_columns[str(a_column.id)] = a_column.title

        # build dict for each row
        for a_row in sheet_data.rows:
            row_data = {}
            row_data['type'] = 'Task'
            row_data['id'] = str(a_row.id)
            row_data['data'] = {}
            row_data['data']['createdAt'] = str(a_row._created_at.value.strftime('%Y-%m-%d'))
            row_data['data']['modifiedAt'] = str(a_row._modified_at.value.strftime('%Y-%m-%d'))
            row_data['data']['modifiedBy'] = str(a_row._modified_by.value)
            row_data['data']['parentId'] = str(a_row._parent_id)
            row_data['data']['projectId'] = str(a_sheet['id'])
            row_data['data']['projectName'] = str(sheet_data.name)

            all_cells = a_row.cells
            for a_cell in all_cells:
                try:
                    if all_columns[str(a_cell._column_id)] in field_mapper:
                        row_data['data'][field_mapper[all_columns[str(a_cell._column_id)]]] = a_cell._value
                    else:
                        row_data['data'][all_columns[str(a_cell._column_id)]] = a_cell._value
                except KeyError:
                    pass

            all_sheet_data.append(row_data)

    return all_sheet_data 

def transform_to_ldif(base_json, all_sheets, all_tasks, workspaces="None"):
    if workspaces != "None":
        for wrkspc in workspaces:
            new_content = {}
            new_content['type'] = 'Workspace'
            new_content['id'] = wrkspc[0]
            new_content['data'] = {}
            new_content['data']['name'] = wrkspc[1]
            base_json['content'].append(new_content)

    for a_sheet in all_sheets:
        base_json['content'].append(a_sheet)

    for a_task in all_tasks:
        base_json['content'].append(a_task)

    return base_json

if __name__ == '__main__':
    ## get data from Smartsheet
    workspaces, sht_wkspc_map = get_all_workspaces(smart)
    all_sheets = get_all_sheets(smart, sht_wkspc_map)
    all_tasks = get_sheet_data(smart, all_sheets, field_mapper)
    ## transform data to LDIF
    ldif_output = transform_to_ldif(base_json, all_sheets, all_tasks, workspaces)
    ## write LDIF to json
    with open('smartsheet_ldif4.json', 'w') as fp:
        json.dump(ldif_output, fp)
