# Smartsheet to LDIF

## Requirements
- python 3.x  
- pip 3.x
- smartsheet-python-sdk

## Abstract
The purpose of this script is to extract data from Smartsheet, transform it to LeanIX Data Interchange Format (LDIF), and import it to a LeanIX workspace.  The relationship hierarchy goes: Workspace, Sheet, Task, Subtask.  As a best practice, we do not want to have more than four layers of a hierarchy (although the script does handle this).  

## Smartshee API

This code utilizes the Smartsheet python SDK.  The API documentation can be found [here](https://smartsheet-platform.github.io/api-docs/?python).  To save you from searching docs, instructions for installing the SDK and retrieving the API token are below.

To install the SDK in your environment, run:

`pip3 install smartsheet-python-sdk`

To retrieve your Smartsheet API token:

- in the Smartsheet UI
- lower left corner, click Account 
- click Personal Setting...
- click API Access

(be ready to store your token, it disappears forever when you close the window)
- click Generate new access token

The easiest way to use this token with the SDK is to create an environment variable.  It is recomended to create this using your .bash_profile file.  To open this in a terminal/command line, either use vim or your favorite editor.

```
vim ~/.bash_profile
```

Add a new line in your .bash_profile with the token

```
export SMARTSHEET_ACCESS_TOKEN="<your token here>"
```

Then run:
```
source ~/.bash_profile
```
=========================================================

BEWARE: Mac does not automatically source .bash_profile.  If you'll be using .bash_profile, make sure your .zshrc sources it:

```
if [ -f ~/.bash_profile ]; then
  . ~/.bash_profile
fi
```
=========================================================

## sh_get_sheet.py

### Running

base_json is initally defined with the metadata for a Smartsheet LDIF.  Column names from Smartsheet are trasformed via the field_mapper dict to fit the LDIF schema.

Obtain an API token from the LeanIX workspace and put it in api_token.  Ensure your auth and request url are correct. (lines 138 - 140 in sh_get_sheet.py)

```
python3 sh_get_sheet.py 
```

### Current functionality
- list all workspaces, sheets, and sub/tasks
- get data from all workspaces, sheets, and sub/tasks
- transform data to ldif
- output ldif json file
- import ldif to LeanIX workspace

## Import LDIF to EAS manually
- go to Administration in the top right drop down
- go to Integration API in the left pane
- click Starter Example
- paste the processor in the left pane
- paste the output lidf from the script into the Input pane on the top right
- click Test run to check for warnings/errors < currently throwing warnings that can be ignored, to be fixed >
- if successful, click run to ingest the data into the workspace
