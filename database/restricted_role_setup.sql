-- TangoOps restricted runtime role setup.
-- Run once in the Supabase SQL Editor as the database administrator.
-- Replace the password placeholder before the FIRST run only — see the note
-- on CREATE ROLE below. Never commit the real value.
--
-- Safe to re-run in full any time RUNTIME_TABLES in store.py gains a new
-- table, so tangoops_app is never missing a grant on a table the app
-- actually queries. 22 Aug 2026: the CREATE ROLE step below is now
-- conditional specifically so the whole file can be re-run without erroring
-- on "role already exists" once the role has been created once.
-- 21 Aug 2026: added 'memberships' (was missed when that table was first
-- added) and 'subscriptions'. 22 Aug 2026: added 'roles', 'permissions',
-- 'role_permissions' (Phase 3, schema/seed only), then 'plans',
-- 'plan_features', 'entitlements' (Phase 4a, schema/seed only), then
-- 'billing_events' (Phase 6, first slice).
--
-- 22 Aug 2026 (Phase 8, Step 2): real per-tenant row-level security for
-- tangoops_app, not just the anon/authenticated block store.py's SCHEMA
-- already handled. Tables are split into two policy groups below:
--   - Tenant-scoped tables get a real predicate checking two session GUCs
--     (app.current_business_id / app.bypass_tenant_scope) that store.py's
--     _set_tenant_scope()/_reset_tenant_scope() set on every call (Step 1,
--     already live). A call that sets neither gets zero rows - fails
--     closed, not open.
--   - businesses/subscriptions/users (business_id-as-own-PK, or read via
--     a fetch-all-then-filter-in-pandas pattern in app.py) and the global
--     catalogs (roles/permissions/role_permissions/plans/plan_features/
--     profiles) keep the old permissive policy - deliberately deferred,
--     see PHASE_LOG.md, not an oversight.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tangoops_app') THEN
        CREATE ROLE tangoops_app
        WITH
            LOGIN
            PASSWORD 'REPLACE_WITH_YOUR_NEW_PASSWORD'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            NOBYPASSRLS
            CONNECTION LIMIT 10;
    END IF;
END $$;

GRANT CONNECT ON DATABASE postgres TO tangoops_app;
GRANT USAGE ON SCHEMA public TO tangoops_app;
REVOKE CREATE ON SCHEMA public FROM tangoops_app;

-- Tenant-scoped tables: real isolation.
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'memberships', 'entitlements', 'agencies', 'raw_uploads', 'assignments',
        'assignment_log', 'archived_periods', 'security_audit',
        'broadcaster_payout_rules', 'broadcaster_payout_status', 'billing_events'
    ] LOOP
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO tangoops_app',
            table_name
        );
        EXECUTE format(
            'DROP POLICY IF EXISTS tangoops_app_runtime ON public.%I',
            table_name
        );
        EXECUTE format(
            $ddl$CREATE POLICY tangoops_app_runtime ON public.%I
            FOR ALL TO tangoops_app
            USING (business_id::text = current_setting('app.current_business_id', true)
                   OR current_setting('app.bypass_tenant_scope', true) = 'true')
            WITH CHECK (business_id::text = current_setting('app.current_business_id', true)
                        OR current_setting('app.bypass_tenant_scope', true) = 'true')$ddl$,
            table_name
        );
    END LOOP;
END $$;

-- Deferred tables: no per-tenant restriction for tangoops_app yet
-- (business_id-as-own-PK / fetch-all-then-filter tables, or global
-- catalogs with no business_id column at all - see the note above).
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'businesses', 'users', 'subscriptions', 'roles', 'permissions',
        'role_permissions', 'plans', 'plan_features', 'profiles'
    ] LOOP
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO tangoops_app',
            table_name
        );
        EXECUTE format(
            'DROP POLICY IF EXISTS tangoops_app_runtime ON public.%I',
            table_name
        );
        EXECUTE format(
            'CREATE POLICY tangoops_app_runtime ON public.%I '
            'FOR ALL TO tangoops_app USING (true) WITH CHECK (true)',
            table_name
        );
    END LOOP;
END $$;

GRANT USAGE, SELECT ON SEQUENCE public.raw_uploads_id_seq TO tangoops_app;
GRANT USAGE, SELECT ON SEQUENCE public.assignment_log_id_seq TO tangoops_app;
GRANT USAGE, SELECT ON SEQUENCE public.security_audit_id_seq TO tangoops_app;
GRANT USAGE, SELECT ON SEQUENCE public.billing_events_id_seq TO tangoops_app;

SELECT
    rolname, rolsuper, rolcreatedb, rolcreaterole,
    rolreplication, rolbypassrls, rolconnlimit
FROM pg_roles
WHERE rolname = 'tangoops_app';
