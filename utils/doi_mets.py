



class MetsHandler():
    def __init__(self, mets_type, table):
        self.mets_type = mets_type
        self.mets_issue_dict = {"journal_metadata lang=\"en\"":
                             {"full_title": table[2][0],
                              "issn media_type=\"" + table[2][1] + "\"": table[2][2]
                              },
                             "journal_issue": {
                                 "publication_date media_type=\"" + table[2][1] + "\"": {"year":table[5][0]},
                                 "journal_volume": {"volume": table[5][1]},
                                 "issue": table[5][2]
                             }}
        self.mets_articles_list = [
                                 {"journal_article publication_type=\"full_text\"":{
                                    "titles": {"title":entry[1]},
                                    "contributors": [{"person_name contributor_role=\"author\"":{
                                        "given_name": "",
                                        "surname": ""}}],
                                    "publication_date media_type=\"print\"": {"year":entry[3][0:5]},
                                    "pages": {"first_page": ""},
                                    "doi_data": {"doi": entry[7],"resource": entry[8]}
                                    }
                                 }
                                for entry in table[8:]]

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
