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
    
    def getSheetID(self, Id: str | int):
        sheet_metadata = self.sheet.get(spreadsheetId=Id).execute()
        sheets = sheet_metadata.get('sheets', '')
        
        sheetsIds = {
            sheet['properties']['title']: sheet['properties']['sheetId']
            for sheet in sheets
        }
        
        return sheetsIds
    
    def sheet_request_body(self, Id: str | int, sheetName: str, startIndex: int = 1):
        sheetsIds = self.getSheetID(Id)
        return [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheetsIds[sheetName],
                        "dimension": "ROWS",
                        "startIndex": startIndex, 
                    },
                }
            }
        ]

    def populateSheet(self, sheetName: str, cell: str, values: list, **options):
        """
        Populates sheet in single request, instead of 1 by 1
        """
        
        if options.get("event"):
            Id = helper.env('evtrckId')
        elif options.get("emailVerification"):
            Id = helper.env("evsheet")
        elif options.get("popular"):
            Id = helper.env("popularCompleteData")
        elif options.get("dataIndex"):
            Id = helper.env('dataIndicator')
        else:
            Id = helper.env('sheetId')
        
        if options.get("singleData"):
                dataOption = "OVERWRITE" if options.get("popular") else "INSERT_ROWS"
                self.sheet.values().append(
                spreadsheetId=Id,
                range=f"{sheetName}!{cell}",
                valueInputOption='RAW',
                insertDataOption=dataOption,
                body={"values": values}
            ).execute()
        else:
            add_row = len(values)
            requests = self.sheet_request_body(Id, sheetName)
            requests[0]["insertDimension"]["range"]["endIndex"] = add_row + 1
            requests[0]["insertDimension"]["inheritFromBefore"] = False

            self.sheet.batchUpdate(
                spreadsheetId=Id,
                body={"requests": requests}
            ).execute()

            range_name = f'{sheetName}!{cell}'
            self.sheet.values().update(
                spreadsheetId=Id,
                range=range_name,
                valueInputOption='RAW',
                body={"values": values}
            ).execute()
 
    def getCellValue(self, sheetName: str, event: bool = False):
        """
        Use for checking cell of the given cell is eq or not to expected.
        """
        
        Id = helper.env('evtrckId') if event else helper.env('sheetId')
        result = self.sheet.values().get(
            spreadsheetId=Id,
            range=f'{sheetName}!A2'
            ).execute()

        if 'values' in result:
            value = result.get('values', [])
            return value[0][0]

    def clearDeleteSheet(self, Id: str | int, sheetName: str):
        requests = self.sheet_request_body(Id, sheetName, startIndex=2)
        requests[0]["deleteDimension"] = requests[0].pop("insertDimension")

        self.sheet.values().clear(
            spreadsheetId=Id,
            range=f"{sheetName}!A2:I"
        ).execute()
        
        self.sheet.batchUpdate(
            spreadsheetId=Id,
            body={"requests": requests}
        ).execute()
