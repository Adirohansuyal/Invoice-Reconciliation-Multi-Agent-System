# Invoice Reconciliation Multi-Agent System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, production-ready multi-agent system for automated invoice reconciliation using LangGraph and large language models.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Test Coverage](#test-coverage)
- [Limitations & Future Enhancements](#limitations--future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Overview

This system automates invoice reconciliation workflows by leveraging a multi-agent architecture to process supplier invoices, match them against purchase orders, detect discrepancies, and make intelligent approval decisions. The system handles real-world document complexity including scanned PDFs, varied formats, and incomplete data.

### Problem Statement

Manual invoice reconciliation in enterprise environments is:
- **Time-intensive**: Requires significant human resources for document review
- **Error-prone**: Subject to human oversight and inconsistent application of rules
- **Non-scalable**: Processing time increases linearly with invoice volume
- **Risk-exposed**: Vulnerable to fraud, duplicate payments, and compliance violations

### Solution

This multi-agent system automates 80-90% of invoice reconciliation workflows while maintaining human oversight for high-risk cases through intelligent escalation mechanisms.

The system also includes a professional review dashboard that mirrors real enterprise workflows by separating automatically approved invoices from those requiring human intervention, complete with PDF previews, agent reasoning traces, and AI-generated explanations for escalations.

## Key Features

- **Intelligent Document Processing**  
  OCR-based extraction combined with LLM-powered structuring to handle scanned PDFs, rotated documents, and heterogeneous invoice templates.

- **True Multi-Agent Orchestration**  
  LangGraph-based agent coordination with explicit state handoffs, conditional routing, and non-linear execution paths.

- **Robust PO Matching Engine**  
  Hybrid matching strategy using direct PO references, fuzzy string matching, and confidence scoring to handle incomplete or missing identifiers.

- **Discrepancy Detection & Risk Classification**  
  Automated detection of price mismatches, quantity discrepancies, missing items, and missing PO references with severity-aware classification.

- **Confidence-Based Decision Making**  
  Automated routing into:
  - AUTO_APPROVE  
  - REQUEST_CLARIFICATION  
  - ESCALATE_TO_HUMAN  
  based on discrepancy severity and match confidence.

- **Human-in-the-Loop Workflow**  
  High-risk or low-confidence invoices are escalated to human review with full context, supporting safe financial decision-making.

- **LLM-Generated Human Review Explanation**  
  For invoices requiring manual review, the system generates a concise natural-language explanation describing *why* human intervention is required.

- **Real-Time Agent Reasoning Transparency**  
  Live, step-by-step streaming of each agent’s internal reasoning, displayed as a chat-style activity feed with agent-specific color coding.

- **Interactive Review Dashboard**  
  Streamlit-based UI featuring:
  - Multi-invoice batch upload
  - Auto-Approved vs Human Review tabs
  - Side-by-side PDF preview and reasoning trace
  - Structured outputs and audit-friendly explanations

- **Fault-Tolerant Design**  
  Graceful handling of OCR failures, LLM parsing errors, missing data, and ambiguous matches without system crashes.

### Decision Outcomes

- **AUTO_APPROVE**: Clean matches with no material discrepancies
- **REQUEST_CLARIFICATION**: Minor issues requiring supplier follow-up
- **ESCALATE_TO_HUMAN**: Critical discrepancies requiring manual review

## System Architecture

```
┌─────────────────────┐
│  Document Upload    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Document    │───▶│   Matching   │───▶│ Discrepancy  │ │
│  │    Agent     │    │    Agent     │    │    Agent     │ │
│  └──────────────┘    └──────────────┘    └──────┬───────┘ │
│         │                                         │         │
│         │                                         ▼         │
│         │                              ┌──────────────┐    │
│         │                              │  Resolution  │    │
│         │                              │    Agent     │    │
│         │                              └──────┬───────┘    │
│         │                                     │            │
│         ▼                                     ▼            │
│  ┌──────────────────────────────────────────────────┐     │
│  │         Human Review Agent (Optional)            │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Result Output     │
└─────────────────────┘
```

### Review & Decision Layer

The system includes a review layer that categorizes invoices into operational queues:

- **Auto-Approved Queue**  
  Invoices with high-confidence matches and no material discrepancies.

- **Human Review Queue**  
  Invoices with critical discrepancies, missing PO references, or low confidence scores.

Invoices routed to human review are accompanied by:
- Original PDF preview
- Full agent reasoning trace
- AI-generated explanation summarizing the escalation rationale

### Agent Responsibilities

#### 1. Document Intelligence Agent
Extracts and structures invoice data from PDFs:
- Performs OCR on scanned and digital documents
- Leverages LLM for intelligent data extraction
- Produces structured JSON output with confidence scores

#### 2. Matching Agent
Identifies corresponding purchase orders:
- Direct PO number matching when available
- Fuzzy item-based matching for missing PO numbers
- Confidence scoring for match quality assessment

#### 3. Discrepancy Detection Agent
Validates invoice accuracy against PO data:
- Line-item price comparison
- Quantity verification
- Item presence validation
- Supports configurable tolerance thresholds

#### 4. Resolution Recommendation Agent
Applies business rules for decision making:
- Confidence-weighted risk assessment
- Multi-factor decision criteria
- Escalation path determination

#### 5. Human Review Agent
Provides human-in-the-loop oversight:
- Reviews high-risk escalations
- Overrides automated decisions when appropriate
- Generates actionable feedback for process improvement

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestration | LangGraph | Agent coordination and workflow management |
| LLM Inference | Groq API | Fast, cost-effective language model processing |
| OCR Engine | Tesseract | Text extraction from scanned documents |
| PDF Processing | pdf2image, Poppler | PDF rendering and image conversion |
| Fuzzy Matching | RapidFuzz | Approximate string matching for reconciliation |
| Frontend | Streamlit | Interactive user interface |
| Runtime | Python 3.10+ | Core application runtime |

## Installation

### Prerequisites

Ensure the following system dependencies are installed:

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Download and install [Poppler for Windows](https://blog.alivate.com.au/poppler-windows/)

### Python Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd invoice_project

# Install required packages
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Command Line Interface

Process all invoices in the `invoices/` directory:

```bash
python main.py
```

Output JSON files will be saved to the `outputs/` directory.

### Streamlit Web Interface

Launch the interactive UI:

```bash
streamlit run app.py
```

**Workflow:**
1. Launch the Streamlit application
2. Upload one or more invoice PDF files
3. The system processes invoices through the multi-agent pipeline
4. Observe real-time agent reasoning streamed step-by-step
5. Review results in two operational tabs:
   - **Auto Approved**: Clean invoices ready for payment
   - **Needs Human Review**: Risky or uncertain invoices
6. For human review cases:
   - View original PDF inline
   - Inspect agent reasoning and detected issues
   - Read an LLM-generated explanation summarizing the escalation rationale

## Project Structure

```
invoice_project/
│
├── agents/                      # Agent implementation modules
│   ├── document_agent.py        # OCR and data extraction
│   ├── matching_agent.py        # PO matching logic
│   ├── discrepancy_agent.py     # Discrepancy detection
│   ├── resolution_agent.py      # Decision recommendation
│   └── human_review_agent.py    # Human-in-the-loop reviewer
│
├── invoices/                    # Sample invoice PDFs
├── outputs/                     # Processing results (JSON)
│
├── app.py                       # Streamlit web interface
├── graph.py                     # LangGraph orchestration
├── llm.py                       # LLM wrapper and utilities
├── ocr_utils.py                 # OCR processing functions
├── main.py                      # CLI entry point
├── purchase_orders.json         # PO database (sample data)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Test Coverage

The system has been validated against diverse invoice scenarios:

| Test Case | Description | Expected Outcome | Status |
|-----------|-------------|------------------|--------|
| Clean Invoice | Standard format, perfect match | AUTO_APPROVE | ✅ Pass |
| Scanned Document | Low-quality scan, rotated image | AUTO_APPROVE | ✅ Pass |
| Alternate Format | Non-standard template layout | AUTO_APPROVE | ✅ Pass |
| Price Discrepancy | Material unit price mismatch | ESCALATE_TO_HUMAN | ✅ Pass |
| Missing PO Reference | No PO number provided | ESCALATE_TO_HUMAN | ✅ Pass |
| Quantity Mismatch | Incorrect quantities ordered | REQUEST_CLARIFICATION | ✅ Pass |

### Reasoning Transparency & Explainability

Every agent contributes real-time reasoning to a shared execution state.  
These reasoning steps are streamed live to the UI and displayed as a chat-style activity feed, enabling:

- Clear visibility into agent handoffs
- Step-by-step decision justification
- Debugging and audit readiness

For invoices escalated to human review, an additional LLM-generated explanation provides a concise, business-friendly summary of why manual intervention is required.

## Limitations & Future Enhancements

### Current Limitations

- **OCR Accuracy**: Performance degrades with poor scan quality or complex layouts
- **LLM Extraction**: Occasional structured output failures require fallback logic
- **Matching Heuristics**: Rule-based approach may miss nuanced relationships
- **Synchronous Processing**: Single-threaded execution limits throughput

### Production Roadmap

**Near-term Enhancements:**
- Integrate layout-aware OCR (Azure Form Recognizer, Google Document AI)
- Implement embedding-based semantic matching for improved accuracy
- Add asynchronous processing with job queues (Celery, Redis)
- Deploy comprehensive monitoring and alerting infrastructure

**Long-term Vision:**
- Machine learning model training from human feedback loop
- Multi-modal document understanding (tables, charts, signatures)
- Real-time drift detection and model retraining
- Integration with enterprise ERP systems (SAP, Oracle, NetSuite)

## Contributing

Contributions are welcome! 
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Author**: Aditya Suyal
**Purpose**: Agent Development Internship Technical Assessment  
**Contact**: https://www.linkedin.com/in/aditya-suyal/

---



## Screenshots
![Screenshot 4](Photos/Screenshot%202026-01-29%20at%209.21.43%E2%80%AFPM.png)
![Screenshot 5](Photos/Screenshot%202026-01-29%20at%209.21.52%E2%80%AFPM.png)
![Screenshot 6](Photos/Screenshot%202026-01-29%20at%209.22.13%E2%80%AFPM.png)
