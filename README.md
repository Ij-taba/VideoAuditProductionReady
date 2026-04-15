# AI Video Audit

An AI-powered compliance auditing pipeline for marketing, ad, and influencer video content.

This project takes a YouTube video URL, extracts transcript and on-screen text using Azure Video Indexer, retrieves the most relevant policy context from compliance PDFs using Azure AI Search, and generates a structured audit report with Azure OpenAI. The workflow is orchestrated with LangGraph to keep the pipeline modular, traceable, and easy to extend.

![Architecture](backend/src/data/Project2_Langgraph_Architecture.png)

## Overview

Manual review of promotional video content is slow, repetitive, and easy to make inconsistent. This project automates that process by combining multimodal extraction, retrieval, and LLM-based reasoning into a single audit pipeline.

The current flow is optimized for YouTube-based inputs and compliance knowledge stored in PDF documents.

## Key Features

- Extracts transcript, OCR text, and metadata from YouTube videos using Azure Video Indexer
- Indexes compliance and policy PDFs into a searchable vector store
- Retrieves the most relevant rule context with Azure AI Search
- Uses Azure OpenAI to evaluate content against retrieved policy guidance
- Produces a structured pass/fail compliance report with issue category and severity
- Orchestrates the end-to-end workflow with LangGraph
- Supports a mock mode for offline testing of the video indexing stage

## How It Works

1. A YouTube video URL is provided as input.
2. The pipeline downloads the video with `yt-dlp`.
3. Azure Video Indexer processes the video and returns transcript, OCR text, and metadata.
4. Compliance PDFs are chunked, embedded, and indexed for retrieval.
5. The pipeline searches for the most relevant compliance context using the extracted video content.
6. Azure OpenAI evaluates the transcript and OCR text against the retrieved rules.
7. The system returns a structured compliance decision and summary report.

## Architecture

The current LangGraph workflow contains two core nodes:

- `indexer`: downloads and indexes the video, then extracts transcript, OCR text, and metadata
- `audio_compliance`: retrieves compliance rules and generates the final audit result with Azure OpenAI

## Tech Stack

- Python 3.13
- LangGraph
- LangChain
- Azure OpenAI
- Azure AI Search
- Azure Video Indexer
- Azure Identity
- `yt-dlp`
- `PyPDF`
- `uv`

## Project Structure

```text
ComplianceQaPipeline/
|- backend/
|  |- src/
|  |  |- data/                  # Compliance PDFs and architecture asset
|  |  |- graph/                 # LangGraph state, nodes, workflow
|  |  |- scripts/               # Document indexing script
|  |  |- services/              # Azure Video Indexer integration
|- main.py                      # CLI entrypoint for workflow execution
|- pyproject.toml               # Project dependencies
|- README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Ij-taba/VideoAuditProductionReady.git
cd VideoAuditProductionReady/ComplianceQaPipeline
```

### 2. Install dependencies

Using `uv`:

```bash
uv sync
```

Or with `pip`:

```bash
pip install -e .
```

### 3. Create a local environment file

Create a `.env` file inside `ComplianceQaPipeline/` and add your Azure credentials and configuration.

## Environment Variables

The codebase currently references a few similar environment variable names across scripts. To avoid configuration issues, set the following values in your local `.env`:

```env
AZURE_OPENAI_API_VERSION=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=
AZURE_OPENAI_EMBEDDING_DEPLOYEMENT=

AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_API_KEY=
AZURE_SEARCH_KEY=
AZURE_SEARCH_INDEX_NAME=
AZURE_SEARCH_INDEX=

AZURE_VI_ACCOUNT_ID=
AZURE_VI_LOCATION=
AZURE_SUBSCRIPTION_ID=
AZURE_RESOURCE_GROUP=
AZURE_VI_NAME=

VIDEO_INDEXER_MOCK=false
```

Notes:

- `VIDEO_INDEXER_MOCK=true` lets you test the pipeline without calling Azure Video Indexer
- Both `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` and `AZURE_OPENAI_EMBEDDING_DEPLOYEMENT` are listed because the current code references the typo variant in one place
- Both `AZURE_SEARCH_API_KEY` and `AZURE_SEARCH_KEY`, plus both index name variants, are listed because different files currently reference different names

## Index Compliance Documents

Before running the audit flow, index the PDF rule documents into Azure AI Search:

```bash
uv run python backend/src/scripts/index_document.py
```

The project currently includes sample PDFs in:

- `backend/src/data/youtube-ad-specs.pdf`
- `backend/src/data/1001a-influencer-guide-508_1.pdf`

## Run the Project

Run the CLI workflow:

```bash
uv run python main.py
```

The current demo run uses a sample YouTube URL defined in `main.py`.

## Example Output

```json
{
  "compliance_results": [
    {
      "category": "Claim Validation",
      "severity": "CRITICAL",
      "description": "A non-compliant or unsupported claim was detected."
    }
  ],
  "status": "FAIL",
  "final_report": "The video contains compliance issues that should be reviewed before publishing."
}
```

## Use Cases

- Brand and ad compliance review
- Influencer content approval workflows
- Pre-publication audit pipelines for marketing teams
- AI-assisted policy validation for multimodal media

## Why This Project Matters

This project demonstrates a practical LLMOps workflow that combines retrieval, multimodal extraction, and structured reasoning for a real business problem. Instead of using a generic chatbot pattern, it applies RAG and workflow orchestration to automate compliance analysis in a way that is explainable, scalable, and closer to production use cases.

## Current Limitations

- The API layer is not fully implemented yet
- The demo entrypoint is CLI-based
- The workflow currently focuses on YouTube inputs
- Some configuration names should be standardized across the codebase

## Future Improvements

- Add a production-ready FastAPI service
- Store audit reports in a database
- Add evaluation and benchmarking for audit quality
- Support more video sources and file uploads
- Standardize environment configuration and error handling
- Add CI/CD and containerized deployment

## Author

Built by Ijtaba as an applied AI / LLMOps project focused on real-world video compliance automation.
