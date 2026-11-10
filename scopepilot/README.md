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

## ScopePilot V3: location follow-up and verified estimating handoff

- A customer stating **“The house is in Woodland Hills”** now receives a follow-up for the **full street address**, rather than being asked for an unspecified location or ZIP code.
- If only a ZIP code is supplied, the assistant still asks for a street address. A full street address suppresses the generic location question. Location recognition is intentionally heuristic; it is not geocoding or address verification.
- The approved export matches BuildEstimate's **POST /api/estimate** JSON request schema. Importing JSON through BuildEstimate's web interface is **not** available yet; test the exported request through the API.
- No pricing is invented by ScopePilot; BuildEstimate performs the costing using its separate catalog.

### Example integration verification

After downloading `buildestimate-input.json`, use a terminal to call the live BuildEstimate API:

```bash
curl -X POST https://buildestimate-82xs.onrender.com/api/estimate -H "Content-Type: application/json" --data-binary @buildestimate-input.json
```

The response should include `items` and `totals.estimated_price`. The hosted free instance may take a little time to wake up. Only use demo values for portfolio evaluation.

## Browser handoff to BuildEstimate (integration update)

After reviewing the proposed scope, select the approved work items, check the approval box, and click **Send to BuildEstimate**. ScopePilot validates the approved payload through `POST /api/handoff` and opens BuildEstimate with only the selected item codes, quantities, project name, and default costing assumptions. BuildEstimate validates and imports the fields, then calculates the estimate using its own price catalog. You can also export the JSON without opening a new tab.

**Deployment dependency:** This feature requires the accompanying BuildEstimate `web/index.html` update. Until it is deployed, the button will open the older demo with its default values. The URL fragment is browser-side transfer data and is removed from the BuildEstimate address bar on page load; no customer notes or follow-up questions are included in the transfer. Avoid personal data in project names. Never treat the imported scope as an approved customer quote; unanswered questions and sample pricing still require review.
