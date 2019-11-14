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




