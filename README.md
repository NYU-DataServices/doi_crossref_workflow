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

<pre>
doi_crossref_workflow
│───README.md
│───LICENSE    
│
│───xml_templates/
│   │  
│   │───serials_template.xml
|   │───serials_template.xml
│   └───website_template.xml
│   
│   
│───utils/
│   │
│   │───__init__.py   
│   │───doi_mets.py
│   │───sheets_creds_builder.py
│   └───gsheets_manager.py
│
└───doi_manage.py
</pre>


 1. Two utilities to handle separate aspects of the workflows:
 
> 	- **doi_mets.py** : classes and functions to handle instantiating a doi production session (including "minting" proposed DOIs and generating resulting XML). These might include:
><pre>class MetsHandler()</pre>
>A list-of-dictionaries object representing the set of all  objects receiving Dois in a single session, each object in turn represented by a dictionary with the keys as metadata fields (i.e. column headers from gsheet template) and values the user-entered values. Has methods that 1. produce proposed non-colliding DOI suffixes for each object, 2. produces alternative formats for re-updating the gsheet (e.g. a list-of-lists version of itself).<br/><br/>
 	
>	- **gsheets_manager.py**: classes and functions to handle the read/write of metadata to and from template gsheets we provide to users as well as reading from our current registry of CrossRef NYU DOIs to handle collisions. These might include:
><pre>def retrieve_doi_mets(sheet_id)</pre>
>A function to access the metadata in a gsheet template (identified using sheet_num) using previous oauth access object. <br/><br/>
 	 	
 2. **/xml_templates/serials_template.xml**, **website_template.xml**, etc.: set of XML formatted templates meeting CrossRef upload standards and Django template-like approach to passing variables in the content of tags.

 3. **doi_manager.py**: main script to run workflow. Should take as sysargv input the gsheet being used as the template and a setting as to whether this is a preliminary doi creation or an xml creation job.

 4. **/utils/sheets_creds_builder.py**, a one-time use utility to generate GSheets access

### Usage

Our sample GSheet template is at: [https://docs.google.com/spreadsheets/d/1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k/edit#gid=0](https://docs.google.com/spreadsheets/d/1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k/edit#gid=0)

#### Dependencies

Google's Sheets API modules

<pre>pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib</pre>

#### Pulling Journal, Issue, and Article Metadata from GSheet and generating XML

1. <pre>git clone https://github.com/NYU-DataServices/doi_crossref_workflow.git</pre>

2. <pre>cd doi_crossref_workflow</pre>

3. Copy <pre>credentials.json</pre> and <pre>doi_workflow_token.pickle</pre> files to this directory

4. After patron fills out basic information (journal and issue info; titles of articles), we can generate proposed DOIs for them:

<pre>python doi_manager.py build-doi serials GSHEET-ID</pre>

e.g.

<pre>python doi_manager.py build-doi serials 1lRSZcW-5me13p823kK7q_ow6cdZq1pw9-ohKENJ8N1k</pre>

5. This allows patron to then add the proposed DOIs to the e-copy and make the deposit in FDA, enabling Handle creation, record URL, etc. Patron then needs to finish filling out rest of GSheet so that we can make XML:

<pre>python doi_manager.py build-xml serials GSHEET-ID</pre>

6. If successful resulting XML will be produced in a 'crossref_xml_output.xml' file.

7. For cases where we just want to mint proposed DOIs to fill in gaps in legacy data, this option generates non-colliding DOIs based on our registry sheet and prints them out to terminal. The last parameter is the number of DOIs needed:

<pre>python doi_manager.py generate-pseudo-doi 5

To-Dos

If we need to re-do the DOIs creation, we want it to overwrite the current DOIs but preserve the article metadata already there
(or does it do that already?)

Error exception handling for Sheets/Validation step for GSheet for each of the two functions

Ability to custom name the output XML

Ability to include certain fields (like an abstract, page numbers) or not (would require "template" metadata object with a dictionary structure that reflects the fields wanted, plus XML templates that work for that type)