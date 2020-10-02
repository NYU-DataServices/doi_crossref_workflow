import sys

from utils.gsheets_manager import retrieve_doi_mets, write_doi_mets
from utils.doi_mets import MetsHandler
from utils.global_settings import *


if __name__ == "__main__":
    if sys.argv[1] != "generate-pseudo-doi" and len(sys.argv) < 4:
        print(
            """Insufficient number of inputs given. 
        Supply a command (build-doi = make proposed DOIs; build-xml = generate XMLs)
        Content type (serials, website, conference)
        and a GSheet template number.
        Examples: python doi_manager.py build-doi serials 1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k
                  python doi_manager.py build-xml serials 1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k
                  python doi_manager.py generate-pseudo-doi 2
        """
        )
    elif sys.argv[1] == "generate-pseudo-doi" and len(sys.argv) < 3:
        print(
            """Insufficient number of inputs given. 
        Supply a command (generate-pseudo-doi = generate a list of proposed DOIs)
        and the number of DOIs you need
        Example: 
                  python doi_manager.py generate-pseudo-doi 2
        """
        )
    else:
        if sys.argv[1] == "build-doi":
            print("Checking registry of previous DOIs and building proposed DOIs...")
            issue_level_mets = retrieve_doi_mets(sys.argv[3])
            session = MetsHandler(sys.argv[2])
            dois = session.generate_pseudo_dois(
                MAIN_DOI_REGISTRY_SHEET, len(issue_level_mets[8:])
            )
            print("Writing proposed DOIs to patron metadata sheet...")
            write_doi_mets(sys.argv[3], dois)
            print("Complete.")

        elif sys.argv[1] == "build-xml":
            print("Retrieving metadata from template sheet...")
            issue_level_mets = retrieve_doi_mets(sys.argv[3], "mets_main")
            citation_level_mets = retrieve_doi_mets(sys.argv[3], "mets_citations")
            author_level_mets = retrieve_doi_mets(sys.argv[3], "mets_authors")
            session = MetsHandler(sys.argv[2])
            print("Assembling mets data...")
            session.assemble_patron_mets(
                issue_level_mets, citation_level_mets, author_level_mets
            )
            print("Organizing mets data into XML...")
            session_xml_results = session.build_serials_xml()
            if session_xml_results != False:
                print(session_xml_results)
            else:
                print("Failed to create XML")
        elif sys.argv[1] == "generate-pseudo-doi":
            print("Checking registry of previous DOIs and building proposed DOIs...")
            session = MetsHandler("doi-list-only")
            dois = session.generate_pseudo_dois(
                MAIN_DOI_REGISTRY_SHEET, (int(sys.argv[2]) - 1)
            )
            print("Proposed DOIs are: \n")
            for doi in dois:
                print(doi)
        else:
            print("There may be a syntax error in your command entry. Try again.")
