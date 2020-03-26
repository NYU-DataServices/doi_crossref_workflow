from utils.gsheets_manager import retrieve_doi_mets
from random import random
import uuid
from datetime import datetime


class MetsHandler():
    def __init__(self, mets_type):
        self.mets_type = mets_type


    def assemble_patron_mets(self, main_table, citation_table, author_table):
        self.mets_issue_dict = {"journal_metadata language=\"en\"":
                                    {"full_title": main_table[2][0],
                                     "issn media_type=\"" + main_table[2][1] + "\"": main_table[2][2]
                                     },
                                "journal_issue": {
                                    "publication_date": {"year": main_table[5][0]},
                                    "journal_volume": {"volume": main_table[5][1]},
                                    "issue": main_table[5][2],
                                    "doi_data": {"doi": main_table[5][3], "resource": main_table[5][5]}
                                }}

        self.mets_articles_list = [
            {"journal_article publication_type=\"full_text\"": {
                "titles": {"title": self.entry_normalizer(entry[1])},
                "contributors": self.build_contributors(entry[2], author_table),
                "publication_date": {"year": main_table[5][0]},
                "pages": {"first_page": entry[3]},
                "doi_data": {"doi": entry[4], "resource": entry[6]},
                "citation_list" : self.build_citations(entry[0], citation_table)
            }
            }
            for entry in main_table[8:] if len(entry) > 1]


    def generate_pseudo_dois(self, reg_sheet_id, number_needed):
        """
        This function checks the current registry of all NYU-minted DOIs and then generates proposed DOIs
        for upload to CrossRef that do not collide with previous DOIs
        :return:
        """

        ##
        #   First pull the previously minted DOIs so we don't allow collisions, consult a list of allowable chars
        ##

        previous_suffixes = [row[7].replace('https://doi.org/10.33682/','') for row in retrieve_doi_mets(reg_sheet_id, 'registry')]
        allowed_chars = ['0','1','2','3','4','5','6','7','8','9',
                         'a','b','c','d','e','f','g','h','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z']

        ##
        #   Generate the list of proposed DOIs
        ##

        generated_dois = []

        for j in range(0,number_needed + 1):
            pseudo_doi = ""
            while True:
                for i in range(0,8):
                    pseudo_doi += allowed_chars[int(random() * len(allowed_chars))]
                    if i == 3:
                        pseudo_doi += '-'
                if pseudo_doi not in previous_suffixes:
                    generated_dois.append('https://doi.org/10.33682/' + pseudo_doi)
                    break
        return generated_dois


    def build_contributors(self, author_entries, author_table):

        # Lookup table based on patron-provided author metadata to find orcid and affiliation information

        author_info = { a_info[0].lower().strip().replace(',', '').replace(' ', '').replace('.', ''): {"orcid": a_info[1],
                                'role': a_info[3], 'affiliation': a_info[2]} for a_info in author_table[2:] if len(a_info) == 4}

        # First pass to populate names based on article metadata

        contrib_mets = [{"person_name sequence=\"additional\" contributor_role=\"author\"": {
            "given_name": self.entry_normalizer(name_entry.split(',')[1]),
            "surname": self.entry_normalizer(name_entry.split(',')[0])}} for name_entry in author_entries.split(';')]

        # Second pass to add any affiliations or orcid IDs; we toss out a warning if no additional author data was found
        # either because the patron didn't spell the author names to match or because not provided at all.

        modified_contribs = []
        for contrib in contrib_mets:
            check_name = contrib["person_name sequence=\"additional\" contributor_role=\"author\""]["surname"].lower().strip().replace(' ','').replace('.', '') + \
                         contrib["person_name sequence=\"additional\" contributor_role=\"author\""]["given_name"].lower().strip().replace(' ', '').replace('.', '')
            if check_name in author_info:
                if author_info[check_name]["affiliation"] != '':
                    contrib["person_name sequence=\"additional\" contributor_role=\"author\""].update({
                        "affiliation": author_info[check_name]["affiliation"]
                    })
                if author_info[check_name]["orcid"] != '':
                    contrib["person_name sequence=\"additional\" contributor_role=\"author\""].update({
                        "ORCID": author_info[check_name]["orcid"]
                    })
                modified_contribs.append(contrib)
            else:
                print("Warning, no metadata info found/given for this author: ",
                      contrib["person_name sequence=\"additional\" contributor_role=\"author\""]["surname"], ", ",
                      contrib["person_name sequence=\"additional\" contributor_role=\"author\""]["given_name"])
                modified_contribs.append(contrib)

        return modified_contribs

    def build_citations(self, article_id, citations_table):
        citations_list = [self.entry_normalizer(cit[2]) for cit in citations_table[2:] if cit[0] == article_id]
        modified_citations_list = []
        refcount = 1
        for citation in citations_list:
            modified_citations_list.append({"citation key=\"ref=" + str(refcount) + "\"" : {"unstructured_citation": citation}})
            refcount+=1

        return modified_citations_list


    @staticmethod
    def starttag(tag_name):
        return '<' + tag_name + '>'

    @staticmethod
    def endtag(tag_name):
        return '</' + tag_name.split(' ')[0] + '>\n'

    @staticmethod
    def entry_normalizer(entry):
        entry = entry.strip()
        for replace in [("’","'"), ("“", '"'), ("”", '"'), ("‘", "'"), ("&", "&amp;")]:
            entry = entry.replace(replace[0], replace[1])
        return entry

    def build_serials_xml(self):
        """
        Using the dictionary containing all journal, issue, and article metadata create on instantiation of the class
        and subsequently populated by parsing the table of metadata supplied by user, this method when called pulls in
        the serials XML header template and populates its contents with an XML rendering of the dictionary
        It performs a quick check as well to make sure a serials minting event was initiated in the first place before
        attempting to build it into a serials XML
        :return: Full XML as string in CrossRef-appropriate upload format (if a serials object instantiated)
        :return: False if it wasn't given serials metadata to parse in the first place
        """

        if self.mets_type == 'serials':

            with open('xml_templates/' + self.mets_type + '_template.xml') as f:
                xml = f.read()
                batch_uuid = str(uuid.uuid1())
                timestamp = datetime.today().strftime('%Y%m%d')
                xml = xml.replace('{{ doi_batch_id }}', batch_uuid).replace('{{ timestamp }}', timestamp)
                f.close()

            insert_xml = ""

            ##
            #  This section builds the XML for the top-level (journal, issue) metadata
            ##

            for mets_section in self.mets_issue_dict:
                insert_xml += self.starttag(mets_section)

                for k, v in self.mets_issue_dict[mets_section].items():

                    if isinstance(v, dict):
                        insert_xml += self.starttag(k)
                        insert_xml += ''.join([self.starttag(tag) + content + self.endtag(tag)
                                               for tag, content in v.items()])
                        insert_xml += self.endtag(k)

                    else:
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

                                insert_xml += self.starttag(met_child_child) + \
                                                article_met[met_child][met_child_child] + \
                                              self.endtag(met_child_child)

                            insert_xml += self.endtag(met_child)

                        elif isinstance(article_met[met_child], list):

                            # We need a last check to weed out any empty lists, such as citation lists for articles with no citations

                            if len(article_met[met_child]) > 0:

                                insert_xml += self.starttag(met_child)

                                for met_child_child in article_met[met_child]:
                                    insert_xml += self.starttag(list(met_child_child)[0])

                                    insert_xml += ''.join([self.starttag(k) + v + self.endtag(k) \
                                                           for k,v in met_child_child[list(met_child_child)[0]].items()])

                                    insert_xml += self.endtag(list(met_child_child)[0])

                                insert_xml += self.endtag(met_child)

                        else:
                            insert_xml += self.starttag(met_child) + article_met[met_child] + self.endtag(met_child)

                    insert_xml += self.endtag(article_parent_met)

            xml = xml.replace('{{ issue_body }}', insert_xml)
            filename = self.mets_issue_dict["journal_metadata language=\"en\""]["full_title"].lower().replace(' ','') + \
                       "_" + self.mets_issue_dict["journal_issue"]["publication_date"]["year"] + "_crossref.xml"
            with open(filename, 'w') as f:
                f.write(xml)
                f.close
            return("XML was successfully created")
        else:
            return False

    def __str__(self):
        return "A DOI minting event metadata for %s group" % (self.mets_type)