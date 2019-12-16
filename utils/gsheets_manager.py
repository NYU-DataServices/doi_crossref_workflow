import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


G_CREDS_FILE = 'credentials.json'
G_TOKEN_FILE = 'doi_workflow_token.pickle'


# We can adjust this to refer to the exact range in the gsheet template that is the actual data (i.e. not instructions rows)
METS_TEMPLATE_RANGE = 'Sheet1!A1:Z'


def retrieve_doi_mets(sheet_id):
    """
    This workflow follows from this https://developers.google.com/sheets/api/quickstart/python
    This function pulls the metadata available in the client-facing gsheet that we provide for user to
    add metadata information for object(s) to receive DOIs.
    Once authenticated, we only need to provide it with the sheet_id.
    It returns the contents of the gsheet as a list of lists; the first element of the list is the
    column headers and will be used later to generate dictionary keys (and to match against elements in the XML template)
    :param sheet_id: string representing the id for the sheets containing mets information
    :return: list of lists, each inner list a row fromo gsheet template; first list contains column headers/mets fields
    >>> read_template_mets('sample_sheet_id')
    [['dc.title','dc.contributors'],['Sample Title'],['Smith, Jane; Jones, Nancy']]
    """

    if os.path.exists(G_TOKEN_FILE):
        with open(G_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=METS_TEMPLATE_RANGE).execute()
    values = result.get('values', [])

    return values



def write_doi_mets(sheet_id, CrefDoiObject):
    """

    :param sheet_id: string representing the id for the sheets containing mets information
    :param CrefDoiObject: a special object representing in Python the set of doi mets for an upload/minting session
    :return:
    >>> write_doi_mets('sample_sheet_id', CrefDoi object)
    """

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    add_values_body = {"values": [append_row]}

    response = sheet.values().append(
        spreadsheetId=sheet_id, range=METS_TEMPLATE_RANGE, valueInputOption='RAW',
        insertDataOption='INSERT_ROWS', body=add_values_body).execute()

    return response






### MORE SAMPLE CODE BELOW


'''
def update_registrations(rows, gsheet_id):
    """
    THIS IS AN APPEND WORKFLOW
    :param rows:
    :param gsheet_id:
    :return:
    """
    creds = None

    if os.path.exists(G_TOKEN_FILE):
        with open(G_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    add_values_body = {"values": rows}
    add_bold = {"requests": [{
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 0,
                "endRowIndex": 1
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat(textFormat)"
        }
    }]}

    response1 = sheet.values().update(
        spreadsheetId=gsheet_id, range='Sheet1!A1:Z', valueInputOption='RAW',
        body=add_values_body).execute()

    response2 = service.spreadsheets().batchUpdate(spreadsheetId=gsheet_id, body=add_bold).execute()

    # At present, nothing done with these responses, which don't actually give a Http code, but a Google
    # specific summary of what was changed

    return (response1, response2)
'''



