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
-- 'role_permissions' (Phase 3, schema/seed only).

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

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'businesses', 'users', 'memberships', 'subscriptions', 'roles', 'permissions',
        'role_permissions', 'agencies', 'raw_uploads',
        'assignments', 'assignment_log', 'archived_periods', 'profiles', 'security_audit',
        'broadcaster_payout_rules', 'broadcaster_payout_status'
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

SELECT
    rolname, rolsuper, rolcreatedb, rolcreaterole,
    rolreplication, rolbypassrls, rolconnlimit
FROM pg_roles
WHERE rolname = 'tangoops_app';
