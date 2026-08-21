# StreamOperiq Phase Log

A dated, task-by-task record of the SaaS rebuild (see the "StreamOperiq
Blueprint" artifact for the full architecture and the 8-phase plan). Every
entry states what was done and, separately, the **expected result** —
something you can actually check against reality. If anything looks wrong in
dev or prod later, start here: find the entry, re-check its expected result,
and that tells you whether the problem is new or was introduced at a specific
known step.

This file gets a new entry every time a phase or task ships, and keeps
growing until Phase 8 (testing & migration) confirms the full rebuild is
running reliably in production — it doesn't stop once Phase 2 is done.

This is a task-level log. It's not a replacement for:
- **git commit messages** — the exact code diff for each change.
- **The blueprint artifact's Section 12** — business-level phase status (not started / pushed to dev / live in prod).

---

## 2026-08-22 — `run_migrations.py` succeeded against dev; connection troubleshooting notes

**What happened:** Took several attempts to connect to the dev Supabase
database from the admin migration script. Worth recording exactly what the
fix was, since this will need doing again for prod:

- Supabase's **Direct connection** host (`db.<project-ref>.supabase.co`)
  failed with a DNS resolution error on this network — likely an IPv6-only
  record that this network/ISP can't resolve. Not a config problem on our
  side; the **pooler** connection is the one that actually works here.
- The pooler (`aws-0-ap-southeast-1.pooler.supabase.com`) requires the
  username written as `postgres.<project-ref>`, not plain `postgres` — using
  plain `postgres` against the pooler produces a misleading
  "password authentication failed" error even with a correct password,
  because Postgres's error message strips the project-ref suffix regardless
  of which one was actually used.
- The real fix that closed it out: reset the database password in Supabase
  and copy the newly-generated password directly from Supabase's own copy
  button, rather than hand-typing or reusing an old one.

**Working connection string shape for this project** (host/username, not the
password): `postgresql://postgres.lqxgoqugfmjxkpcycdko:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`
— i.e. Session pooler, port 5432, project-ref-qualified username.

**Expected result:** `run_migrations.py` prints `StreamOperiq database
migration completed successfully.` — confirmed.

**Status:** Done. `memberships` and `subscriptions` tables now exist on dev.

---

## 2026-08-22 — `restricted_role_setup.sql` succeeded against dev

**What happened:** Ran the grant script (with the CREATE ROLE fix from
earlier) in the Supabase SQL Editor for dev, now that the tables it grants
against actually exist.

**Expected result:** No error; final SELECT returns one row for
`tangoops_app` with `rolsuper`/`rolcreatedb`/`rolcreaterole`/
`rolreplication`/`rolbypassrls` all `false`.

**Actual result:** Confirmed exactly as expected — `tangoops_app | false |
false | false | false | false | 10`.

**Status:** Done. `tangoops_app` now has SELECT/INSERT/UPDATE/DELETE on
`memberships` and `subscriptions` (plus every other runtime table), with no
elevated privileges.

---

## 2026-08-22 — Caught: local secrets.toml points at prod, not dev

**What happened:** Before running `backfill_memberships.py` — which defaults
to reading `.streamlit/secrets.toml` for its database connection — checked
what that file actually points to. It's the **prod** project
(`qppoydbfbtuzchtggeue`), confirmed by the user, not dev
(`lqxgoqugfmjxkpcycdko`). Running the backfill as originally planned would
have connected to prod. `run_migrations.py` and the SQL grant script were
unaffected (they used connection strings built explicitly for dev, not this
file), so nothing has actually touched prod — this was caught before it
happened, not after.

**Why this matters going forward:** any local script or `streamlit run
app.py` that reads secrets.toml without an explicit override defaults to
prod right now. Worth fixing this file to point at dev once today's
immediate work is done, so this risk doesn't resurface later.

**Fix for today:** use the `TANGOOPS_DATABASE_URL` environment variable to
override the connection for this one script run, leaving secrets.toml
untouched rather than risk editing prod credentials by hand right now.

**Status:** Caught, not yet fixed permanently. Working around it via env var
for today's backfill run.

---

## 2026-08-22 — `backfill_memberships.py` succeeded against dev

**What happened:** Ran the backfill against dev (via `TANGOOPS_DATABASE_URL`
override, not the prod-pointing `secrets.toml`). Preview showed 12 users
found, 12 new membership rows, 3 of 3 businesses to flag demo — confirmed
and typed `yes`.

**Expected result:** Output matching the preview exactly, no partial/failed
state.

**Actual result:** `Backfill complete: 12 membership rows inserted, 3
businesses flagged is_demo=true` — exact match to the preview.

**Status:** Done. `memberships` now has one row per existing user; all 3
pre-existing businesses are flagged `is_demo = true`. Remaining Phase 2 test
items: confirm existing logins are unaffected on the dev app, and confirm a
newly-created user gets both a `users` and a `memberships` row.

---

## 2026-08-22 — Caught: stale module cache after redeploy, `AttributeError: module 'store' has no attribute 'get_all_memberships'`

**What happened:** First login test on dev (Agency admin account) after
today's three pushes failed with `AttributeError: module 'store' has no
attribute 'get_all_memberships'`. Verified `get_all_memberships` genuinely
exists at line 559 of `store.py` in the exact deployed commit (`6ab048c`,
confirmed identical between local and `origin/dev`) — not a code or push
problem. Root cause: Streamlit Cloud's "Updated app!" auto-update after a
git push pulls new files onto disk but doesn't reliably force the
already-running process to re-import every module; the running process kept
an in-memory `store` module from before `memberships`-related functions
existed.

**Fix:** manually reboot the app from Streamlit Cloud's "Manage app" menu —
forces a genuine fresh process start and a full re-import of every module.

**Lesson for prod later:** after a deploy that changes `store.py` (or any
module `app.py` imports), don't assume the auto "Updated app!" pull is
enough — do a manual reboot to be sure, especially before testing.

**Status:** Resolved by reboot. Login then surfaced a second, unrelated
issue (below), now also resolved.

---

## 2026-08-22 — Caught: dev app's Streamlit secrets had the old `tangoops_app` password

**What happened:** After the reboot fixed the module-cache issue, login
failed again with `FATAL: password authentication failed for user
"tangoops_app"`. Cause: earlier today, `tangoops_app`'s password was reset
via `ALTER ROLE` (to run the backfill script through an env var, bypassing
the prod-pointing local `secrets.toml`). That changed the password in the
database, but the **dev app's own Streamlit Cloud secrets** still held the
old one — a direct, foreseeable side effect of the password-reset workaround
that wasn't caught until this test.

**Fix:** updated the dev app's Streamlit Cloud secrets (`[postgres]
connection_string`) with the new password, username/host left unchanged
since those were already correct. App rebooted again.

**Expected result:** Agency Owner and Sub-Agency logins succeed, dashboards
match pre-Phase-2 behavior exactly.

**Actual result:** Confirmed by the user — logged in successfully as both
Agency Admin (Owner) and Sub-Agency Admin, both working normally.

**Status:** Done. Test checklist item 1 (existing logins unaffected) passed.

---

## 2026-08-22 — Phase 2 test checklist: all 4 items passed in dev

**What was done:** Created one new test user through the dev app's normal
UI flow.

**Expected result:** The new username appears in both the `users` table and
the `memberships` table (proving `create_user()`'s atomic dual-write works
for new logins, not just backfilled old ones).

**Actual result:** Confirmed by the user — visible in both tables.

**Full checklist status:**
1. Existing logins unaffected — ✅ passed (Agency Owner + Sub-Agency Admin).
2. `memberships` row count sane — ✅ passed (12 rows, matched 12 users).
3. `is_demo` flagged on pre-existing businesses — ✅ passed (3 of 3).
4. New user gets both `users` and `memberships` rows — ✅ passed.

**Status: Phase 2 is fully verified in dev.** Next gate per the staged
rollout process: prod push approval.

---

## 2026-08-21 — Phase 1: Rebranding

**What was done:** TangoOps rebranded to StreamOperiq (brand tokens, logo,
page titles). Already live in prod before this log existed; recorded here
for completeness.

**Expected result:** No user-facing "Tango" branding remains outside
source-provenance labels (e.g. "Tango profile", "tango.me" URLs, which are
intentionally kept — see `BRAND-SPEC.md`'s rename boundary).

**Status:** Live in prod (commit `0658a57` and later). Verified.

---

## 2026-08-21 — Phase 2, commit `9ab0f6b`: memberships table

**What was done:** Added the `memberships` table and `businesses.is_demo`
column to the schema; added `scripts/backfill_memberships.py`;
`current_user_context()` in `app.py` now resolves role/business through
`memberships` first, falling back to reading `users` directly only if a
login has zero active membership rows.

**Expected result once migrated, backfilled, and deployed:**
- Every existing user (owner, sub-agency) logs in and sees an identical
  dashboard/permissions to before this change — nothing should look or
  behave differently for them.
- `SELECT COUNT(*) FROM memberships` should roughly equal the number of
  active users with a role of `owner` or `sub_agency` in the `users` table.
- Every business that existed before the backfill ran shows
  `is_demo = true`.
- Creating one new test user produces both a `users` row and a matching
  `memberships` row.

**How to verify:** Run the 4-point checklist in the blueprint's Section 12
"Pick up here" callout.

**Status:** Pushed to `dev`. **Not yet run against the dev database** —
`run_migrations.py` and `backfill_memberships.py` have not been executed
yet, so the expected results above cannot be checked yet.

---

## 2026-08-21 — Phase 2, commit `7fd96a0`: subscriptions table + memberships grant fix

**What was done:** Added the `subscriptions` table (schema only — no
`store.py`/`app.py` code reads or writes it yet). Separately, fixed a real
gap: the `memberships` table (added in the previous commit) had never been
granted to the restricted `tangoops_app` database role in
`database/restricted_role_setup.sql`.

**Expected result:**
- Before the grant fix: running `run_migrations.py` then trying to use the
  app would have failed at startup with a `RuntimeError` from
  `_verify_runtime_permissions()` — the app checks it has SELECT/
  INSERT/UPDATE/DELETE on every table in `RUNTIME_TABLES`, and `memberships`
  would have been missing that grant.
- After re-running `restricted_role_setup.sql` (updated in this commit):
  the app should start normally with no permission error, and
  `scripts/verify_database_role.py` should print `PASS`.
- `subscriptions` table exists in the database but stays empty — nothing
  writes to it yet, so an empty table here is correct, not a bug.

**How to verify:** Run `python3 scripts/verify_database_role.py` against dev
after re-running the SQL setup script — should print `PASS: role
tangoops_app has required StreamOperiq access and no administrator
privileges.` with no error.

**Status:** Pushed to `dev`. **Not yet run** — same as above, the grant
script has not been re-executed against dev yet.

---

## 2026-08-22 — Phase 2, commit `6ab048c`: memberships.expires_at (Trial Viewer)

**What was done:** Added a nullable `expires_at` column to `memberships`,
with a CHECK constraint (`expires_at IS NULL OR expires_at > created_at`).
Documented a new 8th role, **Trial Viewer** (read-only, no export,
time-boxed), in the blueprint's Section 03 and new Section 15. No new
table, so no grant-script change was needed this time.

**Expected result:**
- Existing rows in `memberships` are unaffected — `expires_at` defaults to
  `NULL` for all of them, meaning "permanent," which is correct for every
  role except Trial Viewer.
- Inserting a membership row with `expires_at` set to a time *before*
  `created_at` should fail with a constraint violation (proves the CHECK is
  active); with `expires_at` in the future, or `NULL`, it should succeed.
- **Not yet functional:** nothing in the app actually reads `expires_at` at
  login yet, and there is no UI to grant Trial Viewer access. A trial
  membership created directly in the database today would not actually
  expire on its own — that enforcement is Phase 3 work. Don't expect
  trial-expiry behavior to work end-to-end until Phase 3 ships.

**How to verify:** After migrating, check the column exists
(`\d memberships` in `psql`, or query `information_schema.columns`) and
that existing rows show `expires_at IS NULL`.

**Status:** Pushed to `dev`. Not yet run.

---

## 2026-08-22 — Fix: `restricted_role_setup.sql` wasn't actually re-runnable

**What was done:** The file claimed to be safe to re-run in full, but its
`CREATE ROLE tangoops_app` line would have thrown "role already exists" on
dev, since that role was created in earlier security-hardening work.
Wrapped it in a `DO $$ ... IF NOT EXISTS ... $$` block so the whole file can
now genuinely be re-run without editing anything.

**Expected result:** Pasting the entire file into the Supabase SQL Editor
for dev and running it should complete with no error, whether or not
`tangoops_app` already exists. The final `SELECT` at the bottom should
return exactly one row for `tangoops_app` with `rolsuper`, `rolcreatedb`,
`rolcreaterole`, `rolreplication`, `rolbypassrls` all `false`.

**How to verify:** Run it, confirm no error, check that final SELECT's
output.

**Status:** Fixed locally, not yet pushed to `dev` — see chat for the exact
copy-pasteable SQL.

---

## 2026-08-22 — Fix: instructions had the run order backwards

**What was done:** Told the user to run the SQL grant script before the
migration script. Wrong order — the grant script does `GRANT ... ON TABLE
public.memberships`, which needs `memberships` to already exist, and only
`run_migrations.py` (running `store.SCHEMA` as the database administrator)
actually creates that table. Running the grant script first fails with
`ERROR: 42P01: relation "public.memberships" does not exist`. Caught when
the user hit exactly that error running it live.

**Expected result:** With the corrected order below, the migration script
creates the tables, then the grant script (independently re-runnable per the
earlier fix) succeeds against tables that now actually exist.

**Status:** Documentation-only fix, corrected here and in the "Pick up
here" callout in the blueprint artifact.

---

## 2026-08-22 — Hardening: `current_user_context()` now survives a missing/ungranted `memberships` table

**What was done:** The existing fallback only covered "zero active
membership rows" (an empty query result). It did not cover the
`memberships` query failing outright — e.g. if app code were ever live
before `run_migrations.py` had created the table, or before
`restricted_role_setup.sql` had granted it, every login would crash with an
uncaught exception instead of falling back gracefully. Wrapped the
`load_all_memberships_df()` call in `current_user_context()` in a
try/except that treats any failure the same as an empty result.

**Why this matters for prod specifically:** dev sat with this gap for about
a day between the code landing and the migration running, with no visible
impact only because nobody happened to log in during that window. Prod has
real, continuous usage — the same gap there would have caused real login
failures. Closing this before prod gets any of this code.

**Expected result:** Behavior is identical to before on the success path
(dev's already-passing tests are unaffected, since the query has been
succeeding there since the migration ran). On a hypothetical failure path,
login now falls back to the pre-Phase-2 `users`-table lookup instead of
crashing.

**Status:** Pushed to dev (no re-test needed — provably a no-op change on
the path dev already verified). Included in the prod push below.

---

## Phase 2 → prod rollout (started 2026-08-22 evening)

Following the exact same steps that succeeded on dev, against prod's
database and app. See above for the working connection-string shape,
troubleshooting notes, and lessons already learned — expect some of them to
recur here, especially the pooler/DNS and password mismatch issues.

1. Run `scripts/run_migrations.py` against **prod** — creates the
   `memberships`/`subscriptions` tables.
2. Run `database/restricted_role_setup.sql` in the Supabase SQL Editor for
   **prod** — grants `tangoops_app` access to the new tables. (Prod's
   `tangoops_app` role already exists, same as dev did, so the `CREATE
   ROLE` block will skip — no password to set there.)
3. Run `scripts/backfill_memberships.py` against **prod** — real customer
   data this time, not dummy tenants. Preview the counts carefully before
   typing `yes`.
4. Push the code (`app.py`, `store.py`, and everything else already on
   `dev`) to `origin/main`.
5. Confirm real prod logins still work — same spirit as the dev checklist,
   but this time it's actual customers' accounts, not test ones.

---

## 2026-08-22 — `run_migrations.py` succeeded against prod

**What happened:** Ran the migration against prod using the Session pooler
+ project-ref-qualified username format learned from today's dev
troubleshooting — no connection issues this time.

**Expected result:** `StreamOperiq database migration completed
successfully.`

**Actual result:** Exact match, no error.

**Status:** Done. `memberships` and `subscriptions` tables now exist on
prod. Next: grant script.

---

## 2026-08-22 — `restricted_role_setup.sql` succeeded against prod

**Expected result:** No error; final SELECT returns `tangoops_app` with
every privilege flag `false`.

**Actual result:** Confirmed by the user — matched exactly.

**Status:** Done. `tangoops_app` now has access to `memberships` and
`subscriptions` on prod, same as dev. Next: backfill.

---

## 2026-08-22 — `backfill_memberships.py` against prod: caught a stale env var pointing it at dev instead

**What happened:** First backfill attempt against prod reported "Nothing to
do" — 13 users found, 0 new rows, 0 businesses to flag. That matched dev's
state *exactly* (12 original + 1 test user created during dev's checklist =
13), which was the tell. Root cause: `TANGOOPS_DATABASE_URL`, exported
earlier in this same terminal session to route dev's backfill around the
prod-pointing `secrets.toml`, was still set — and the script checks that
env var before falling back to `secrets.toml`. It silently hit dev again
instead of prod. `secrets.toml` itself was correct and untouched.

**Verification before retrying (not just trusting the fix):**
1. Cancelled the run cleanly (typed anything but `yes` — the script exits
   with "no changes made").
2. `unset TANGOOPS_DATABASE_URL`, confirmed with `echo` that it printed
   empty.
3. Directly queried prod's `businesses` table
   (`SELECT business_id, business_name, status, created_at FROM businesses
   ORDER BY created_at;`) and confirmed three distinct, real-looking
   business names (NorthStar Talent Network, Elevate Live Agency, Horizon
   Creator Network) — nothing like dev's dummy test businesses.

**Expected result (re-verified prod-specific):** 12 users found, 12 new
membership rows, 3 of 3 businesses flagged demo.

**Actual result:** `Backfill complete: 12 membership rows inserted, 3
businesses flagged is_demo=true` — exact match.

**Lesson for next time an env var override is used:** `unset` it
immediately after the one command it was needed for, don't leave it
lingering in the shell session — it silently overrides `secrets.toml` on
every subsequent script run in that same terminal, with no warning.

**Status:** Done. `memberships` now populated on prod; all 3 real
businesses flagged `is_demo = true` — same treatment as dev's dummy ones,
per the earlier confirmed decision that all current tenants (real or not)
predate the SaaS billing model and shouldn't be enforced against yet.
