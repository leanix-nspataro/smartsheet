# Smartsheet to LDIF

## Requirements
- python 3.x  
- pip 3.x
- smartsheet-python-sdk

## Abstract
The purpose of this script is to extract data from Smartsheet and transform it to LeanIX Data Interchange Format (LDIF).  A mapping file to the inbound processors will also be included.

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

=========================================================

BEWARE: Mac does not automatically source .bash_profile.  If you'll be using .bash_profile, make sure your .zshrc sources it:

```
if [ -f ~/.bash_profile ]; then
  . ~/.bash_profile
fi
```
=========================================================

Add a new line in your .bash_profile with the token

```
export SMARTSHEET_ACCESS_TOKEN="< your token here >"
```

Either source the .bash_profile or restart your terminal.

## sh_get_sheet.py

### Running

base_json is initally defined with the metadata for a Smartsheet LDIF.  Column names from Smartsheet are trasformed via the field_mapper dict to fit the LDIF schema.

```
python3 sh_get_sheet.py 
```

### Current functionality
- list all sheets 
- get data from all sheets
- transform data to ldif
- output ldif json file
