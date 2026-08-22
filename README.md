# StreamOperiq

StreamOperiq is a multi-platform operations and performance intelligence platform
for creator agencies and live-streaming networks. One deployment can host several
completely separate businesses (ABC, DEF, ...), each with its own
broadcasters, sub-agencies, and logins — fully walled off from every other
business on the same platform.

- **Platform admin** (you, or whoever runs the platform) creates businesses
  and their first owner login. Nothing else — no broadcaster data.
- **Business owner** (e.g. ABC) sees everything inside their own business:
  upload the monthly/daily `referral_statistics` CSV, see the full
  broadcaster list, assign any broadcaster to any sub-agency directly from
  that list, manage sub-agencies, users, and data — all scoped only to ABC.
  Additional uploads add new profiles and update matching profiles without
  deleting other broadcasters already stored for that period.
- **Sub-agency login** (e.g. Partner X under ABC) sees only their own
  assigned broadcasters — dashboard, list, and upload are all automatically
  locked to them, no separate screen or filter needed.
- Every broadcaster is matched by their permanent Tango profile URL, so an
  assignment made once is remembered forever, no matter how many future
  files come in.
- Insights built in: retention rate, an at-risk list, diamonds-per-day,
  attribution completeness, and a top-5 leaderboard, automatically on every
  business's dashboard.

Everything below is free — no credit card required anywhere, and no
external services beyond a free Postgres database, GitHub, and Streamlit
Cloud. The only ever-optional paid step is a custom domain later, which the
app doesn't need to function.

---

## One-time setup (~10 minutes)

### Step 1 — Create a free Postgres database (Supabase)
1. Go to supabase.com → sign up (free, no credit card) → **New project**.
2. Pick any name and a database password (write the password down).
3. Once the project's ready, go to **Project Settings → Database →
   Connection string** → copy the URI (it looks like
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`).
   Paste in the password you chose in step 2 where it says `[YOUR-PASSWORD]`.
4. That's it — no tables to create by hand. The app creates every table it
   needs automatically the first time it connects.

### Step 2 — Put this code on GitHub (free)
1. Create a free account at github.com if you don't have one.
2. Create a new repository (public or private, either works).
3. Upload all the files from this project into it (`app.py`, `utils.py`,
   `store.py`, `requirements.txt`, the `.streamlit` folder).
   Do **not** upload a filled-in secrets file — secrets go into Streamlit
   Cloud directly (next step), never into GitHub.

### Step 3 — Deploy on Streamlit Community Cloud (free)
1. Go to share.streamlit.io → sign in with your GitHub account.
2. **New app** → pick the repository from Step 2 → main file: `app.py` → Deploy.
3. Once it's building, go to **Settings → Secrets** and paste in the
   contents of `secrets_example.toml`, filled in with:
   - `[postgres] connection_string` = the URI from Step 1
   - `[cookie]` = leave as is, or change the random string
   - `[bootstrap_admin]` = your own platform-admin login — pick any email,
     name, and password. This is the only account that lives in secrets.
4. Save. The app restarts and you'll have a permanent link like
   `https://your-app-name.streamlit.app`.

### Step 4 — First run
1. Open your link, log in with the platform-admin credentials from Step 3.
2. You land on **Businesses**. Create your first one — e.g. "ABC Agency" —
   and set its owner's email and password in the same step (or click
   **Generate password**).
3. Sign out, sign back in as that owner. You're now inside ABC's own
   dashboard, completely separate from any other business you create later.
4. Go to **Create sub-agency** → add Partner X, Y, Z, ticking "also create a
   login" for each (or generate a password) — this solves the attribution
   problem: any broadcaster tagged to a sub-agency stays tagged to them
   forever, by their permanent Tango profile URL.
5. Go to **Monthly report** (Upload Reports) → type the period (e.g.
   `2026-08`) → upload the CSV → review the summary → Confirm upload.
6. Go to **Assign broadcasters** → tick the ones brought in by Partner X →
   pick "Partner X" → Assign selected. Anyone left unticked stays
   "Unassigned" — i.e. direct to you. The banner on the dashboard tells you
   how many are still unassigned at a glance.
7. Go to **Admin** — the dashboard is live, with insights and a leaderboard
   underneath the KPI cards, and a "Sub-agency" dropdown to switch between
   "All" and any individual partner's numbers.

---

## Onboarding a second, completely separate business
Sign in as the platform admin → **Businesses** → create the new business
(e.g. "DEF Agency") with its own owner login. From that moment on, DEF's
broadcasters, sub-agencies, uploads, and users are entirely invisible to
ABC, and vice versa — they share the one deployed link, nothing else.
Logins are unique across the whole platform (based on email), so the same
email can't be reused for two different businesses.

## Giving someone else access within a business
Business owners create their own sub-agency and owner-level logins from
**User access** or **Create sub-agency** — no redeploying, no editing files.
The same page can disable a login or reset its password at any time. A
sub-agency login only ever sees its own broadcasters.

## Every month going forward
Repeat Step 4.5 — upload the new file, tag it with the right period. Additional
files for the same period add new profiles and update matching profiles,
which is what lets the dashboard show active/inactive trends and the
insights (retention, at-risk, growth) across months. If a sub-agency user
does their own upload, any of their previously-unassigned broadcasters in
that file get attributed to their agency automatically.

### Agency direct hires
Upload the CSV normally. A broadcaster assigned to a Sub-Agency is classified
as a Sub-Agency hire; a broadcaster without a Sub-Agency assignment is classified
as **Agency Direct**. No special upload mode is required. The Agency overview
compares direct hires with Sub-Agency hires and shows the commission-adjusted
earnings mix.

## AI Poster Studio
An Owner/Agency Manager–only page (sidebar → **Creative → AI Poster Studio**)
that turns participant photo(s) plus event details into a premium,
high-resolution promotional poster: birthday, official battle, finals,
winner/achievement, live event, and more. AI generates the artwork; exact
title/name/date/time text is composited afterward with Pillow, so it can
never contain an AI spelling error.

**Setup:** add to Streamlit Cloud secrets (or local `.streamlit/secrets.toml`):
```toml
[openai]
api_key = "sk-..."
# model = "gpt-image-1"   # optional
```
Without an `[openai]` section, the page shows a friendly "not configured"
message — nothing else in the dashboard is affected. To turn the whole
feature off without a deploy, add `[features] ai_poster_studio = false`.

**Supported poster categories:** Birthday Celebration, Premium/Glam
Birthday, Official Battle, Battle Promotion, Finals/Competition, Special
Celebration, Special Live Event, Winner/Achievement, Custom — defined in
`poster/categories.py`; add a new one there, nothing else needs an
if/elif.

**Supported photo formats:** JPG, JPEG, PNG, WEBP, up to 8 MB each.

**Demo Mode — try the full UI for free, no OpenAI key or cost required:**
tick "Preview UI with placeholder art" (auto-checked when no `[openai]`
key is configured) before clicking Generate. It skips the paid AI call
entirely and runs a Pillow-generated gradient background through the same
real crop/typography/logo pipeline, clearly watermarked "DEMO PREVIEW" so
it's never mistaken for real output. Every step of the wizard — category,
participants, event info, style, branding, the generation-preview summary
— is walkable with zero API key at all; Demo Mode additionally lets you
see and download a realistic-looking finished poster.

**Generation flow:** validate uploads → build a structured prompt
(`poster/prompt_builder.py`) → OpenAI image generation/edit
(`poster/image_generation_service.py`) → crop to the exact output size,
never stretched (`poster/image_processor.py`) → deterministic Python
typography + logo (`poster/typography.py`) → quality check → preview →
download. Only the **Generate Poster** / **Regenerate** / **Create
Variation** buttons ever call the paid API — normal Streamlit reruns don't.

**Local testing (no API key or cost required):**
```bash
pip install -r requirements-dev.txt
pytest tests/ -q
```
The test suite mocks the image-generation provider entirely — it never
calls OpenAI.

**Deployment:** fonts are bundled at `assets/fonts/Inter-Variable.ttf` (SIL
OFL) so typography doesn't depend on the host having fonts installed.
Uploaded photos are processed in memory and never written to disk or
stored permanently — Poster History is intentionally not built yet (see
Future Improvements).

**Troubleshooting:**
- *"AI Poster Studio isn't configured yet"* — the `[openai]` secret is
  missing; add it and reboot the app.
- *"The AI image service is temporarily unavailable"* — a transient
  OpenAI error after retries; wait and try again.
- *"The AI image service rejected this request"* — usually an unsupported
  photo or a prompt OpenAI's safety system declined; try different photos
  or wording.
- Nothing else in the dashboard should ever break because of this page —
  if it does, check the server logs for a line starting `poster_studio:`.

## Known gap — true day-by-day charting
The approved design's comparison chart plots a full month day-by-day.
Your monthly CSV only has period *totals*, not a row per day, so the app
compares month-vs-month totals instead (same insight, coarser resolution).
If you also export Tango's **daily** report, share one sample file and the
exact day-by-day chart can be wired up on the Daily report upload path
that's already in place.
