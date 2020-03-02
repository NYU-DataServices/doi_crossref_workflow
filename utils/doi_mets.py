from utils.gsheets_manager import retrieve_doi_mets
from random import random


class MetsHandler():
    def __init__(self, mets_type):
        self.mets_type = mets_type


    def pull_patron_mets(self, table):
        self.mets_issue_dict = {"journal_metadata lang=\"en\"":
                                    {"full_title": table[2][0],
                                     "issn media_type=\"" + table[2][1] + "\"": table[2][2]
                                     },
                                "journal_issue": {
                                    "publication_date media_type=\"" + table[2][1] + "\"": {"year": table[5][0]},
                                    "journal_volume": {"volume": table[5][1]},
                                    "issue": table[5][2]
                                }}
        self.mets_articles_list = [
            {"journal_article publication_type=\"full_text\"": {
                "titles": {"title": entry[1]},
                "contributors": [{"person_name contributor_role=\"author\"": {
                    "given_name": "",
                    "surname": ""}}],
                "publication_date media_type=\"print\"": {"year": entry[3][0:5]},
                "pages": {"first_page": ""},
                "doi_data": {"doi": entry[7], "resource": entry[8]}
            }
            }
            for entry in table[8:]]

    def generate_pseudo_dois(self, reg_sheet_id, number_needed):
        """
        This function checks the current registry of all NYU-minted DOIs and then generates proposed DOIs
        for upload to CrossRef that do not collide with previous DOIs
        :return:
        1KXyBq47ciMnQD0mTns4Q9OUZC11kISIWA0yh6hjyLBo
        """

        ##
        #   First pull the previously minted DOIs so we don't allow collisions, build a list of allowable chars
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

    @staticmethod
    def starttag(tag_name):
        return '<' + tag_name + '>'

    @staticmethod
    def endtag(tag_name):
        return '</' + tag_name.split(' ')[0] + '>\n'

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
            with open('crossref_xml_output.xml', 'w') as f:
                f.write(xml)
                f.close
            return("XML was successfully created")
        else:
            return False

    def __str__(self):
        return "A DOI minting event metadata for %s group" % (self.mets_type)