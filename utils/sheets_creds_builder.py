import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# We have some options for setting scopes based on the request; for now set to read/write as we should be able to control
# access of the workflow to the master CrossRef DOI registry by setting the appropriate NetID's Google permissions to RO

# SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def refresh_credentials():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time. So the following needs to be run once, and once pickle file created and authentication happens
    # it will now longer be needed

    creds = None

    # If there are no (valid) credentials available, let the user log in.

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run

        with open("../doi_workflow_token.pickle", "wb") as token:
            pickle.dump(creds, token)


refresh_credentials()
