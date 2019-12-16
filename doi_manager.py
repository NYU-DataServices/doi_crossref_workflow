import sys

from utils.gsheets_manager import retrieve_doi_mets
from utils.doi_mets import MetsHandler



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Insufficient number of inputs given. Supply a content type (serials, website, conference) and a GSheet template number")
    else:
        patron_provided_mets = retrieve_doi_mets(sys.argv[2])
        session = MetsHandler(sys.argv[1], patron_provided_mets)
        session_xml_results = session.build_serials_xml()
        if session_xml_results != False:
            print(session_xml_results)
        else:
            print("Failed to create XML")