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

---

## 2026-08-22 — Found: prod app connects to the database as the Postgres superuser, not the restricted `tangoops_app` role

**This is a pre-existing security gap, not caused by Phase 2.** Discovered
only because today was the first time anyone actually loaded the Platform
Admin dashboard on live prod — `SECURITY_CHECKLIST.md` had this exact live
test listed as **Blocked** beforehand, meaning nobody had verified it in
the running app itself, only via standalone scripts.

**What was found:** After deploying and rebooting the prod app, logging in
as Platform Admin showed "The platform security configuration requires
administrator attention" — the app's own fail-closed check
(`get_database_role_posture()` in `store.py`, gated behind
`is_platform_admin` in `app.py`) refuses to render that page if the live
database connection has any elevated privilege (superuser, create-database,
create-role, replication, or RLS-bypass).

Checked prod's actual Streamlit Cloud secrets: the `[postgres]
connection_string` username is `postgres.qppoydbfbtuzchtggeue` — the full
Supabase admin/superuser account — not `tangoops_app`, the restricted role
that was supposedly already set up and verified per `SECURITY_CHECKLIST.md`'s
"Completed" section. Most likely explanation: the restricted role was
verified in isolation with the standalone scripts
(`verify_database_role.py`, `smoke_test_runtime_database.py`), but the live
app's actual secrets were never switched over to use it.

**Scope of impact:** Confirmed **not** affecting regular customer logins —
Agency Owner and Sub-Agency accounts resolve through a separate code path
that never calls this check. This is specifically a Platform Admin
dashboard issue. Also means the app has been running with far more database
privilege than it needs for its entire runtime, which is a real exposure
regardless of whether it's been exploited — least-privilege was the whole
point of the earlier security-hardening work, and this defeats it.

**Fix (pending, not yet applied as of this log entry):**
1. `ALTER ROLE tangoops_app WITH PASSWORD '<new-password>';` on prod.
2. Update prod's Streamlit Cloud secrets: change the `[postgres]
   connection_string` username from `postgres.qppoydbfbtuzchtggeue` to
   `tangoops_app.qppoydbfbtuzchtggeue`, password to match. Host/port/db
   unchanged.
3. Save, reboot, reload Platform Overview.

**Expected result once fixed:** Platform Overview loads normally instead of
showing the fail-closed message; `get_database_role_posture()` reports all
five privilege flags `false` for prod, same as dev already does.

**Status:** Fixed. First attempt only changed the password, leaving the
username as `postgres` — produced a second, misleading-looking error
(`password authentication failed for user "postgres"`) that turned out to
be the same root cause, just half-fixed. Corrected connection string
(`tangoops_app.qppoydbfbtuzchtggeue`, new password, same host/port/db)
applied, app rebooted. **Confirmed:** Platform Admin login now succeeds and
loads Platform Overview normally — the fail-closed security check passes.

---

## 2026-08-22 — Phase 2: prod verification complete

**Confirmed by the user:** both Platform Admin and Agency Admin logins
succeed on prod, matching dev's verified behavior. Combined with the
earlier-confirmed migration, grants, and backfill (all against real
customer data, cross-checked against actual business names to rule out a
repeat of the dev/prod mixup), **Phase 2 is fully live and verified in
prod.**

**Status: Phase 2 — done.** `memberships`, `subscriptions`,
`memberships.expires_at`, the hardened `current_user_context()`, and the
database-role fix are all live on both dev and prod. Next: Phase 3 (Roles &
permissions), per the blueprint's Section 12.

---

## 2026-08-22 — Phase 3a: roles/permissions schema + seed data (safe, additive)

**Scope decision:** `is_owner` alone is referenced 34 times across
`app.py`, `is_sub_agency` 5 times, `is_platform_admin` 4 times — but most of
those are cosmetic (labels, column choices), not real access-control gates.
Mass-rewriting all of them in one pass is real surgery on the app's actual
security logic, spread across a 3,320-line file, with no way to click
through the running app to verify each change before it ships. Splitting
Phase 3 in two: 3a (this entry) is schema + seed data only, zero risk,
same pattern as Phase 2's DB work. The actual `app.py` migration (3b) is a
separate, deliberately deferred pass.

**What was done:** Added `roles`, `permissions`, `role_permissions` tables.
Seeded 8 roles (matching Section 03 of the blueprint) and 17 permission
keys grounded in the app's real pages/actions (not abstract CRUD verbs),
with a `role_permissions` mapping per role. Added `get_roles()`,
`get_permissions()`, `get_role_permissions()`, and `has_permission()` to
`store.py` — none of them called from `app.py` yet. Extended the grant
script and both database verification scripts to cover the 3 new tables.

**Expected result:** Zero behavior change anywhere in the running app —
these tables are pure additive schema/data that nothing reads yet. After
migrating: `roles` has 8 rows, `permissions` has 17, `role_permissions` has
one row per (role, permission) pair from the seed list above — all
enforced by foreign keys, so a typo in either seed list would fail the
migration loudly rather than silently insert bad data.

**Status:** Implemented, compiled, reviewed, pushed to dev (`446f4c5`).

---

## 2026-08-22 — Phase 3a: `run_migrations.py` against dev, another admin-vs-restricted-role mix-up

**What happened:** Two attempts used `tangoops_app`'s connection string
(the restricted app role) instead of the admin `postgres` account —
`run_migrations.py` correctly refuses to run against a non-admin role
rather than silently failing partway through a schema change. Same
category of mix-up as earlier today's password/role confusion — worth
double-checking which of the two accounts (`postgres` for schema changes,
`tangoops_app` for the app itself) a connection string belongs to before
pasting it anywhere.

**Expected result:** `StreamOperiq database migration completed
successfully.`

**Actual result:** Confirmed by the user — succeeded once the correct
admin connection string was used.

**Status:** Done. `roles`, `permissions`, `role_permissions` tables now
exist on dev, seeded. Next: grant script.

---

## 2026-08-22 — Phase 3a: grant script succeeded against dev

**Expected result:** No error; final SELECT returns `tangoops_app` with
every privilege flag `false`.

**Actual result:** Confirmed by the user — matched exactly.

**Status:** Done. `tangoops_app` now has access to `roles`, `permissions`,
`role_permissions` on dev. Next: verify the actual seed data landed
correctly (row counts, foreign keys) via Table Editor.

---

## 2026-08-22 — Phase 3a: seed data verified correct on dev

**Expected result:** `roles_count = 8`, `permissions_count = 17`,
`role_permissions_count = 35`.

**Actual result:** Exact match — `8, 17, 35`.

**Status: Phase 3a — fully verified in dev.** Schema, grants, and seed data
all confirmed correct. Nothing in the app reads any of it yet, so there's
no login/UI behavior to test this time — the verification is the row
counts themselves. Ready for a prod-push decision (zero behavior risk,
same reasoning as Phase 2's schema-only commits).

---

## 2026-08-22 — Phase 3a on prod: `run_migrations.py` blocked for an extended time by a genuine Supabase-side credential sync issue

**What happened:** Unlike every previous migration today, prod's `postgres`
account kept failing `password authentication failed` across many
attempts, despite methodically ruling out every configuration explanation:

- Confirmed correct username format (`postgres.qppoydbfbtuzchtggeue`, not
  `tangoops_app` — that exact mix-up recurred twice before landing on the
  right one).
- Confirmed correct host/port for both Session pooler (5432) and
  Transaction pooler (6543) — both failed identically, ruling out a
  pooler-mode-specific cache.
- Confirmed Direct connection fails on DNS/IPv6 for this network (known,
  unrelated — same as dev).
- Reset the password multiple times via Supabase's official "Reset
  database password" UI (confirmed via direct question — not a SQL
  command, not accidentally resetting `tangoops_app` again).
- Confirmed the new password was plain alphanumeric (no special
  characters needing URL-encoding) by having the user check its shape
  without sharing it — ruled out an encoding issue. (The actual password
  did end up posted in chat during this process — treat it as compromised
  regardless of "ignore security for now"; rotate it again once things are
  stable.)
- Attempted `ALTER ROLE postgres WITH PASSWORD ...` directly in the SQL
  Editor as a bypass — blocked by Postgres/Supabase itself: `ERROR: 42501:
  permission denied to alter role — Only superusers can alter privileged
  roles`. Confirms Supabase reserves the `postgres` role's password
  changes to its own dashboard control plane; even the SQL Editor's session
  isn't a true superuser for this specific purpose.

**Root cause (working theory, matches the fix):** A genuine Supabase-side
sync gap between the `postgres` role's actual password and what the
pooler (Supavisor) was authenticating connections against — a known
category of issue with managed Postgres poolers occasionally not picking
up a credential change cleanly. This exact process had worked fine for
prod's *first* migration earlier the same day, so something changed
in between, not a mistake in how the connection was being built.

**Fix:** restarted the Supabase project (Project Settings → General →
Restart project) and rebooted the Streamlit Cloud app. Migration succeeded
immediately after, using the exact same connection string and password
that had failed repeatedly before the restart.

**Lesson for next time this happens:** if a freshly-reset, correctly
formatted admin password keeps failing across both pooler modes with no
other explanation, a project restart is a legitimate, fairly low-risk next
step (brief connection drop, app recovers or needs a manual reboot) —
don't keep resetting the password indefinitely, that wasn't the actual
problem here.

**Status:** Resolved. `roles`, `permissions`, `role_permissions` tables now
exist on prod. Next: grant script.

---

## 2026-08-22 — Phase 3a: grant script succeeded against prod

**Expected result:** No error; final SELECT returns `tangoops_app` with
every privilege flag `false`.

**Actual result:** Confirmed by the user — matched exactly.

**Status:** Done. `tangoops_app` now has access to `roles`, `permissions`,
`role_permissions` on prod. Next: verify seed data row counts.

---

## 2026-08-22 — Phase 3a: prod seed data verified correct

**Expected result:** `roles_count = 8`, `permissions_count = 17`,
`role_permissions_count = 35`.

**Actual result:** Exact match — `8, 17, 35`.

**Status: Phase 3a — fully verified on prod, same as dev.** Schema,
grants, and seed data confirmed correct on both environments. Code push to
`main` is next — this is schema/data that already exists in the database
independent of the code push, so pushing the code now just brings
`store.py`'s `has_permission()`/`get_roles()`/etc. helper functions (still
unused by `app.py`) into sync between dev and prod.

---

## 2026-08-22 — Phase 3b, first slice: Agency Manager is a real, working role

**This is genuine behavior change**, unlike everything in Phase 2 and
Phase 3a — unlike those, this needs real testing in dev before it goes
anywhere near prod.

**Scope decision:** mapped every `is_owner`/`is_sub_agency`/
`is_platform_admin` call site in `app.py` (34/5/4 occurrences) before
touching anything. Most `is_owner` sites are the same semantic question —
"full tenant view vs. own-scoped view" — which maps directly onto
`broadcaster.view` in the Phase 3a permission seed. Only a handful are
genuinely Owner-exclusive actions. Did **Agency Manager only** in this
slice; Auditor, Broadcaster, and Trial Viewer's expiry enforcement are
separate, not-yet-started work.

**What was done:**
- `current_user_context()`'s role whitelist now accepts `agency_manager`
  (both the memberships-path and the fallback-path checks).
- Added `is_manager` and a derived `is_owner_or_manager` boolean.
- `allowed_pages_by_role["agency_manager"]` = everything Owner has **except**
  SubAgencies, CreateAgency, DataManagement, and Payouts.
- Replaced `is_owner` with `is_owner_or_manager` at 28 call sites where the
  semantic question was "full view" — the dashboard, Statistics,
  Broadcasters, BroadcasterDetail, Assign, and Upload pages.
- **Left `is_owner` unchanged at 6 sites, deliberately:** Payouts,
  CreateAgency, DataManagement (Manager's permission set excludes all
  three), and **SubAgencies** — which Section 03 of the blueprint actually
  says Manager should see, but that page has a live commission-rate edit
  control (`update_agency_commission`) Manager's permission set excludes.
  Chose the safer gap (Manager sees slightly less than spec) over the risk
  of a permission leak (Manager editing commission rates). Worth revisiting
  once/if that page's view and edit responsibilities are split apart.
- **Caught one real bug during the mapping**, not introduced by this
  change: the upload-confirmation auto-assign logic (`if not is_owner: ...
  store.assign_broadcasters(..., user_agency, ...)`) would have silently
  broken for Manager, since `user_agency` is `None` for a tenant-wide role
  — auto-assigning uploads to `None` as a sub-agency name. Fixed to check
  `is_sub_agency` directly instead, which is what the logic actually means.
- **UserAccess page got special handling**, not just extended: Manager can
  access it, but the "Create User" role dropdown only offers `sub_agency`
  to a Manager (never `owner` or `agency_manager`), and the
  disable/enable/reset-password controls on existing users are hidden
  (replaced with "Owner-managed account") whenever the target user's role
  isn't `sub_agency` and the actor isn't the Owner. Enforces "no role can
  invite/suspend a role above or equal to itself" (Section 03) at the only
  two places a Manager could otherwise act on another login.

**Expected result:**
- Existing Owner and Sub-Agency logins behave **identically** to before —
  none of their code paths changed value (`is_owner`/`is_sub_agency` are
  still computed the same way; only new variables were added).
- A test user created with `role = 'agency_manager'` (via SQL, since the
  UserAccess dropdown to create one requires being logged in as Owner
  first) should be able to log in and see: Admin, Statistics, Broadcasters,
  BroadcasterDetail, Assign, UploadMonthly, UploadDaily, UserAccess,
  MyProfile — with the same "full tenant view" as an Owner on all of them.
- That same Manager should be **blocked** from: SubAgencies, CreateAgency,
  DataManagement, Payouts (page-level, via `allowed_pages_by_role`).
- In UserAccess specifically, a Manager should only be able to create
  `sub_agency` logins, and should see "Owner-managed account" instead of
  Disable/Enable/Reset controls on the existing Owner row.

**How to verify:** In dev's Supabase Table Editor, insert one test
`memberships` row with `role = 'agency_manager'` for an existing test
tenant (or promote an existing test sub-agency login), log in as that
account, and walk through every item in "Expected result" above.

**Status:** Implemented, compiled, self-reviewed, pushed to dev (`caed655`).
Auditor role, Broadcaster role, and Trial Viewer's `expires_at` login-time
enforcement remain separate, not-yet-started slices of Phase 3b.

---

## 2026-08-22 — Phase 3b: real dev testing caught a real bug — sidebar showed nav links to pages Manager couldn't actually open

**What happened:** User promoted an existing test sub-agency login to
`agency_manager` and logged in to test. Page-level access worked correctly
(could reach the pages Manager should have; blocked from the ones it
shouldn't) — but the sidebar showed clickable links for Payouts,
CreateAgency, SubAgencies, and DataManagement anyway, because the
sidebar's outer gate (`if is_owner_or_manager:`) was extended for this
change, but the individual `nav_button()` calls inside it weren't further
filtered by `allowed_pages_by_role`. Clicking one of those links wouldn't
have actually worked - a separate page-level redirect check
(`elif st.session_state.get("page") not in allowed_pages_by_role[user_role]`)
would bounce back to the dashboard on the next rerun, and each of those
page's own hard `is_owner` gate would also still block it. **Not a
security hole - a cosmetic/UX bug**, but a real one, and exactly the kind
of thing this dev testing step exists to catch before it reaches prod.

**Fix:** `nav_button()` itself now checks `allowed_pages_by_role` and
simply doesn't render if the current role can't access that page — fixes
it once, for every nav button, rather than needing every call site to
remember to gate itself individually (which is exactly what got missed
here).

**Expected result after the fix:** Logged in as the test `agency_manager`
account, the sidebar should show only: My Dashboard, Broadcaster Dashboard,
Broadcasters, Assign Broadcasters, Monthly/Daily Report, User Access, My
Profile. No Recruiter Dashboard (SubAgencies), Broadcaster Rewards
(Payouts), Create Sub-Agency, or Data Management links should appear at
all.

**Status:** Fixed, compiled, pushed to dev (`964fe17`).

---

## 2026-08-22 — Phase 3b, first slice: Agency Manager fully verified in dev

**Confirmed by the user, after the sidebar fix and an app reboot:**
- Sidebar shows exactly the right set of links for the test `agency_manager`
  account — no Recruiter Dashboard, Broadcaster Rewards, Create Sub-Agency,
  or Data Management.
- User Access's "Create User" role dropdown only offers Sub-Agency.
- The Owner's row in User Access's existing-users list shows "Owner-managed
  account" instead of Disable/Reset controls.

**Status: Agency Manager slice of Phase 3b — done, verified in dev.**
Remaining before this could go to prod: revert the test promotion
(`UPDATE memberships SET role = 'sub_agency' WHERE ...` back to its
original value) so dev doesn't carry a lingering test artifact. Auditor,
Broadcaster, and Trial Viewer's `expires_at` enforcement remain separate,
not-yet-started slices of Phase 3b.

---

## 2026-08-22 — Phase 3b Agency Manager: pushed to prod and fully verified there too

**What happened:** Code (pure `app.py` — no schema change needed, Phase 3a
already put `roles`/`permissions`/`role_permissions` on prod) pushed to
`main`, app rebooted. User confirmed all 3 prod businesses are test
tenants, not real customers, so the same promote → verify → revert cycle
used on dev was safe to run on prod directly.

**Expected result:** Same checklist as dev — existing Owner/Sub-Agency
logins unaffected; a promoted `agency_manager` test account shows the
correct sidebar (no Recruiter Dashboard/Payouts/Create Sub-Agency/Data
Management links), the full-tenant view on its visible pages, and the
correct User Access restrictions (Sub-Agency-only create dropdown,
"Owner-managed account" on the Owner's row).

**Actual result:** Confirmed by the user — "tested all running as
expected."

**Status: Phase 3b's Agency Manager slice — done. Live and verified on
both dev and prod.** `main` and `dev` both at commit `2cdd767`.
**Outstanding cleanup, unconfirmed:** revert both test promotions (dev's
and prod's) back to `sub_agency` — asked the user to confirm both are
done, not verified in this log yet. Auditor role, Broadcaster role, and
Trial Viewer's `expires_at` login-time enforcement remain separate,
not-yet-started slices of Phase 3b.

---

## 2026-08-22 — Phase 3b, second slice: Auditor is a real, read-only role

**No database change needed** — `auditor`'s permissions were already
seeded in Phase 3a (`agency.view_dashboard`, `audit.view`, `report.export`,
`profile.manage`). Pure `app.py` work, same as Agency Manager.

**What was done:**
- `current_user_context()`'s role whitelist now also accepts `auditor`.
- Added `is_auditor` and a new, broader `can_view_full_tenant = is_owner or
  is_manager or is_auditor` variable — deliberately distinct from
  `is_owner_or_manager`, which stays reserved for pages Manager can *act* on
  but Auditor (zero write rights) cannot: Assign, Upload, User Access.
- Replaced `is_owner_or_manager` with `can_view_full_tenant` at 23 sites
  that are pure viewing (dashboard, Statistics, Broadcasters,
  BroadcasterDetail, the sidebar's own rendering) — left the 5 write-gated
  sites (Assign's gate, the daily-upload restriction, the upload
  confirmation's internal logic, User Access's gate) on the narrower
  `is_owner_or_manager` so Auditor never gets them.
- `allowed_pages_by_role["auditor"]` = Admin, Statistics, Broadcasters,
  BroadcasterDetail, **AuditLog** (new), MyProfile. No Assign, Upload, or
  User Access at all.
- **New `AuditLog` page** — the `security_audit` table already had a
  viewer, but it was embedded inside the Owner-only Data Management page
  alongside a destructive "Clear This Period" action. Rather than try to
  carve out read-only access within that page (real risk of leaking the
  destructive control), added a standalone read-only page reusing the same
  `store.get_security_audit()` call. Owner/Manager still see their
  original embedded version in Data Management unchanged; Auditor gets
  this new page instead. Sidebar nav link added under "Administration" —
  relies on `nav_button()`'s self-filtering (added during the Agency
  Manager bug fix) to only appear for roles that actually have it.
- Fixed a latent display bug while in there: `role_labels` in the User
  Access page didn't have an "auditor" entry, so an Auditor row in the
  existing-users list would have silently mislabeled as "Agency Owner."
  Fixed, and changed the fallback default from a specific (wrong) label to
  a generic title-cased version of the actual role string, so any future
  unlisted role fails safely instead of misleadingly.
- **No UI to grant Auditor access yet** — same as Trial Viewer, this is a
  SQL-only promotion for now (`UPDATE memberships SET role = 'auditor'
  WHERE ...`), consistent with how Agency Manager was tested before a
  "Create User" flow existed for it either.

**Expected result:** A promoted `auditor` test account should see the
sidebar with the same page set as Agency Manager minus Assign/Upload/User
Access, plus AuditLog. On Admin/Statistics/Broadcasters/BroadcasterDetail,
sees the full tenant view (like Owner/Manager), not a scoped one. AuditLog
shows the same security activity data Owner sees in Data Management.
Cannot reach Assign, Upload, User Access, CreateAgency, DataManagement,
SubAgencies, or Payouts — page-level redirect blocks all of them.

**How to verify:** Same pattern as Agency Manager — promote an existing
test `sub_agency` login to `auditor` via SQL, log in, walk through
"Expected result" above, then revert.

**Status:** Implemented, compiled, self-reviewed, pushed to dev (`de5e543`).

---

## 2026-08-22 — Auditor slice fully verified in dev

**Confirmed by the user:** "tested all running as expected" — sidebar
shows exactly the right page set (including the new Audit Log link), full
tenant view on the visible pages, Audit Log page loads correctly, and no
access to Assign/Upload/User Access/CreateAgency/DataManagement/
SubAgencies/Payouts.

**Status: Auditor slice of Phase 3b — done, verified in dev.** Ready for
prod, same as Agency Manager's rollout.

---

## 2026-08-22 — Auditor slice: pushed to prod, fully verified there too

**What happened:** Code pushed to `main` (no schema change needed), app
rebooted. User confirmed all 3 prod businesses are test tenants, ran the
same promote → verify → revert cycle directly on prod.

**Actual result:** Confirmed by the user — "tested all running as
expected."

**Status: Auditor slice of Phase 3b — done. Live and verified on both dev
and prod.** `main` and `dev` both at commit `a2ca33a`. Remaining Phase 3b
work: Trial Viewer's `expires_at` enforcement (next), then Broadcaster
(biggest lift — needs actual broadcaster login accounts, which don't
exist at all today).

---

## 2026-08-22 — Phase 3b, third slice: Trial Viewer's expiry actually enforced

**What was done:**
- `store.get_all_memberships()` and `get_memberships()` now select
  `expires_at` — they didn't before, so nothing could check it even though
  the column has existed since Phase 2.
- `current_user_context()` now filters out any membership row where
  `expires_at` is in the past, treating it exactly like an inactive
  membership (same generic "session no longer valid" message — a lapsed
  trial account gets no special message hinting that the access was
  time-limited rather than simply revoked).
- Added `is_trial_viewer` and `can_view_full_tenant` now includes it
  alongside Owner/Manager/Auditor.
- Added `can_export = not is_trial_viewer` and gated the one reachable,
  previously-ungated `st.download_button` (the Statistics page's broadcaster
  report) behind it. (Two other download buttons found in the codebase are
  on Payouts/SubAgencies, which Trial Viewer has no page access to at all —
  nothing to gate there.)
- **Caught a second export surface while checking**: `st.dataframe()` has
  its own built-in toolbar with a CSV download icon, entirely separate from
  explicit `download_button` calls — gating the buttons alone wouldn't have
  been enough. Added conditional CSS (only injected `if is_trial_viewer`)
  hiding that toolbar. **This one genuinely needs visual confirmation in
  dev** — it's a CSS selector guess at Streamlit's current toolbar
  test-id(s), not something provable from reading the code alone the way
  everything else in this entry is.
- `allowed_pages_by_role["trial_viewer"]` = Admin, Statistics, Broadcasters,
  BroadcasterDetail, MyProfile — same visual surface as Owner (Section 15),
  no AuditLog (not in scope), no write pages at all.

**Known gap, not fixed in this pass:** the User Access page's "Existing
Users" list reads `users.role`/`users.business_id` directly
(`store.get_users()`), not `memberships`. A test account promoted via
`UPDATE memberships SET role = 'trial_viewer'` will correctly log in and
behave as Trial Viewer, but will still show its old role label in that
list, since only login resolution was ever migrated to read through
`memberships` (Phase 2) — everywhere else in `app.py` that touches
`users.role` directly was out of scope for that migration. Cosmetic only;
doesn't affect actual access control.

**No UI to grant Trial Viewer access yet.** Testing it is one step more
involved than Manager/Auditor, which just needed a `memberships.role`
update on an existing account — Trial Viewer additionally needs
`expires_at` set, and ideally a fresh test account rather than reusing one
that's actively used for other role tests.

**Expected result — two scenarios to test:**
1. **Not-yet-expired grant**: promote a test account with `expires_at` a
   few days in the future. Login should succeed; sidebar shows exactly
   Admin/Statistics/Broadcasters/MyProfile (no Assign, Upload, User Access,
   AuditLog, or anything else); full tenant view on those pages; **no
   download button visible on Statistics**; **no CSV icon visible in any
   dataframe's toolbar anywhere** (the part needing visual confirmation).
2. **Expired grant**: promote a test account with `expires_at` already in
   the past. Login should be **denied** with the same generic "session no
   longer valid" message every other denied login gets.

**How to verify:**
```sql
UPDATE memberships SET role = 'trial_viewer', expires_at = now() + interval '5 days'
WHERE username = '<username>' AND business_id = '<business_id>';
-- test scenario 1, then:
UPDATE memberships SET expires_at = now() - interval '1 day'
WHERE username = '<username>' AND business_id = '<business_id>';
-- test scenario 2 (log out and back in), then revert:
UPDATE memberships SET role = 'sub_agency', expires_at = NULL
WHERE username = '<username>' AND business_id = '<business_id>';
```

**Status:** Implemented, compiled, self-reviewed, pushed to dev (`efc0d01`).

---

## 2026-08-22 — Trial Viewer slice fully verified in dev, including the CSS toolbar fix

**Confirmed by the user:** "tested all running as expected" — both
scenarios passed: a not-yet-expired grant logs in with the correct
restricted page set, full tenant view, no Statistics download button, and
**no dataframe-toolbar CSV icon anywhere** (the one thing in this slice
that genuinely needed visual confirmation rather than being provable from
code alone — confirmed working). An expired grant is denied with the
generic message, same as any other invalid login.

**Status: Trial Viewer slice of Phase 3b — done, verified in dev.** Ready
for prod, same rollout pattern as Agency Manager and Auditor.

---

## 2026-08-22 — Trial Viewer slice: pushed to prod, fully verified there too

**What happened:** Code pushed to `main` (no schema change — `expires_at`
already existed from Phase 2), app rebooted. Same two-scenario test
(valid grant, expired grant) run directly on prod.

**Actual result:** Confirmed by the user — "tested all running as
expected."

**Status: Trial Viewer slice of Phase 3b — done. Live and verified on
both dev and prod.** `main` and `dev` both at commit `d667513`. Three of
Phase 3b's four roles are now done: Agency Manager, Auditor, Trial Viewer.
Remaining: Broadcaster — the biggest lift by far, since broadcasters have
no login accounts at all today; this is closer to a new feature (a
self-service account system) than the role-permission extensions the
other three were.

---

## 2026-08-22 — Phase 3b, fourth slice: Broadcaster (first slice — real database change this time)

**Scoped down deliberately**, agreed with the user before starting: schema
addition + reusing the existing `BroadcasterDetail` page locked to one
`profile_url`, granted via SQL like the other three roles. Deferred: the
actual invite/signup flow, and plan-based dashboard-access gating
(Section 04 — not built until Phase 4 anyway).

**This one needs a real migration**, unlike Auditor/Trial Viewer -
`memberships` gained a genuinely new column.

**What was done:**
- `memberships.profile_url` (nullable) - `sub_agency` scopes a Recruiter to
  a whole named roster; a Broadcaster needs a narrower scope (exactly one
  broadcaster), so it gets its own column rather than overloading
  `sub_agency` with a second meaning depending on role.
- `current_user_context()`'s return value grew from a 3-tuple to a
  4-tuple (added `profile_url`) - the single call site was updated to
  unpack 4 values. Every return statement in the function (6 of them,
  including 2 in the fallback path) updated to match. `profile_url` is
  only ever populated for `role == 'broadcaster'`; every other role gets
  `None` in that slot, same as `sub_agency` already worked.
- `allowed_pages_by_role["broadcaster"]` = `BroadcasterDetail`, `MyProfile`
  only - no dashboard, no roster, nothing else.
- On login, `selected_profile_url` is auto-set to the broadcaster's own
  `profile_url` (not `None`, the way every other role starts) - they never
  pick a broadcaster, they land directly on their own.
- **`BroadcasterDetail` reused rather than a new page built from scratch**
  - it already renders exactly the per-broadcaster history view Section 03
  asks for. Added: a broadcaster-appropriate message if `profile_url` is
  somehow missing (instead of pointing them at a "Broadcasters list" page
  they have no access to); a defense-in-depth check that blocks viewing
  any `profile_url` other than their own even if session state were ever
  manipulated; hid "Agency revenue" (the agency's own commission cut, not
  the broadcaster's own performance) and the "Assignment history" section
  (exposes internal staff usernames - agency operations, not broadcaster
  data) specifically for this role; hid the "Back to broadcasters" button
  (they have no Broadcasters page to go back to).
- **Caught and fixed a real bug before testing, not after this time**: the
  sidebar's structure is `if can_view_full_tenant: ... elif is_sub_agency:
  ... else: [platform-admin-only content]`. Broadcaster would have fallen
  into that bare `else:` branch - literally labeled "PLATFORM CONTROL" -
  with no navigation and **no sign-out button at all**. Added a dedicated
  `elif is_broadcaster:` branch with a proper workspace card, a nav link
  back to their own performance view, My Profile, and sign-out.

**Expected result:** A test account promoted to `broadcaster` with a real
`profile_url` set should log in and land directly on that broadcaster's
own performance page - diamonds/streaming history charts, no agency
revenue figure, no assignment history, no "back to broadcasters" button.
Sidebar shows exactly "My Performance" and "My Profile," with a working
sign-out. Cannot reach any other page - the Admin dashboard, Broadcasters
list, everything else redirects away.

**How to verify (needs the migration run first, then a real profile_url
from the test data):**
```sql
-- find a real profile_url to test with:
SELECT DISTINCT profile_url, broadcaster_name FROM raw_uploads
WHERE business_id = '<business_id>' LIMIT 5;

-- promote a test account:
UPDATE memberships SET role = 'broadcaster', profile_url = '<a profile_url from above>'
WHERE username = '<username>' AND business_id = '<business_id>';

-- revert when done:
UPDATE memberships SET role = 'sub_agency', profile_url = NULL
WHERE username = '<username>' AND business_id = '<business_id>';
```

**Status:** Implemented, compiled, self-reviewed, pushed to dev (`cad95b3`).

---

## 2026-08-22 — Broadcaster (first slice) fully verified in dev

**Confirmed by the user:** "tested as expected" — lands directly on own
performance page, no Agency revenue or Assignment history shown, sidebar
shows exactly My Performance/My Profile with a working sign-out (the bug
caught and fixed before testing this time).

**Status: Broadcaster's first slice of Phase 3b — done, verified in
dev.** Ready for prod, same rollout pattern as the other three roles —
this one needs the migration run there too (real schema change, unlike
Auditor/Trial Viewer).

---

## 2026-08-22 — Broadcaster's first slice: pushed to prod, fully verified there too — no credential-sync repeat

**What happened:** Migration run against prod using the correct admin
connection (`postgres.qppoydbfbtuzchtggeue`) — succeeded cleanly this
time, no repeat of the Supabase pooler credential-sync issue from earlier
today. Confirms that was a one-off, not a recurring pattern. Code pushed
to `main`, app rebooted, same promote → verify → revert cycle run
directly on prod.

**Actual result:** Confirmed by the user — "Test results are as
expected."

**Status: Phase 3b — all four roles now live and verified on both dev
and prod.** `main` and `dev` both at commit `44a54b1`.

**Summary of everything shipped in Phase 3b today:**
- **Agency Manager** — full working role, everything Owner sees except
  billing/plan and 4 specific write actions.
- **Auditor** — read-only, full-tenant view, plus a new standalone Audit
  Log page.
- **Trial Viewer** — read-only, zero export (including Streamlit's own
  dataframe-toolbar download icon), time-boxed via `expires_at`.
- **Broadcaster (first slice)** — own-performance-only view, reusing the
  existing BroadcasterDetail page, scoped to one `profile_url`.

**What's deliberately still open, not forgotten:**
- Broadcaster's actual invite/signup flow (SQL-only grant for now, same as
  Trial Viewer and Auditor).
- Plan-based dashboard-access gating for Broadcaster (Section 04) — Phase
  4 work, entitlements don't exist yet.
- A Super Admin "grant trial access" screen for Trial Viewer (Section 15)
  — still SQL-only.
- The cosmetic User Access role-label gap noted in the Auditor slice
  entry — `users.role` vs `memberships.role` display inconsistency,
  doesn't affect actual access control.
- The rest of Phase 3's original scope: `has_permission()` and the
  `roles`/`permissions`/`role_permissions` tables from 3a are still
  unused by any of this — everything in Phase 3b was built with direct
  boolean role checks (`is_owner`, `is_manager`, etc.), consistent with
  the existing codebase style, not the permission-table lookup. Wiring
  the two together is future cleanup, not required for correctness today.

---

## 2026-08-22 — Phase 4a: Plans & entitlements — schema, seed, resolver

**Scope agreed with the user**: 4a today (schema + seed + `has_feature()`
resolver, safe/additive, zero behavior change — same profile as Phase 3a).
Wiring individual features to real UI gates (4b) is its own follow-on
pass, same as each Phase 3b role was.

**Design decision worth restating**: `has_feature()` resolves **live**,
every call — checks `entitlements` for a manual override first, falls
through to the tenant's current `subscriptions.plan_code` looked up
against `plan_features` if none exists. `entitlements` is deliberately
NOT a synced snapshot of every tenant's full entitlement set — it only
ever holds rows for tenants with an actual override. This is what makes
Phase 4's own acceptance criterion ("changing a tenant's plan in the DB
alone changes what they can do — no code deploy required") true by
construction: there's no resync step to remember, because there's nothing
to resync.

**What was done:**
- `plans` — 5-row catalog (Essential, Growth, Scale, Network, Pioneer),
  seeded with the exact pricing from Section 04: ₹3,999/9,999/24,999/59,999
  monthly (₹39,990/99,990/249,990/599,990 annual — "2 months free"), and
  Pioneer at ₹99,999 one-time-annual only (`billing_mode = 'one_time_annual'`,
  `price_monthly = NULL`).
- `plan_features` — one row per (plan, feature), 12 feature keys × 5 plans
  = 60 rows, mirroring Section 04's comparison table exactly:
  `broadcaster_limit`, `internal_user_limit`, `recruiter_logins`,
  `broadcaster_dashboard_access`, `upload_frequency`,
  `historical_data_months`, `automated_reports`, `ai_features`,
  `white_label_access`, `exports`, `support_level`, `agency_workspaces`.
  Numeric "unlimited" values use `-1` as a sentinel, not `NULL` or a large
  number, so a consumer can always safely parse an int. Pioneer's row set
  is a literal duplicate of Growth's (Section 04: "Pioneer isn't a new
  capability tier, it's Growth sold under different billing terms").
- `entitlements` — override-only table, schema ready, zero rows expected
  in normal operation.
- `store.py`: `get_plans()`, `get_plan_features()`, `get_tenant_plan_code()`
  (defaults to `'essential'` — the most restrictive tier — for any
  business with no `subscriptions` row at all, which is every existing
  business today; fails toward restriction, not toward free features),
  `has_feature()`, `get_entitlement_overrides()`,
  `set_entitlement_override()`, `clear_entitlement_override()`.
- Extended the grant script, `verify_database_role.py`'s `TABLES`, and
  `smoke_test_runtime_database.py` to cover all three new tables, same as
  every previous table addition.

**Expected result once migrated:** `plans` has 5 rows, `plan_features` has
60 rows, `entitlements` has 0 rows. Nothing in the running app changes —
`app.py` doesn't call `has_feature()` anywhere yet.

**How to verify:**
```sql
SELECT
  (SELECT COUNT(*) FROM plans) AS plans_count,
  (SELECT COUNT(*) FROM plan_features) AS plan_features_count,
  (SELECT COUNT(*) FROM entitlements) AS entitlements_count;
```
Expected: `5, 60, 0`.

**Status:** Implemented, compiled, self-reviewed, pushed to dev (`d0df672`).

---

## 2026-08-22 — Phase 4a fully verified in dev

**Actual result:** `plans_count 5, plan_features_count 60,
entitlements_count 0` — exact match to expected.

**Status: Phase 4a — done, verified in dev.** Ready for prod, same
rollout pattern as every prior schema-only slice.

---

## 2026-08-22 — Phase 4a fully verified on prod too

**Actual result:** `plans_count 5, plan_features_count 60,
entitlements_count 0` — exact match, same as dev.

**Status: Phase 4a — done. Live and verified on both dev and prod.**
`main` and `dev` both at commit `c5c9704`. `plans`, `plan_features`,
`entitlements`, and `has_feature()` all exist and are correct on both
environments; nothing in the running app reads any of it yet.

**Next up: Phase 4b — wiring real features to `has_feature()`.** Natural
first candidates, each its own testable slice like Phase 3b's roles were:
`broadcaster_dashboard_access` (gates the Statistics page), `exports`
(extends the `can_export`/download-button work from Trial Viewer),
`ai_features`, `upload_frequency`, `broadcaster_limit`. Not started.

---

## 2026-08-22 — Phase 4b, first slice: `ai_features` gates the Admin dashboard's AI-derived sections

**No schema change** — `has_feature()` already existed from 4a. Pure
`app.py` work.

**What was done:**
- `load_ai_features_enabled(business_id)` — cached (`ttl=30`, matching the
  rest of the app's loader pattern), calls `store.has_feature(business_id,
  'ai_features')`, treats anything other than `'off'`/`None` as enabled
  (the specific basic/advanced/custom tier distinction is future scope,
  not this slice).
- Gated the Overview panel's two AI-derived cards (broadcaster health
  score ring, retention warning) — replaced with a one-line upgrade
  message when off.
- Gated the **entire "Insights" tab** — its panel boundary was already
  clean and self-contained (retention/at-risk insight cards, the at-risk
  expander, the rule-based "Monthly management summary," the follow-up
  task list) — replaced with a single upgrade message when off, rather
  than gating each piece separately.
- **Deliberately scoped to the Admin dashboard only** — Statistics page's
  and the Recruiter (SubAgencies) dashboard's own health-score/retention
  displays are NOT touched in this slice; they're a separate concern
  (Statistics is also meant to be plan-gated via
  `broadcaster_dashboard_access`, a different not-yet-done slice) and
  mixing the two risked scope creep.

**Important thing to know before testing**: no business has a
`subscriptions` row yet (Phase 4a didn't backfill one), and
`get_tenant_plan_code()` defaults to `'essential'` when none exists.
**This means every existing business will show `ai_enabled = False`
immediately on deploy** — the Admin dashboard should show the upgrade
messages right away, without needing to change anything first. To see the
"on" state, a `subscriptions` row needs to exist with a plan other than
`essential`.

**Expected result:**
1. **Immediately after deploy, any existing test business**: Overview
   panel shows an upgrade message instead of the health score/retention
   cards; Insights tab shows one upgrade message instead of its whole
   usual content.
2. **After giving a test business a non-essential plan** (see below): the
   real health score, retention alert, and full Insights tab content all
   reappear exactly as they looked before this slice.

**How to verify:**
```sql
-- confirm the "off" state first (should already be true for any business):
-- log in, check the Admin dashboard shows the upgrade messages.

-- then give one test business a plan that has AI on:
INSERT INTO subscriptions (business_id, plan_code, billing_cycle, status, auto_renew)
VALUES ('<business_id>', 'growth', 'annual', 'active', false)
ON CONFLICT (business_id) DO UPDATE SET plan_code = 'growth';
-- log back in (or just reload after the 30s cache expires) - AI sections should reappear.

-- revert when done:
UPDATE subscriptions SET plan_code = 'essential' WHERE business_id = '<business_id>';
-- or: DELETE FROM subscriptions WHERE business_id = '<business_id>';
```

**Status:** Implemented, compiled, self-reviewed. Pushed to `dev` at commit
`5e7fc9b`. Tested on dev by the user 2026-08-22: confirmed the "off" state
first (existing test business "NorthStar Talent Network," no
`subscriptions` row, showed the upgrade message correctly in the Insights
tab and Overview panel — initial confusion during testing turned out to
just be the user looking at the expected off-state screen, not a bug),
then confirmed the "on" state after inserting a `subscriptions` row with
`plan_code='growth'` — health score ring, retention warning, and full
Insights tab content all reappeared as expected. Result: **tested as
expected.** Pushed to `main` at commit `81518b3` (fast-forward from
`74d0271`), tested on prod 2026-08-22: **tested as expected.** Test
`subscriptions` row deleted afterward to return the test business to
baseline. **Live and verified on both dev and prod.**

---

## Phase 4b, second slice: `broadcaster_dashboard_access` gating the Statistics page

**No schema change** — `has_feature()` already existed from 4a. Pure
`app.py` work, same shape as the `ai_features` slice.

**What was done:**
- `load_broadcaster_dashboard_access(business_id)` — cached (`ttl=30`),
  calls `store.has_feature(business_id, 'broadcaster_dashboard_access')`.
  Section 04's tiers are `off` (Essential) / `readonly` (Growth, Pioneer)
  / `full` (Scale) / `full_custom` (Network). This slice only
  distinguishes `off` vs not-`off` — the readonly/full/full_custom
  distinction (presumably extra filtering/export/customization
  capabilities within the page) is future scope, not this slice, same
  reasoning as the ai_features basic/advanced/custom deferral.
- Gated the **entire Statistics ("Broadcaster Dashboard") page** — the
  hero header still renders (title/context stays visible), but everything
  below it (the section tabs, KPIs, retention panel, performance charts,
  directory/export) is replaced with a single upgrade message and
  `st.stop()` when the tenant's tier resolves to `off`.
- **Left the sidebar's "Broadcaster Dashboard" nav link visible** whether
  or not the feature is off, consistent with how the Insights tab stayed
  visible in the ai_features slice — clicking through shows the upgrade
  message rather than the link disappearing. Keeps this slice's diff
  small and avoids touching `nav_button`/`allowed_pages_by_role` at all.
- **Existing role gate at the top of the page (`can_view_full_tenant`)
  left untouched** — this is a plan gate layered on top of, not instead
  of, the existing role gate. Sub-Agency and Broadcaster still can't
  reach this page at all, regardless of plan.

**Important thing to know before testing**: same as the ai_features
slice — no business has a `subscriptions` row yet, so every existing
business defaults to `essential`/`off`. **Every existing test business
should show the upgrade message immediately on deploy**, not the
dashboard content.

**Expected result:**
1. **Immediately after deploy, any existing test business** (Owner,
   Agency Manager, or Auditor login): the Statistics page's hero shows,
   but everything below it is replaced by the upgrade message.
2. **After giving a test business a non-essential plan**: the full
   Overview/Performance/Retention/Directory content reappears exactly as
   it looked before this slice, including CSV export (still separately
   gated by `can_export`, unrelated to this slice).

**How to verify:**
```sql
-- confirm the "off" state first (should already be true for any business):
-- log in as Owner/Manager/Auditor, open Broadcaster Dashboard, confirm the upgrade message.

-- then give one test business a plan with dashboard access on:
INSERT INTO subscriptions (business_id, plan_code, billing_cycle, status, auto_renew)
VALUES ('<business_id>', 'growth', 'annual', 'active', false)
ON CONFLICT (business_id) DO UPDATE SET plan_code = 'growth';
-- reload after the 30s cache expires - the full dashboard should reappear.

-- revert when done:
DELETE FROM subscriptions WHERE business_id = '<business_id>';
```

**Status:** Implemented, compiled, self-reviewed. Not yet pushed to dev.
