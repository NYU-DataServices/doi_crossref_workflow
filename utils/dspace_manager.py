# import ?

"""
If there is a stable DSpace wrapper that does the steps below more easily, we can go for using it.
Otherwise my preference is to use requests and formed GET requests, then handle the parsing
of what FDA gives back here and perform the matching

"""


def fda_get()
    """
    This function could perform a simple preliminary GET of the data, either everything in the FDA that subsequent steps would parse
    and perform a search to match and retrieve handles, or a subset if there is a way to grab only relevant FDA data without falsely missing relevant hits
    :return: a list-based or dictionary-based object that can be easily searched to perform matches against GSheet issue/article data
    """

def mets_match(issue_article_metadata, fda_data)
    """
    
    :param issue_article_metadata: a list or dict based representation of the issue and article information present in the patron's GSheet
    :param fda_data: a list or dict based representation of the FDA's info to match against
    :return: probably an ordered list that can be directly written to the GSheet, ordered so that the issue Handle is last and the article Handles are in correct order as rows in GSheet
    """