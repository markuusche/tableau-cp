import re
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
 
    def get_first_empty_row(self, sheet_name, start_range='A3'):
        match = re.match(r"([A-Z]+)(\d+)", start_range)
        if not match:
            raise ValueError("Invalid start_range format. Use something like 'A3' or 'AA5'")

        col_letters, start_row = match.groups()
        start_row = int(start_row)

        # request with correct fields and range
        sheet_metadata = self.service.spreadsheets().get(
            spreadsheetId=helper.env('sheetId'),
            ranges=[f'{sheet_name}!{col_letters}{start_row}:{col_letters}'],
            includeGridData=True,
            fields="sheets.data.rowData.values.effectiveValue,sheets.merges"
        ).execute()

        sheet = sheet_metadata['sheets'][0]
        rows = sheet['data'][0].get('rowData', [])
        merged_ranges = sheet.get('merges', [])

        def is_in_merged_range(row_index):
            for merge in merged_ranges:
                if merge['startRowIndex'] <= row_index < merge['endRowIndex']:
                    return True
            return False

        for i, row in enumerate(rows):
            row_index = start_row - 1 + i
            cell = row.get('values', [{}])[0]
            if 'effectiveValue' not in cell and not is_in_merged_range(row_index):
                return start_row + i

        return start_row + len(rows)
