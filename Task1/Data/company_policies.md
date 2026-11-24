# Company Policies

## Employee Data and Workplace Guidelines

**Document type:** Sample project document\
**Purpose:** Demonstration data for the Client Legacy Data Ingestion &
Vector ETL Pipeline\
**Status:** Example policy content --- not an official policy of any
company

------------------------------------------------------------------------

## 1. Purpose and Scope

These sample guidelines describe how an organization might manage
employee information and general workplace processes. They are provided
for testing document ingestion, semantic chunking, metadata
preservation, embedding generation, and vector search.

## 2. Employee Records

Employee records may contain fields such as employee name, company name,
designation, experience, current location, qualification, and other
employment-related details.

-   Keep employee records accurate and up to date.
-   Correct incomplete or outdated information through an authorized
    process.
-   Treat blank, missing, or invalid values as unknown until verified.
-   Do not infer personal details that are not present in the source
    record.

## 3. Privacy and Confidentiality

Employee information may be personal or confidential.

-   Use employee data only for an authorized business or educational
    purpose.
-   Share records only with people who have a legitimate need to access
    them.
-   Remove or mask direct identifiers when they are not required for the
    task.
-   Do not publish private employee information in public repositories,
    demonstrations, or reports.
-   Use synthetic or anonymized records when possible.

## 4. Data Access Levels

For this demonstration project, records and documents can be assigned
the following example access levels:

### Public

Information approved for unrestricted public sharing.

### Internal

Information intended for authorized members of the organization or
project team.

### Confidential

Sensitive information that requires explicit authorization and stricter
handling.

These access labels are sample metadata values for the project; they do
not represent verified classifications from the employee dataset.

## 5. Data Quality and Cleaning

Before employee data is indexed:

-   Inspect column names and data types.
-   Identify missing values, duplicate rows, inconsistent spelling, and
    invalid formats.
-   Normalize text fields such as company names, designations, and
    locations where appropriate.
-   Preserve the original source file and document any transformations.
-   Avoid replacing missing values with invented employee information.

## 6. Document Ingestion and Semantic Search

The project pipeline may ingest CSV, PDF, and Markdown documents.

-   Convert each employee row into a readable text record before
    embedding it.
-   Split longer policy documents into meaningful chunks.
-   Preserve useful metadata, including source filename, department or
    team when available, document date when known, and access level.
-   Store each chunk with its embedding and metadata in a vector
    database such as ChromaDB or Qdrant.
-   Use cosine similarity or another supported distance measure to
    retrieve relevant content.
-   Apply metadata filters before returning results when access
    restrictions are required.

## 7. Metadata Guidelines

Suggested metadata fields for the demonstration pipeline include:

-   `source`: original filename
-   `document_type`: employee_record or policy
-   `department`: only when present in the source data
-   `designation`: only when present in the source data
-   `location`: only when present in the source data
-   `access_tier`: project-defined label such as internal
-   `chunk_id`: unique identifier for a text chunk

Do not label a field as verified if it was assigned only for
demonstration purposes.

## 8. Retention and Deletion

Keep only the data needed for the project. Remove test records and
generated vector indexes when they are no longer required. When a source
document changes, reprocess the document and remove obsolete chunks to
reduce stale search results.

## 9. Responsible Use

Search results should be treated as references to source material, not
as unquestionable facts. Verify important information against the
original source. Do not use this demonstration dataset to make
employment, compensation, or other consequential decisions about real
people.

## 10. Document Metadata

-   **Document name:** company_policies.md
-   **Dataset context:** Salaried employee profile dataset
-   **Content origin:** Synthetic example written for a student project
-   **Intended use:** Testing multi-format ingestion, chunking, metadata
    filtering, and semantic retrieval
-   **Official company policy:** No --- this is sample content only
