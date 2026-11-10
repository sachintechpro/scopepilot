# ScopePilot — Construction Operations Assistant

A portfolio demonstration for converting contractor/customer requests into **reviewable work items** and **follow-up questions**. Built using Python, browser JavaScript, JSON APIs, and automated tests.

> **This is a demo, not an autonomous estimator.** The default Rules Demo uses deterministic pattern matching and **does not use AI**. Optional AI-assisted extraction requires a server-side API key. All extracted scope and quantities require human confirmation.

## Features

- Paste customer inquiry or job notes and identify recognizable construction work items
- Associate explicit quantities with the appropriate price-catalog unit when reasonably clear
- Surface missing dimensions, location, and scheduling information
- Edit quantities, deselect suggested items, or manually add other known catalog items
- Require explicit contractor approval before export, with backend validation of all item codes and quantities
- Download approved JSON compatible with the **BuildEstimate** `/api/estimate` request schema
- Configure **optional** language-model-assisted extraction using an API key, with catalog allowlisting and evidence requirements
- Automated unit tests and GitHub Actions CI

## Run locally

Python 3.10+ required. No external Python packages:

```bash
python -m app.server
```

Open http://127.0.0.1:8000

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Deploy on Render

- New **Web Service** from this repository
- Language: **Python 3**
- Build command: `python -m unittest discover -s tests -v`
- Start command: `python -m app.server`
- Instance: Free is adequate for demo use

The server uses Render's `PORT` environment variable and binds to `0.0.0.0`. The free instance may spin down when idle.

## Optional real AI integration

On Render, set `OPENAI_API_KEY` as a **secret environment variable**, not in GitHub, and optionally set `OPENAI_MODEL` to a compatible chat-completions JSON-mode model. The AI mode sends the customer's text to an external model provider. This incurs provider charges and should not be used with sensitive personal/customer data without appropriate consent and safeguards. The default demo remains free of API costs.

The AI backend suggests known catalog item codes, provides source-text evidence, and generates clarification questions. A secondary validator rejects unsupported catalog codes and ungrounded evidence. **Evidence matching does not establish that an AI-proposed quantity is correct**; all proposals remain subject to human review.

## Architecture

```
Browser UI (web/index.html)
    | POST /api/review, POST /api/handoff
Python API (app/server.py)
    |-- rules mode: app/core.py
    |-- optional AI mode: app/ai.py -> model provider
    |-- known catalog: data/catalog.csv
    |-- validate review result / export for BuildEstimate
```

### APIs

- `GET /api/health` — service health
- `GET /api/catalog` — available work-item catalog (no costs)
- `GET /api/modes` — available extraction modes
- `POST /api/review` — JSON `{ "request": "...", "mode": "rules" }`
- `POST /api/handoff` — validate `{ "approved": true, "project_name": "...", "items": [{"code": "FLOOR", "quantity": 250}] }` and return a BuildEstimate-compatible request

## End-to-end demo walkthrough

1. Paste a customer request and click **Review scope**.
2. Inspect suggested work items and follow-up questions.
3. Correct quantity fields, deselect unwanted items, and add a missing catalog item if needed.
4. Check the explicit approval checkbox and export `buildestimate-input.json`.
5. Open [BuildEstimate](https://buildestimate-82xs.onrender.com) and enter the reviewed item codes and quantities in its form. Its API also accepts the exported JSON as the body for `POST /api/estimate`. **The BuildEstimate browser UI does not currently import JSON**, so the handoff is a validated API payload, not a one-click automatic transfer.
6. Recheck prices, assumptions, missing scope questions, and job-site conditions before preparing an actual bid.


## Showcase narrative

**Business problem:** Contractors often receive unstructured project notes with incomplete quantities, mismatched units, and missing logistics. Estimating on insufficient information can lead to rework or inaccurate quotes.

**Solution:** ScopePilot converts a request into a draft scope and a checklist of questions, while keeping pricing and final approvals separate. It provides a validated JSON API handoff to [BuildEstimate](https://github.com/sachintechpro/construction-estimator) by exporting compatible request JSON.

**Engineering choices:** A deterministic rules-mode baseline, restricted catalog mappings, evidence capture, explicit missing quantities, no database persistence, and unit tests.

## Limitations

The rules parser is deliberately narrow and can fail on complex phrasing or wrongly associate nearby measurements. It recognizes only seven demo catalog items. It does not understand images, specifications, floorplans, permits, contracts, local pricing, or detailed estimating. The optional AI integration is not a substitute for a professional's measurements or approvals. The sample catalog has illustrative values only.
