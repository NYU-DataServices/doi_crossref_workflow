# doi_crossref_workflow
Workflow for establishing new NYU CrossRef DOIs and transforming required metatdata

### Steps in automation workflow

 1. Client fills in preliminary Google spreadsheet (copied from our template, but remaining in our owned Drive folder)  with title and publication info. At this point, these are mostly placeholders so we know how many DOIs to mint and how umbrella objects (e.g. a journal issue) relate to sub-objects (e.g. an article).
 2. Script reads from template GSheet and populates a DOI grouping object with the bare metadata and the prefix (Libraries or Press; in this case, always Libraries) to be assigned 
 3. Script proposes DOI suffixes, taking care not to create collision with current GSheet registry of NYU Libraries CrossRef DOIs (this may justify a read from that Registry first)
 4. Script modifies original templated sheet with the new DOIs.
 5. Client uses these DOIs to place them on electronic assets, e.g. the journal issue and article.
 6. Client fills out the remainder of the template with full metadata
 7. Second script reads the template again and transforms the full metadata to a valid XML record for upload to CrossRef. Script uses pre-established XML templates and fills it in with metadata gleaned from template GSheet

### Proposed components


doi_crossref_workflow
│───README.md
│───LICENSE    
│
│───xml_templates/
│   │  
│   │───serials_template.xml
│   └───website_template.xml
│   
│   
│───utils/
│   │
│   │───__init__.py   
│   │───doi_mets.py
│	│───gsheets_manager.py
│	└───xml_builder.py
│
└───doi_manage.py



 1. Three utilities to handle separate aspects of the workflows:
 
 	- **doi_mets.py**: classes and functions to handle instantiating a doi production session (including "minting" proposed DOIs). These might include:
 	
 	**class CrefDoi()** class, a list-of-dictionaries object representing the set of all objects receiving Dois in a single session, each object in turn represented by a dictionary with the keys as metadata fields (i.e. column headers from gsheet template) and values the user-entered values. Has methods that 1. produce proposed non-colliding DOI suffixes for each object, 2. produces alternative formats for re-updating the gsheet (e.g. a list-of-lists version of itself).	
 	
 	- **gsheets_manager.py**: classes and functions to handle the read/write of metadata to and from template gsheets we provide to users as well as reading from our current registry of CrossRef NYU DOIs to handle collisions. These might include:
 	
 	**def retrieve_doi_mets(sheet_num, gsheet_connection)** a function to access the metadata in a gsheet template (identified using sheet_num) using previous oauth access object.
 	
 	- **xml_builder.py**: functions to build a valid XML file using Django template-like variable replacement and some regex.
 	
 2. **/xml_templates/serials_template.xml**, **weebsite_template.xml**, etc.: set of XML formatted templates meeting CrossRef upload standards and Django template-like approach to passing variables in the content of tags.



