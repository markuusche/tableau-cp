from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from src.utils.helper import Helper
helper = Helper()

class GoogleSheet:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.sevice_account = helper.env("cds")
        self.credentials = Credentials.from_service_account_file(self.sevice_account, scopes=self.scopes)
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet = self.service.spreadsheets()
    
    def update_cells(self, sheetName, cell, values):
        self.sheet.values().update(
            spreadsheetId=helper.env('sheetId'),
            range=f'{sheetName}!{cell}',
            valueInputOption='USER_ENTERED', 
            body={
                'values': [values]
            }
        ).execute()

    def populateSheet(self, sheetName, cell, values):
        creds = Credentials.from_service_account_file(helper.env('cds'))
        service = build('sheets', 'v4' , credentials=creds)
        range_name = f'{sheetName}!{cell}'
        
        sheet_metadata = service.spreadsheets().get(spreadsheetId=helper.env('sheetId')).execute()
        sheets = sheet_metadata.get('sheets', '')

        # get sheet Id
        sheetsIds = {
            sheet['properties']['title']: sheet['properties']['sheetId']
            for sheet in sheets
        }

        # add row above the data
        add_row = len(values)
        requests = [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheetsIds[sheetName],
                        "dimension": "ROWS",
                        "startIndex": 1, 
                        "endIndex": add_row + 1
                    },
                    "inheritFromBefore": False
                }
            }
        ]

        body = {
            'requests': requests
        }
   
        service.spreadsheets().batchUpdate(
            spreadsheetId=helper.env('sheetId'),
            body=body
        ).execute()


        body = {
            "values": values
        }

        service.spreadsheets().values().update(
            spreadsheetId=helper.env('sheetId'),
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
 
    def getCellValue(self):
        result = self.sheet.values().get(
            spreadsheetId=helper.env('sheetId'),
            range=f'{helper.env("sts")}!A2'
            ).execute()
        value = result.get('values', [])
        return value[0][0]
