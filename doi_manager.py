import sys

from utils.gsheets_manager import retrieve_doi_mets, write_doi_mets
from utils.doi_mets import JournalMetsHandler, DoiMinter
from global_settings import *


if __name__ == "__main__":
    if sys.argv[1] != "generate-pseudo-doi" and len(sys.argv) < 4:
        print(
            """Insufficient number of inputs given. 
        Supply a command (build-doi = make proposed DOIs; build-xml = generate XMLs)
        Content type (serials, website, report)
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
            dois = DoiMinter.mint(
                MAIN_DOI_REGISTRY_SHEET, len(issue_level_mets[8:])
            )
            print("Writing proposed DOIs to patron metadata sheet...")
            write_doi_mets(sys.argv[3], dois)
            print("Complete.")

        elif sys.argv[1] == "retrieve-fda-handles":
            print("Consulting FDA (archive.nyu.edu) for record information...")
            """
            The remaining steps here should:
                1. Retrieve the issue_level_mets along the lines of build-doi step above (this will grab all info in the template's "issue" tab); isolate and organize info needed for calls to FDA API
                2. Use journal name and vol/issue information to locate the journal issue handle in the FDA using calls to API
                3. Offer warnings and catch exceptions for any issue or article not found in the system so user troubleshoot and adjust GSheet info as needed
                4. Print out a summary of matches made and indicate to user that something has happened post API call
                5. Write the Handles to the provided GSheet in the correct column using an updated write_doi_mets() function in utils/gsheets_manageer.py
                6. Report that write-out was successful
            """

        elif sys.argv[1] == "build-xml":
            print("Retrieving metadata from template sheet...")
            issue_level_mets = retrieve_doi_mets(sys.argv[3], "mets_main")
            citation_level_mets = retrieve_doi_mets(sys.argv[3], "mets_citations")
            author_level_mets = retrieve_doi_mets(sys.argv[3], "mets_authors")
            try:
                custom_filename = sys.argv[4]
            except:
                custom_filename = False
            session = JournalMetsHandler(sys.argv[2])
            print("Assembling mets data...")
            session.assemble_patron_mets(
                issue_level_mets, citation_level_mets, author_level_mets
            )
            print("Organizing mets data into XML...")
            session_xml_results = session.build_serials_xml(custom_filename)
            if session_xml_results != False:
                print(session_xml_results)
            else:
                print("Failed to create XML")
        elif sys.argv[1] == "generate-pseudo-doi":
            print("Checking registry of previous DOIs and building proposed DOIs...")
            dois = DoiMinter.mint(
                MAIN_DOI_REGISTRY_SHEET, (int(sys.argv[2]) - 1)
            )
            print("Proposed DOIs are: \n")
            for doi in dois:
                print(doi)
        else:
            print("There may be a syntax error in your command entry. Try again.")
