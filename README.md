# ScopePilot — Construction Scope Review Assistant

**[Try the live application](https://scopepilot-etgt.onrender.com)** · **[BuildEstimate live demo](https://buildestimate-82xs.onrender.com)** · [Automated tests](https://github.com/sachintechpro/scopepilot/actions)

ScopePilot turns a contractor's free-form customer inquiry into a **reviewable work scope**. It suggests work items and quantities, flags missing information, and requires a contractor to approve the selected scope before transferring it to BuildEstimate.

> **Portfolio prototype, not a production estimating or AI system.** The default **Rules Demo** uses pattern matching, **not a language model**. Optional AI-assisted extraction is available only when an API key is configured; its accuracy and production suitability have not been independently validated. Do not enter confidential customer information in this public demo.

## Live walkthrough

1. Open **[ScopePilot](https://scopepilot-etgt.onrender.com)** and click **Review scope**.
2. Check the proposed catalog items, quantities, and missing-information questions. Try changing quantities or removing a unit to see how the review responds.
3. Edit, exclude, or add supported items; enter a project name.
4. Select the contractor approval checkbox and click **Send to BuildEstimate**.
5. **[BuildEstimate](https://buildestimate-82xs.onrender.com)** opens with approved quantities populated and calculates using its own illustrative price catalog. Verify the pricing assumptions before printing or exporting.

Free hosting may take time to wake up after inactivity.

## Technical design

```text
Customer notes (browser)
  → Python API POST /api/review
  → deterministic extraction (app/core.py), optional AI (app/ai.py)
  → missing-information prompts + human review
  → POST /api/handoff (app/handoff.py): catalog/quantity/approval validation
  → browser URL-fragment transfer (approved estimate inputs only)
  → BuildEstimate frontend import → its /api/estimate calculation endpoint
```

- **Python:** zero-dependency HTTP server, explicit validation, catalog matching, handoff endpoint
- **JavaScript:** editable scope review, approval control, structured JSON export, browser-to-browser handoff
- **CSV:** shared demonstration item codes and units, not real supplier costs
- **Testing:** unit tests for parsing, missing information, invalid quantities, approvals, and schema compatibility; CI runs on pushes and pull requests

### Data transfer and limitations

The browser transfer includes only selected item codes, quantities, project name, and default costing assumptions. It does **not** transfer the customer notes or missing-information questions. The payload briefly appears in the destination URL fragment; avoid identifying details in project names. Because this is browser-mediated, it is **not** a secured server-to-server integration. Approving a scope for estimating does not mean unresolved questions are answered or that a quote has been authorized.

Location recognition is heuristic: "The house is in Woodland Hills" should prompt for the full street address, whereas an explicit street address should not generate the same location question. There is no geocoding or address verification.

## Run locally

Requires Python 3.10+. From the **scopepilot** application directory:

```bash
python -m app.server
```

Visit http://127.0.0.1:8000. To run tests:

```bash
python -m unittest discover -s tests -v
```

## Render deployment

Create a Python Web Service with repository root directory **scopepilot**, build command `python -m unittest discover -s tests -v`, and start command `python -m app.server`. The server uses Render's `PORT` environment variable.

## APIs

- `GET /api/health` — service health
- `GET /api/catalog` — supported item codes and units
- `GET /api/modes` — supported extraction modes
- `POST /api/review` — `{ "request": "Replace 12 linear ft of base cabinets", "mode": "rules" }`
- `POST /api/handoff` — `{ "approved": true, "project_name": "Demo", "items": [{"code":"CABINET", "quantity":12}] }`

### Optional real AI

Set `OPENAI_API_KEY` as a server-side secret (never in GitHub), and optionally `OPENAI_MODEL` to a supported model. AI mode sends entered notes to an external provider and may incur charges. AI suggestions still require human verification and are validated against the item catalog.

**Portfolio focus:** API design, deterministic baselines, human-in-the-loop workflows, defensive validation, tests, and integration between separately deployed applications.
