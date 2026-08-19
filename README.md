# TangoOps – Agency Control

A multi-business referral-agency platform. One deployment can host several
completely separate businesses (ABC, DEF, ...), each with its own
broadcasters, sub-agencies, and logins — fully walled off from every other
business on the same platform.

- **Platform admin** (you, or whoever runs the platform) creates businesses
  and their first owner login. Nothing else — no broadcaster data.
- **Business owner** (e.g. ABC) sees everything inside their own business:
  upload the monthly/daily `referral_statistics` CSV, see the full
  broadcaster list, assign any broadcaster to any sub-agency directly from
  that list, manage sub-agencies, users, and data — all scoped only to ABC.
  A new upload for a period replaces that period only; history is kept.
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
Repeat Step 4.5 — upload the new file, tag it with the right period. The
same period uploaded twice replaces the first; other periods are untouched,
which is what lets the dashboard show active/inactive trends and the
insights (retention, at-risk, growth) across months. If a sub-agency user
does their own upload, any of their previously-unassigned broadcasters in
that file get attributed to their agency automatically.

### Adding Agency direct hires to an existing month
When a smaller file contains only broadcasters recruited directly by the
Agency, open **Monthly report** and choose **Add Agency direct hires** before
uploading it. This preserves every existing row in that month, adds or updates
only the profiles in the smaller file, and classifies them as **Agency Direct**.
Do not assign those profiles to a Sub-Agency. The Agency overview then compares
direct hires with Sub-Agency hires and shows the commission-adjusted earnings mix.

## Known gap — true day-by-day charting
The approved design's comparison chart plots a full month day-by-day.
Your monthly CSV only has period *totals*, not a row per day, so the app
compares month-vs-month totals instead (same insight, coarser resolution).
If you also export Tango's **daily** report, share one sample file and the
exact day-by-day chart can be wired up on the Daily report upload path
that's already in place.
