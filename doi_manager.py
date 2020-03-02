import sys

from utils.gsheets_manager import retrieve_doi_mets, write_doi_mets
from utils.doi_mets import MetsHandler
from utils.global_settings import *



if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("""Insufficient number of inputs given. 
        Supply a command (build-doi = make proposed DOIs; build-xml = generate XMLs)
        Content type (serials, website, conference)
        and a GSheet template number.
        Examples: python doi_manager.py build-doi serials 1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k
                  python doi_manager.py build-xml serials 1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k
        """)
    else:
        if sys.argv[1] == 'build-doi':
            patron_provided_mets = retrieve_doi_mets(sys.argv[3])
            session = MetsHandler(sys.argv[2])
            dois = session.generate_pseudo_dois(MAIN_DOI_REGISTRY_SHEET, len(patron_provided_mets[8:]))
            write_doi_mets(sys.argv[3], dois)

        elif sys.argv[1] == 'build-xml':
            print("Retrieving metadata from template sheet...")
            patron_provided_mets = retrieve_doi_mets(sys.argv[3])
            session = MetsHandler(sys.argv[2])
            print("Assembling mets data...")
            session.assemble_patron_mets(patron_provided_mets)
            print("Organizing mets data into XML...")
            session_xml_results = session.build_serials_xml()
            if session_xml_results != False:
                print(session_xml_results)
            else:
                print("Failed to create XML")
        else:
            print("There may be a syntax error in your command entry. Try again.")
