import pickle
import json
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from global_settings import (
    G_CREDS_FILE,
    G_TOKEN_FILE,
    METS_SERIALS_TEMPLATE_RANGE,
    REGISTRY_TEMPLATE_RANGE,
    METS_SERIALS_DOI_COLUMN_RANGE,
    METS_SERIALS_ISSUE_DOI_COLUMN_RANGE,
    REGISTRY_TEMPLATE_COLUMN_RANGE,
    METS_CITATIONS_TEMPLATE_RANGE,
    METS_AUTHORS_TEMPLATE_RANGE,
    SCOPES,
)


def retrieve_doi_mets(sheet_id, retrieve_type="mets_main"):
    """
    This workflow follows from this https://developers.google.com/sheets/api/quickstart/python
    This function pulls the metadata available in the client-facing gsheet that we provide for user to
    add metadata information for object(s) to receive DOIs.
    Once authenticated, we only need to provide it with the sheet_id.
    It returns the contents of the gsheet as a list of lists; the first element of the list is the
    column headers and will be used later to generate dictionary keys (and to match against elements in the XML template)
    :param sheet_id: string representing the id for the sheets containing mets information
    :return: list of lists, each inner list a row fromo gsheet template; first list contains column headers/mets fields
    >>> read_template_mets('sample_sheet_id', 'mets_main')
    [['dc.title','dc.contributors'],['Sample Title'],['Smith, Jane; Jones, Nancy']]
    """
    if retrieve_type == "mets_main":
        range = METS_SERIALS_TEMPLATE_RANGE
    elif retrieve_type == "mets_citations":
        range = METS_CITATIONS_TEMPLATE_RANGE
    elif retrieve_type == "mets_authors":
        range = METS_AUTHORS_TEMPLATE_RANGE
    elif retrieve_type == "registry":
        range = REGISTRY_TEMPLATE_RANGE

    if os.path.exists(G_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(G_TOKEN_FILE)

    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range).execute()
    values = result.get("values", [])

    return values


def write_doi_mets(sheet_id, append_vals, retrieve_type="mets_main"):
    """
    Function to write values to our GSheets. Currently, it is configured to write to cells only in two circumstances:
    1. To write the proposed DOI URLs to column H in the patron-facing template
    TODO: 2. To write the proposed DOI URLS to the master registry of NYU DOIs
    :param sheet_id: string representing the id for the sheets containing mets information
    :param retrieve_type: whether for the patron-facing sheet or the NYU DOI registry
    :return:
    >>> write_doi_mets('sample_sheet_id', [['val1','val2']] 'mets_main')
    """
    if retrieve_type == "mets_main":
        range = METS_SERIALS_DOI_COLUMN_RANGE + str(8 + len(append_vals))
        issue_doi_range = METS_SERIALS_ISSUE_DOI_COLUMN_RANGE
    elif retrieve_type == "handles":
        """
        Here, we should set a range appropriate to the correct columns for writing Handles in a fashion similar to the approach in mets_main
        """

    elif retrieve_type == "registry":
        range = REGISTRY_TEMPLATE_COLUMN_RANGE

    if os.path.exists(G_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(G_TOKEN_FILE)

    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()

    """
    Quick note about the append_vals below. It is currently set to write all DOIs provided in the list except for the last one, which is reserved for
    the issue's DOI. The DOIs don't have any particular meaning at this point, so they are assigned without regard to order.
    But when fed a list of Handles, we need to order them correctly in the append_vals parameter passed above so that 
    the issue-level Handle is at the end of the list. Furthermore, the Handles have to be in the order of the articles in the GSheet rows,
    otherwise they won't match the articles correctly.
    """

    add_values_body = {"values": [append_vals[:-1]], "majorDimension": "COLUMNS"}

    response = (
        sheet.values()
        .append(
            spreadsheetId=sheet_id,
            range=range,
            valueInputOption="RAW",
            body=add_values_body,
        )
        .execute()
    )

    """
    The step below is a second call to write the issue-level DOI to the correct place (treated as last proposed DOI in the list)
    To moodify it to accommodate writing the Handle, the best approach would be to modify this range= parameter in the 
    response_2 object below so that it refers to either the DOI or the Handle location in the issue metadata rows on the GSheet,
    and is set above in the if/elif section
    """

    add_values_body_issue_dois = {
        "values": [[append_vals[-1]]],
        "majorDimension": "COLUMNS",
    }

    response_2 = (
        sheet.values()
        .append(
            spreadsheetId=sheet_id,
            range=issue_doi_range,
            valueInputOption="RAW",
            body=add_values_body_issue_dois,
        )
        .execute()
    )

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
        
    response = sheet.values().append(
        spreadsheetId=sheet_id, range=range, valueInputOption='RAW',
        insertDataOption='INSERT_ROWS', body=add_values_body).execute()

    response2 = service.spreadsheets().batchUpdate(spreadsheetId=gsheet_id, body=add_bold).execute()

    # At present, nothing done with these responses, which don't actually give a Http code, but a Google
    # specific summary of what was changed

    return (response1, response2)
'''
