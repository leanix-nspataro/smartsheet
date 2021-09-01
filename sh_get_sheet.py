import smartsheet
from datetime import datetime
import json
import requests
import re
import logging

top_level = "workspace"

field_mapper = {
    "Due Date": "dueDate",
    "Task Name": "taskName",
    "Assigned To": "assignedTo"
}

logging.basicConfig(filename='smartsheet_audit.log', format='>> %(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class smartsheetToLdif:
    ## connection to smartsheet
    smart = smartsheet.Smartsheet()

    ## base json and field mapping
    base_json = {
        "connectorType": "Smartsheet Test-3",
        "connectorId": "smartSheet-3",
        "connectorVersion": "1.0.0",
        "lxVersion": "1.0.0",
        "description": "",
        "processingDirection": "inbound",
        "processingMode": "partial",
        "customFields": {},
        "content": []
    }

    ## returns array of workspace data and sheet to workspace map
    def get_all_workspaces(self, smart):
        self.sh_wkspc_map = {}
        self.all_wkspc = smart.Workspaces.list_workspaces()
        self.wkspc_arr = []
        num_wkspc = 0
        num_sht = 0

        for wkspc in self.all_wkspc.data:
            num_wkspc += 1
            self.wkspc_arr.append([str(wkspc.id), wkspc.name])
            wkspc_data = smart.Workspaces.get_workspace(wkspc.id)
            # sheets and _sheets seem to be broken, works as dict
            wkspc_dict = wkspc_data.to_dict()
            logging.debug('Workspace data: %s',str(wkspc_dict))
            # create map of sheets to workspaces
            for a_sheet in wkspc_dict["sheets"]:
                num_sht += 1
                str_id = str(a_sheet["id"])
                new_wkspc = {}
                new_wkspc[str_id] = {}
                new_wkspc[str_id]["wkspc_id"] = str(wkspc.id)
                new_wkspc[str_id]["wkspc_name"] = wkspc.name
                new_wkspc[str_id]["type"] = "workspace"
                self.sh_wkspc_map.update(new_wkspc)

        logging.info('Processing %i sheets from %i workspaces.', num_sht, num_wkspc)
        return self.wkspc_arr, self.sh_wkspc_map


    ## returns id of all sheets
    def get_all_sheets(self, smart, sht_wkspc_map):
        # get all sheets
        self.response = smart.Sheets.list_sheets(include_all=True)
        self.sheets = self.response.data
        self.all_sheets = []
        # loop over sheets to get id"s
        for a_sheet in self.sheets:
            logging.debug('Sheet data: %s', str(a_sheet.to_dict()))
            str_id = str(a_sheet.id)
            # example sheet: {"accessLevel": "OWNER", "createdAt": "2021-07-29T20:43:04+00:00Z", "id": 5473133349103492, "modifiedAt": "2021-07-30T14:04:39+00:00Z", "name": "projects", "permalink": "https://app.smartsheet.com/sheets/jfCMVXQ6jQF4H8PWJ3jGhJf75pxjwvX3VXv9CXV1"}
            row_data = {}
            row_data["type"] = "Sheet"
            row_data["id"] = str_id
            row_data["data"] = {}
            row_data["data"]["name"] = a_sheet.name
            row_data["data"]["createdAt"] = a_sheet._created_at.value.strftime("%Y-%m-%d")
            if str_id in sht_wkspc_map:
                row_data["data"]["parentId"] = sht_wkspc_map[str_id]["wkspc_id"]
            self.all_sheets.append(row_data)

        logging.info('Processing %i total sheets (including from workspaces).', len(self.all_sheets))
        return self.all_sheets

    ## returns dict of sheet data to feed ldif
    def get_sheet_data(self, smart, all_sheets, field_mapper):
        self.all_columns = {}
        self.all_sheet_data = []
        self.i = 1
        self.webhook_map = {}
        num_sht = 0
        num_row = 0
        num_cell = 0

        for a_sheet in all_sheets:
            num_sht += 1
            sheet_data = smart.Sheets.get_sheet(int(a_sheet["id"])) 
            # populate dict of column id:name 
            for a_column in sheet_data.columns:
                self.all_columns[str(a_column.id)] = a_column.title

            # build dict for each row
            for a_row in sheet_data.rows:
                logging.debug('Row data: %s', str(a_row.to_dict()))
                num_row += 1
                row_data = {}
                row_data["type"] = "Task"
                row_data["id"] = str(a_row.id)
                row_data["data"] = {}
                row_data["data"]["createdAt"] = str(a_row._created_at.value.strftime("%Y-%m-%d"))
                row_data["data"]["modifiedAt"] = str(a_row._modified_at.value.strftime("%Y-%m-%d"))
                row_data["data"]["modifiedBy"] = str(a_row._modified_by.value)
                row_data["data"]["parentId"] = str(a_row._parent_id)
                row_data["data"]["projectId"] = str(a_sheet["id"])
                row_data["data"]["projectName"] = str(sheet_data.name)

                all_cells = a_row.cells
                for a_cell in all_cells:
                    try:
                        logging.debug('Cell data: %s', str(a_cell.to_dict()))
                        # if str(a_sheet["id"]) not in self.webhook_map:
                        #     self.webhook_map[str(a_sheet["id"])] = []
                        #     self.webhook_map[str(a_sheet["id"])].append(a_cell._column_id.value)
                        # else:
                        #     self.webhook_map[str(a_sheet["id"])].append(a_cell._column_id.value)
                        num_cell += 1
                        if self.all_columns[str(a_cell._column_id)] in field_mapper:
                            row_data["data"][field_mapper[self.all_columns[str(a_cell._column_id)]]] = a_cell._value
                        else:
                            row_data["data"][self.all_columns[str(a_cell._column_id)]] = a_cell._value
                    except KeyError:
                        logging.debug('Column not in map: %s', str(a_cell._column_id))
                        pass

                self.all_sheet_data.append(row_data)

        logging.info('Extracted data from %i cells, %i rows, %i sheets.', num_cell, num_row, num_sht)
        return self.all_sheet_data #, self.webhook_map

    ## transform 
    def transform_to_ldif(self, base_json, all_sheets, all_tasks, workspaces="None"):
        if workspaces != "None":
            for wrkspc in workspaces:
                new_content = {}
                new_content["type"] = "Workspace"
                new_content["id"] = wrkspc[0]
                new_content["data"] = {}
                new_content["data"]["name"] = wrkspc[1]
                base_json["content"].append(new_content)

        for a_sheet in all_sheets:
            base_json["content"].append(a_sheet)

        for a_task in all_tasks:
            base_json["content"].append(a_task)

        return base_json

class ldifToWorkspace:
    api_token = ""
    auth_url = "https://demo-us.leanix.net/services/mtm/v1/oauth2/token"
    request_url = "https://demo-us.leanix.net/services/integration-api/v1/"

    response = requests.post(auth_url, auth=("apitoken", api_token), data={"grant_type": "client_credentials"})
    response.raise_for_status()
    header = {"Authorization": "Bearer " + response.json()["access_token"], "Content-Type": "application/json"}

    with open("sh_processor4.json") as json_file:
        ldif_processor = json.load(json_file)

    def createProcessorRun(self, ldif_processor, request_url, header, api_token):
        self.data = {
            "connectorType": "Smartsheet Test-3",
            "connectorId": "smartSheet-3",
            "connectorVersion": "1.0.0",
            "processingDirection": "inbound",
            "processingMode": "partial",
            "credentials": {
                "apiToken": api_token
            },
            "variables": {
                "deploymentMaturity": {
                    "default": "0"
                }
            },
            "processors": ldif_processor['processors']
        }
        self.data = json.dumps(self.data)
        new_data = re.sub(r': True', ': true', self.data)
        response = requests.put(url=request_url + "configurations/", headers=header, data=new_data)

    def createRun(self, content, request_url, header):
        self.data = {
            "connectorType": "Smartsheet Test-3",
            "connectorId": "smartSheet-3",
            "connectorVersion": "1.0.0",
            "lxVersion": "1.0.0",
            "description": "Creates LeanIX Projects from Smartsheet workspaces",
            "processingDirection": "inbound",
            "processingMode": "partial",
            "customFields": {},
            "content": content['content']
        }
        
        self.response = requests.post(url=request_url + "synchronizationRuns/", headers=header, data=json.dumps(self.data))
        return (self.response.json())

    def startRun(self, run, request_url, header):
        response = requests.post(url=request_url + "synchronizationRuns/" + run["id"] + "/start?test=false", headers=header)


if __name__ == "__main__":
    logging.info('----- Start -----')
    #### Get smartsheet data, transform to LDIF
    sh = smartsheetToLdif()
    ## get data from Smartsheet
    workspaces, sht_wkspc_map = sh.get_all_workspaces(sh.smart)
    all_sheets = sh.get_all_sheets(sh.smart,sht_wkspc_map)
    all_tasks = sh.get_sheet_data(sh.smart, all_sheets, field_mapper)
    # print(all_sheets)
    ## transform data to LDIF
    ldif_output = sh.transform_to_ldif(sh.base_json, all_sheets, all_tasks, workspaces)
    logging.info('Trasformed data to LDIF.')
    logging.debug('LDIF: %s', str(ldif_output))
    ## write LDIF to json
    with open("smartsheet_ldif5.json", "w") as fp:
        json.dump(ldif_output, fp)

    #### send data to Lean IX workspace
    lx = ldifToWorkspace()
    lx.createProcessorRun(lx.ldif_processor, lx.request_url, lx.header, lx.api_token)
    run = lx.createRun(ldif_output, lx.request_url, lx.header)
    lx.startRun(run, lx.request_url, lx.header)
    logging.info('LDIF processed by LeanIX iAPI.')
    logging.info('----- End -----')
