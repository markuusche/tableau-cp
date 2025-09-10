from src.helpers.helper import Helpers
import httplib2, google_auth_httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build

helper = Helpers()

class GoogleSheet:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.sevice_account = helper.env("cds")
        self.credentials = service_account.Credentials.from_service_account_file(self.sevice_account, scopes=self.scopes)
        self.http = httplib2.Http(timeout=180)
        self.auth = google_auth_httplib2.AuthorizedHttp(self.credentials, http=self.http)
        self.service = build('sheets', 'v4', http=self.auth)
        self.sheet = self.service.spreadsheets()

    def populateSheet(self, sheetName, cell, values, event=False):
        range_name = f'{sheetName}!{cell}'
        Id = helper.env('sheetId') if not event else helper.env('evtrckId')
        sheet_metadata = self.sheet.get(spreadsheetId=Id).execute()
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

        self.sheet.batchUpdate(
            spreadsheetId=Id,
            body={"requests": requests}
        ).execute()

        self.sheet.values().update(
            spreadsheetId=Id,
            range=range_name,
            valueInputOption='RAW',
            body={"values": values}
        ).execute()
 
    def getCellValue(self, range, event=False):
        Id = helper.env('evtrckId') if event else helper.env('sheetId')
        result = self.sheet.values().get(
            spreadsheetId=Id,
            range=f'{range}!A2'
            ).execute()
        if 'values' in result:
            value = result.get('values', [])
            return value[0][0]
