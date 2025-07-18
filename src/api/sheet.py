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

    def populateSheet(self, sheetName, cell, values, event=False):
        creds = Credentials.from_service_account_file(helper.env('cds'))
        service = build('sheets', 'v4' , credentials=creds)
        range_name = f'{sheetName}!{cell}'
        
        Id = helper.env('sheetId') if not event else helper.env('evtrckId')
        sheet_metadata = service.spreadsheets().get(spreadsheetId=Id).execute()
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
            spreadsheetId=Id,
            body=body
        ).execute()


        body = {
            "values": values
        }

        service.spreadsheets().values().update(
            spreadsheetId=Id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
 
    def getCellValue(self, event=False):
        Id = helper.env('evtrckId') if event else helper.env('sheetId')
        result = self.sheet.values().get(
            spreadsheetId=Id,
            range='Home!A2'
            ).execute()
        if 'values' in result:
            value = result.get('values', [])
            return value[0][0]
