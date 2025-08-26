# Credit Decision MVP V1

This project is a Minimum Viable Product (MVP) for a credit decision engine that uses a Large Language Model (LLM) to extract information from a free-text letter and applies a set of business rules to make a decision.

## Architecture

```mermaid
flowchart TD
  A[Entrada: Carta .txt / POST /decision] --> B[Extractor LLM]
  B -->|JSON| C[Pydantic Schema (validación)]
  B -. falla o sin red .-> H[Fallback Heurístico (regex)] --> C
  C --> D[Motor de Reglas (YAML thresholds)]
  D --> E{Lógica de decisión}
  E -->|Aprobado/Rechazado| F[Decision JSON + Rationale + Risk]
  C --> G[Logs (INFO/ERROR, masking)]
  subgraph Config
    I(.env: API keys, modelo)
    J(business_rules.yaml)
  end
  I -.-&gt; B
  J -.-&gt; D
  subgraph Interfaces
    K[CLI]
    L[FastAPI /extract, /decision]
  end
  A --> K
  A --> L
  L --> B
```

## How to Run

### 1. Installation

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file from the `.env.example` and add your API key for either Google Gemini or OpenAI.

```bash
cp .env.example .env
```

### 3. Run the CLI

To process a letter and get a decision, use the following command:

```bash
python -m app.main --letter examples/sample_letter.txt --rules business_rules.yaml
```

### 4. Run the API

To start the FastAPI server, run:

```bash
uvicorn app.main:api --reload
```

The API documentation will be available at `http://127.0.0.1:8000/docs`.

## Editing Business Rules

The business rules are defined in the `business_rules.yaml` file. You can modify the thresholds and the decision logic in this file.

## Resilience and Security

- **Resilience**: If the LLM API fails or is not available, the system will fallback to a heuristic-based extraction using regular expressions.
- **Security**: The API keys are loaded from the `.env` file, which is included in the `.gitignore` to prevent it from being committed to the repository.
