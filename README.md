---
title: AI Translation Quality Pipeline
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "5.38.2"
python_version: "3.11"
app_file: app.py
pinned: false
hardware: cpu
---

# AI-Assisted Translation & Quality Scoring Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Anthropic Claude API](https://img.shields.io/badge/Anthropic-Claude%20API-orange.svg)](https://docs.anthropic.com/)
[![Gradio UI](https://img.shields.io/badge/UI-Gradio-red.svg)](https://gradio.app/)
[![Deployment Target](https://img.shields.io/badge/Hugging%20Face-Spaces-yellow.svg)](https://huggingface.co/spaces)

An enterprise-grade AI software localization and quality evaluation application. This project demonstrates how Large Language Models (LLMs) perform context-aware software internationalization (i18n) and objective translation quality auditing.

> *Note: This project was originally developed as part of an AI Engineer technical assessment.*

---

## 📌 Project Overview

Software localization requires more than literal dictionary translations. English software UI strings frequently contain polysemous single words—such as **"Open"**, **"Post"**, or **"Due"**—whose correct translation changes dramatically depending on user context and developer intent.

This project solves software localization challenges through two independent, production-grade pipelines:

1. **Context-Aware Software Localization**: Translates ambiguous English UI strings into Spanish by analyzing string key hierarchy and developer comments alongside the source text.
2. **Translation Quality Scoring Audit**: Evaluates candidate translations using an explainable, 100-point scoring rubric, producing itemized issue reports, severity ratings, and suggested corrections.
3. **Interactive Reviewer Interface**: Features a clean Gradio dashboard allowing engineering teams to run pipelines independently or end-to-end, with exportable CSV and JSON reports.

---

## 🚀 Live Demo

**Hugging Face Spaces**:  
*(Add deployed URL after deployment)*

---

## 🛠️ Tech Stack

- **LLM Engine**: Anthropic Claude API (`claude-sonnet-4-6`)
- **User Interface**: Gradio 4+
- **Core Runtime**: Python 3.11+
- **Data Validation & Schemas**: Pydantic v2
- **Data Manipulation & Formatting**: Pandas
- **Environment Management**: python-dotenv

---

## 🏗️ Architecture Diagram

```
                 ┌──────────────────────────────────────┐
                 │         Gradio User Interface        │
                 │     (app.py - Default Theme)         │
                 └──────────────────┬───────────────────┘
                                    │
               ┌────────────────────┴───────────────────┐
               ▼                                        ▼
     ┌───────────────────┐                    ┌───────────────────┐
     │   translator.py   │                    │     scorer.py     │
     │ (Translation)     │                    │ (Quality Audit)   │
     └─────────┬─────────┘                    └─────────┬─────────┘
               │                                        │
               └────────────────────┬───────────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │    claude_client.py   │
                        │(Anthropic API Client) │
                        └───────────┬───────────┘
                                    ▼
                        ┌───────────────────────┐
                        │ Anthropic Claude API  │
                        │  (claude-sonnet-4-6)  │
                        └───────────────────────┘
```

---

## 📂 Repository Structure

```
ai-translation-quality-pipeline/
├── app.py              # Gradio web application & orchestration layer
├── claude_client.py    # Dedicated Anthropic Claude API client (retries, timeouts, JSON parsing)
├── translator.py       # Context-aware translation service
├── scorer.py           # 100-point rubric quality scoring service & metrics aggregator
├── prompts.py          # Structured system & user prompts for translation and evaluation
├── schemas.py          # Strict Pydantic models for data validation
├── sample_data.py      # Benchmark datasets (10 translation inputs & 8 evaluation candidates)
├── config.py           # Configuration management (.env & environment resolution)
├── logger.py           # Standardized application logging
├── utils.py            # DataFrame conversion & CSV/JSON export handlers
├── requirements.txt    # Pinned dependency manifest
├── README.md           # Documentation & architectural blueprint
└── .env.example        # Environment configuration template
```

---

## 🎯 Design Decisions

- **Why Gradio**: Enables rapid, Python-native UI deployment perfectly tailored for Hugging Face Spaces without complex web framework overhead.
- **Why Pydantic**: Guarantees strict runtime data validation, strong typing, and schema contracts for all LLM JSON payloads.
- **Why a Dedicated Claude Client**: Decouples API connectivity, retries, rate-limit backoff, and raw JSON parsing from business services (`translator.py` / `scorer.py`), upholding SOLID principles.
- **Why Deterministic Temperature (0.0)**: Eliminates creative variance and hallucinations, ensuring reproducible localization choices and consistent 100-point rubric audits.
- **Why Retry Logic**: Automatically recovers from transient network timeouts and API rate limits via exponential backoff without user-facing crashes.
- **Why Business Logic is Separated from UI**: Keeps `app.py` strictly focused on UI orchestration, making core services independently testable and maintainable.

---

## 💡 Context-Aware Translation Strategy & Polysemy Analysis

### How Claude Translates UI Strings
Every localization request provides Claude with three contextual signals:
1. **UI Key Syntax** (e.g., `ticket.button.open` vs `settings.hours.status_label_open`)
2. **Developer Commentary** (e.g., *"Button an agent clicks to open a closed support ticket back up"*)
3. **English Source Text** (e.g., *"Open"*)

Claude combines these signals to infer whether a string represents an action verb, a status adjective, or a specific domain concept before selecting the correct Spanish term.

### Polysemy Benchmark Comparison

| English Word | UI Key Syntax | Developer Context | Naive Translation | Context-Aware Translation | Context Reasoning |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Open** | `ticket.button.open` | Agent clicks to open closed support ticket | *Abierto* (Adjective) | **Reabrir** | Reopening action verb for support ticket workflow |
| **Open** | `settings.hours.status_label_open` | Support desk is open for business | *Abrir* (Verb) | **Abierto** | State/Adjective indicating operational status |
| **Post** | `feed.button.post` | Publish new post to internal feed | *Correo* (Mail) | **Publicar** | Social/Feed publishing action verb |
| **Post** | `mail.label.post` | Physical mail correspondence field | *Publicar* (Social) | **Dirección Postal** | Postal mailing address context |
| **Due** | `ticket.field.due` | Field showing ticket due date | *Vencido* (Expired) | **Fecha de vencimiento** | Resolution deadline context |
| **Due** | `invoice.field.amount_due` | Field showing amount of money owed | *Vencimiento* (Date) | **Importe pendiente** | Financial balance owed context |

---

## 📊 Quality Scoring Rubric Framework (100 Points)

Candidate translations are evaluated against an explainable 100-point rubric:

- **Contextual Accuracy (0–40 Points)**: Correct semantic interpretation of key hierarchy and developer intent.
- **Linguistic Quality (0–30 Points)**: Spanish grammar, spelling, natural phrasing, and fluency.
- **UI Appropriateness (0–20 Points)**: Character length conciseness suitable for UI components.
- **Consistency (0–10 Points)**: Alignment with standard software terminology conventions.

### Approval Threshold
- **Score ≥ 70.0** ➔ Status: **`Passed`**
- **Score < 70.0** ➔ Status: **`Needs Review`**

---

## 🔍 Notable Quality Scoring Findings

During benchmark evaluation of candidate translation pairs, the quality scoring engine correctly identifies semantic errors that naive translators miss:

1. **`ticket.button.open` (Candidate: *Abierto*)**
   - **Score**: ~42/100 | **Status**: `Needs Review` | **Severity**: `Critical`
   - **Audit Issue**: *Abierto* is an adjective. A ticket reopen button requires an action verb (*Reabrir*).
2. **`feed.button.post` (Candidate: *Correo*)**
   - **Score**: ~35/100 | **Status**: `Needs Review` | **Severity**: `Critical`
   - **Audit Issue**: *Correo* refers to postal mail. Publishing to an internal team feed requires *Publicar*.
3. **`invoice.field.amount_due` (Candidate: *Vencido*)**
   - **Score**: ~48/100 | **Status**: `Needs Review` | **Severity**: `Critical`
   - **Audit Issue**: *Vencido* means expired/past due. The amount owed on an invoice requires *Importe pendiente* or *Monto a pagar*.
4. **Passing Benchmarks**:
   - Accurate candidates (*Cerrar*, *Asignar*, *Compartir*, *Exportar*) consistently score **85–100** points with status **`Passed`**.

---

## 📝 Key Assumptions

- **Target Locale**: Standard Spanish (Castilian/International software Spanish).
- **UI Component Type**: Compact software UI components (buttons, labels, input headers).
- **Passing Threshold**: 70 out of 100 total rubric points required for automatic approval.
- **Contextual Priority**: Key names and developer notes take precedence over literal dictionary lookup.

---

## 🖼️ Screenshots

### Translation Pipeline
*(Insert screenshot after deployment)*

### Quality Scoring
*(Insert screenshot after deployment)*

---

## ⚙️ Local Installation & Setup

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/ai-translation-quality-pipeline.git
cd ai-translation-quality-pipeline

# Create virtual environment (Python 3.11+)
python -m venv venv

# Activate environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate environment (Linux/macOS)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```
Edit `.env` and set your API key:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key
MODEL_NAME=claude-sonnet-4-6
REQUEST_TIMEOUT=30.0
MAX_RETRIES=3
LOG_LEVEL=INFO
```

### 4. Launch Application
```bash
python app.py
```
Open your browser at `http://127.0.0.1:7860`.

---

## 🚀 Hugging Face Spaces Deployment Guide

1. Log into [Hugging Face](https://huggingface.co/) and create a **New Space**.
2. Select **Gradio** as the SDK and Python **3.11**.
3. Upload all repository files (`app.py`, `claude_client.py`, `translator.py`, `scorer.py`, `prompts.py`, `schemas.py`, `sample_data.py`, `config.py`, `logger.py`, `utils.py`, `requirements.txt`, `README.md`, `.gitignore`).
4. **Configure Space Secret**:
   - Navigate to **Space Settings ➔ Variables and secrets ➔ New secret**
   - Key: `ANTHROPIC_API_KEY`
   - Value: `your_anthropic_api_key`
5. Save secret and deploy. Hugging Face Spaces will automatically build and launch `app.py`.

---

## ⚠️ Known Limitations

- **API Key Requirement**: Requires a valid Anthropic API key (`claude-sonnet-4-6`).
- **Sequential Processing**: Processes batch items sequentially to respect default rate limits.
- **Language Scope**: Target locale is currently optimized for English-to-Spanish UI localization.
