# Project Context — AI Document Formatting Agent (Undergraduate Thesis / Tugas Akhir)

## Overview
This is an undergraduate thesis project (S1/D3 Manajemen Informatika, semester 7).

**Thesis title:** "Hybrid Rule-Based dan IndoBERT untuk Klasifikasi Struktur dan Penerapan Aturan Format Dokumen Karya Ilmiah Berbasis Data Template Adaptif"

**Goal:** Build a web application that automatically tidies/formats Indonesian academic documents (Microsoft Word .docx) — internship proposals, final reports (laporan akhir), theses (skripsi) — to match institutional formatting standards: heading style, font, font size, line spacing, margins, and numbering.

## Core Concept — Two Processing Modes
1. **Standard Template Mode** — Pre-configured formatting rules (built from official university writing guidelines) that the user selects and applies directly, no training needed.
2. **Adaptive Learning Mode** — The user uploads a correctly-formatted example document plus a target document to reformat. The system extracts the formatting rules from the example, stores them as a reusable config (JSON), and applies them to the target document — and to future documents from the same user without re-uploading the example.

## Two-Layer Processing Pipeline (IMPORTANT — keep these separated)
1. **Rule-based layer (deterministic, no AI)** — Parses the .docx OOXML/XML directly via `python-docx` to extract measurable style properties: font family, font size, line spacing, margins, paragraph alignment, numbering format. Lives in something like `services/rule_based_extractor.py`.
2. **AI layer (IndoBERT — classification, NOT generative)** — A fine-tuned IndoBERT model (encoder-only) classifies each text segment/paragraph into a structural role label, e.g. `judul_bab`, `sub_bab`, `isi`, `caption_tabel`, `caption_gambar`, `daftar_poin`. This solves the semantic problem plain rule-based parsing cannot: knowing *which* text is a heading vs. body content. Lives in something like `services/structure_classifier.py`.

**Do not suggest merging these two layers or replacing IndoBERT with a generative LLM (GPT/Llama/Qwen/etc.).** The thesis advisor explicitly required a specific, named model architecture (not a generic "LLM" wrapper), and IndoBERT was chosen and justified for this reason. Keep the classification framing (labels a fixed set of categories) rather than an extraction/generation framing.

## Tech Stack (defaults — update this section once finalized)
- **Backend:** Python 3.10+, FastAPI
- **Document processing:** `python-docx`, direct OOXML parsing where python-docx is insufficient
- **AI model:** `indobenchmark/indobert-base-p1` (or p2), fine-tuned via Hugging Face `transformers` + PyTorch
- **Config storage:** SQLite via SQLAlchemy — stores extracted template configs as JSON, keyed per user/task
- **Frontend:** React (Vite) — document upload/download, template selection, adaptive-mode example upload flow
- **Deployment:** Fully local/offline inference — no calls to external cloud AI APIs (OpenAI, Anthropic, Google, etc.). This is a stated privacy justification in the thesis and must not be violated by suggested code.

## Coding Conventions
- Python: follow PEP8, use type hints, prefer explicit and well-commented code over clever one-liners (the code must be explainable during the thesis defense / sidang)
- Keep rule-based and AI-classification logic in clearly separate modules — they are evaluated as separate components in the thesis (rule-based accuracy vs. classifier accuracy/F1)
- Template configs: structured JSON with a documented schema (e.g. `schemas/template_config_schema.json`)
- When writing document-parsing code, use python-docx's proper API (`paragraph.style`, `run.font`, `paragraph_format`) instead of regex/text-pattern guessing
- Write labeled training data for IndoBERT fine-tuning in a simple, consistent format (e.g. CSV/JSONL with `text` and `label` columns) so it's easy to expand the dataset later

## What NOT to Suggest
- No cloud LLM API calls (OpenAI, Anthropic, Google Gemini, etc.) — violates the local/privacy-preserving requirement
- No fine-tuning framing described as "training a generative LLM" — IndoBERT here is a classifier, not a text generator
- No insecure storage of uploaded documents — treat them as potentially containing personal/institutional data
- Don't default to English-only NLP models/tokenizers — this project is Bahasa Indonesia specific

## Current Stage
<!-- Update this line as the project progresses, e.g.: -->
<!-- "Currently building the rule-based extraction module (services/rule_based_extractor.py)" -->
<!-- "Currently preparing the labeled dataset for IndoBERT fine-tuning" -->
Just starting — environment setup and dataset collection phase.
