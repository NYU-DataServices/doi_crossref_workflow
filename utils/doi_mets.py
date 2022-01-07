from utils.gsheets_manager import retrieve_doi_mets
from random import random
import uuid
from datetime import datetime
from global_settings import ALLOWED_CHARS, DEPOSITOR_NAME, DEPOSITOR_EMAIL_ADDRESS
import re


class MetsHandler:
    """
    Parent class with a few methods available to all child classes, namely ability to compose XML,
    normalize patron-written entries for XML outputs, format DOI URLs
    """

    def __init__(self, mets_type):
        self.mets_type = mets_type

    @staticmethod
    def starttag(tag_name):
        return "<" + tag_name + ">"

    @staticmethod
    def endtag(tag_name):
        return "</" + tag_name.split(" ")[0] + ">\n"

    @staticmethod
    def entry_normalizer(entry):
        entry = entry.strip()
        for replace in [("’", "'"), ("“", '"'), ("”", '"'), ("‘", "'"), ("&", "&amp;")]:
            entry = entry.replace(replace[0], replace[1])
        return entry

    @staticmethod
    def format_doi(url_doi):
        return url_doi.replace("https://doi.org/", "")

    @staticmethod
    def format_orcid(orcid_chars):
        if not re.search(r'^http', orcid_chars):
            return 'https://orcid.org/' + orcid_chars
        return orcid_chars

    def access_xml_template(self):
        with open("xml_templates/" + self.mets_type + "_template.xml") as f:
            xml = f.read()
            batch_uuid = str(uuid.uuid1())
            timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
            for temp_tag, value in [("{{ doi_batch_id }}", batch_uuid),
                                    ("{{ timestamp }}", timestamp),
                                    ("{{ depositor_name }}",DEPOSITOR_NAME),
                                    ("{{ depositor_email }}",DEPOSITOR_EMAIL_ADDRESS)]:
                xml = xml.replace(temp_tag, value)
            f.close()
        return xml

    def __str__(self):
        return "A DOI minting event metadata for %s group" % (self.mets_type)


class JournalMetsHandler(MetsHandler):
    """
    Object representing metadata for a journal/serial (issue, authors, citations) as a native python object,
    transforming the GSheet list of list formatting into a dictionary. Also has ability
    to transform that dictionary into a valid XML for CrossRef registry
    """

    def assemble_patron_mets(self, main_table, citation_table, author_table):
        self.mets_issue_dict = {
            'journal_metadata language="en"': {
                "full_title": main_table[2][0],
                'issn media_type="' + main_table[2][1] + '"': main_table[2][2],
            },
            "journal_issue": {
                "publication_date": {"month": main_table[5][1], "day": main_table[5][2], "year": main_table[5][0]},
                "journal_volume": {"volume": main_table[5][3]},
                "issue": main_table[5][4],
                "doi_data": {
                    "doi": self.format_doi(main_table[5][5]),
                    "resource": main_table[5][7],
                },
            },
        }

        self.mets_articles_list = [
            {
                'journal_article publication_type="full_text"': {
                    "titles": {"title": self.entry_normalizer(entry[1])},
                    "contributors": self.build_contributors(entry[2], author_table),
                    "jats:abstract": {"jats:p": self.entry_normalizer(entry[7])},
                    "publication_date": {"year": main_table[5][0]},
                    "pages": {"first_page": entry[3]},
                    "doi_data": {
                        "doi": self.format_doi(entry[4]),
                        "resource": entry[6],
                    },
                    "citation_list": self.build_citations(entry[0], citation_table),
                }
            }
            for entry in main_table[8:] if len(entry) > 1
        ]


    def build_contributors(self, author_entries, author_table):

        # Lookup table based on patron-provided author name metadata to find orcid and affiliation information

        author_info = {
            a_info[0].lower().strip().replace(",", "").replace(" ", "").replace(".", ""): {
                "orcid": self.format_orcid(a_info[1]),
                "role": a_info[3],
                "affiliation": a_info[2],
            }
            for a_info in author_table[2:] if len(a_info) == 4
        }

        # First pass to populate names based on article metadata

        contrib_mets = [
            {
                'person_name sequence="additional" contributor_role="author"': {
                    "given_name": self.entry_normalizer(name_entry.split(",")[1]),
                    "surname": self.entry_normalizer(name_entry.split(",")[0]),
                }
            }
            for name_entry in author_entries.split(";")
        ]

        # Second pass to add any affiliations or orcid IDs; we toss out a warning if no additional author data was found
        # either because the patron didn't spell the author names to match or because not provided at all.

        modified_contribs = []
        for contrib in contrib_mets:
            check_name = contrib['person_name sequence="additional" contributor_role="author"']["surname"].lower().strip().replace(" ", "").replace(".", "") + \
                         contrib['person_name sequence="additional" contributor_role="author"']["given_name"].lower().strip().replace(" ", "").replace(".", "")
            if check_name in author_info:
                if author_info[check_name]["affiliation"] != "":
                    contrib['person_name sequence="additional" contributor_role="author"'].update(
                        {
                            "affiliation": self.entry_normalizer(
                                author_info[check_name]["affiliation"]
                            )
                        }
                    )
                if author_info[check_name]["orcid"] != "":
                    contrib['person_name sequence="additional" contributor_role="author"'].update({"ORCID": author_info[check_name]["orcid"]})
                modified_contribs.append(contrib)
            else:
                print(
                    "Warning, no metadata info found/given for this author: ",
                    contrib['person_name sequence="additional" contributor_role="author"']["surname"],", ",
                    contrib['person_name sequence="additional" contributor_role="author"']["given_name"],
                )
                modified_contribs.append(contrib)

        return modified_contribs

    def build_citations(self, article_id, citations_table):
        citations_list = [
            self.entry_normalizer(cit[2])
            for cit in citations_table[2:] if cit[0] == article_id
        ]
        modified_citations_list = []
        refcount = 1
        for citation in citations_list:
            modified_citations_list.append(
                {
                    'citation key="ref=' + str(refcount) + '"': {"unstructured_citation": self.entry_normalizer(citation)}
                }
            )
            refcount += 1

        return modified_citations_list


    def build_serials_xml(self, custom_filename):
        """
        Using the dictionary containing all journal, issue, and article metadata create on instantiation of the class
        and subsequently populated by parsing the table of metadata supplied by user, this method when called pulls in
        the serials XML header template and populates its contents with an XML rendering of the dictionary
        It performs a quick check as well to make sure a serials minting event was initiated in the first place before
        attempting to build it into a serials XML
        :return: Full XML as string in CrossRef-appropriate upload format (if a serials object instantiated)
        :return: False if it wasn't given serials metadata to parse in the first place
        """

        xml = self.access_xml_template()

        insert_xml = ""

        ##
        #  This section builds the XML for the top-level (journal, issue) metadata
        ##

        for mets_section in self.mets_issue_dict:
            insert_xml += self.starttag(mets_section)

            for k, v in self.mets_issue_dict[mets_section].items():

                if isinstance(v, dict) and len(v) > 0:
                    insert_xml += self.starttag(k)
                    insert_xml += "".join(
                        [
                            self.starttag(tag) + content + self.endtag(tag)
                            for tag, content in v.items()
                        ]
                    )
                    insert_xml += self.endtag(k)

                elif len(v) > 0:
                    insert_xml += self.starttag(k) + v + self.endtag(k)

            insert_xml += self.endtag(mets_section)

        ##
        #  This section builds the XML for the issue's article-level metadata
        ##

        for article in self.mets_articles_list:

            for article_parent_met, article_met in article.items():
                insert_xml += self.starttag(article_parent_met)

                for met_child in article_met:

                    if isinstance(article_met[met_child], dict):

                        insert_xml += self.starttag(met_child)

                        for met_child_child in article_met[met_child]:

                            insert_xml += (
                                self.starttag(met_child_child)
                                + article_met[met_child][met_child_child]
                                + self.endtag(met_child_child)
                            )

                        insert_xml += self.endtag(met_child)

                    elif isinstance(article_met[met_child], list):

                        # We need a last check to weed out any empty lists, such as citation lists for articles with no citations

                        if len(article_met[met_child]) > 0:

                            insert_xml += self.starttag(met_child)

                            for met_child_child in article_met[met_child]:
                                insert_xml += self.starttag(
                                    list(met_child_child)[0]
                                )

                                insert_xml += "".join(
                                    [
                                        self.starttag(k) + v + self.endtag(k)
                                        for k, v in met_child_child[
                                            list(met_child_child)[0]
                                        ].items()
                                    ]
                                )

                                insert_xml += self.endtag(list(met_child_child)[0])

                            insert_xml += self.endtag(met_child)

                    else:
                        insert_xml += (
                            self.starttag(met_child)
                            + article_met[met_child]
                            + self.endtag(met_child)
                        )

                insert_xml += self.endtag(article_parent_met)

        xml = xml.replace("{{ issue_body }}", insert_xml)
        if custom_filename:
            filename = custom_filename + '.xml'
        else:
            filename = (
                self.mets_issue_dict['journal_metadata language="en"']["full_title"]
                .lower()
                .replace(" ", "")
                + "_"
                + self.mets_issue_dict["journal_issue"]["publication_date"]["year"]
                + "_crossref.xml"
            )
        with open(filename, "w") as f:
            f.write(xml)
            f.close
        return "XML was successfully created"


class ReportMetsHandler(MetsHandler):
    """
    Object representing metadata for a report as a native python object,
    transforming the GSheet list of list formatting into a dictionary. Returns an XML representation
    of metadata for CrossRef registry using report_template.xml using same methods for constructing
    XML outlined in JournalMetsHandler above
    """


class DoiMinter:
    """
    This class consists of a list of proposed DOIs that will not collide with previously created DOIs.
    It checks the current registry of all NYU-minted DOIs and then generates proposed DOIs based on set
    pararmeters for what characters can be included in DOIs
    :return: list of DOIs including full URL, e.g. ['https://doi.org/10.33682/8dkj-d93kd', 'https://doi.org/10.33682/3kd9s-9dfj3']
    """

    def mint(reg_sheet_id, number_needed):

        ##
        #   First pull the previously minted DOIs so we don't allow collisions, consult a list of allowable chars
        ##

        previous_suffixes = [
            row[7].replace("https://doi.org/10.33682/", "")
            for row in retrieve_doi_mets(reg_sheet_id, "registry")
        ]

        ##
        #   Generate the list of proposed DOIs
        ##

        allowed_chars = ALLOWED_CHARS
        generated_dois = []

        for j in range(0, number_needed + 1):
            pseudo_doi = ""
            while True:
                for i in range(0, 8):
                    pseudo_doi += allowed_chars[int(random() * len(allowed_chars))]
                    if i == 3:
                        pseudo_doi += "-"
                if pseudo_doi not in previous_suffixes:
                    generated_dois.append("https://doi.org/10.33682/" + pseudo_doi)
                    break
        return generated_dois

    def doi_registration(list_dois,title="",journal="",date="",unit="",contact="",url="",handle=""):
        """
        This function should write the DOIs passed as a pararamter (e.g. list of DOIs) to the registry GSheet
        In addition to the list of DOIs to register, it should include a series of optional parameters to write to the other columns of the sheet
        as well as auto-increment column A. The write step should be treated as an append to the values already in the GSheet to prevent accidentally
        overwriting what is there.
        :return:
        """