# Job Agent — Frontend Dashboard

A static HTML + React dashboard for tracking job applications. No build step, no npm — just open `index.html` in a browser with the FastAPI backend running.

## Setup

**1. Install backend dependencies** (if not done):
```bash
pip install -r requirements.txt
pip install uvicorn
```

**2. Start the API server:**
```bash
uvicorn job_agent.api:app --reload
```
The API will be available at `http://localhost:8000`.

**3. Open the dashboard:**

Open `frontend/index.html` directly in your browser, or serve it with any static file server:
```bash
# Option A — Python (simplest)
cd frontend
python -m http.server 3000
# Then open http://localhost:3000

# Option B — Just open the file
open frontend/index.html   # macOS
start frontend/index.html  # Windows
```

> **Note:** Opening directly as a `file://` URL works fine since all API calls go to `localhost:8000` and CORS is enabled on the backend.

## Files

| File | Description |
|------|-------------|
| `index.html` | Main app — React dashboard (Babel, no build step) |
| `colors_and_type.css` | Design system tokens: colors, type, spacing, motion |
| `kit.css` | Component styles: sidebar, cards, table, modal, etc. |

## API endpoints used

| Method | Endpoint | Usage |
|--------|----------|-------|
| `GET` | `/applications` | Load all applications |
| `GET` | `/stats` | Dashboard stats + pipeline counts |
| `PATCH` | `/applications/{id}/status` | Update application status |
| `POST` | `/applications` | Add a manual application |

## Changing the API URL

Edit the `API_BASE` constant at the top of `index.html`:
```js
const API_BASE = "http://localhost:8000";
```

## Pages

- **Dashboard** — Stats grid, pipeline bar, recent applications
- **Applications** — Searchable/filterable table with inline status updates, add modal
- **Application detail** — Click any row to see folder path, score reason, docs list
- **Run agent** — CLI reference card (agent runs in terminal, not browser)
- **Daily digest** — CLI reference card for `python -m job_agent.digest`
- **Settings** — API connection info, tone selector reference
