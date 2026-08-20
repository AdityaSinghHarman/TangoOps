-- StreamOperiq broadcaster payout tracking.
-- Apply with an administrator connection before deploying the matching app code.

CREATE TABLE IF NOT EXISTS public.broadcaster_payout_rules (
    business_id TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    broadcaster_name TEXT,
    effective_from TEXT NOT NULL,
    agency_rate_pct NUMERIC(5,2) NOT NULL,
    payout_rate_pct NUMERIC(5,2) NOT NULL,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, profile_url, effective_from),
    CONSTRAINT broadcaster_payout_rules_period_format
        CHECK (effective_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT broadcaster_payout_rules_agency_rate
        CHECK (agency_rate_pct BETWEEN 0 AND 20),
    CONSTRAINT broadcaster_payout_rules_payout_rate
        CHECK (payout_rate_pct BETWEEN 0 AND agency_rate_pct)
);

CREATE INDEX IF NOT EXISTS idx_payout_rules_effective
    ON public.broadcaster_payout_rules (business_id, profile_url, effective_from DESC);

CREATE TABLE IF NOT EXISTS public.broadcaster_payout_status (
    business_id TEXT NOT NULL,
    period TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    paid_at TIMESTAMP,
    paid_by TEXT,
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, period, profile_url),
    CONSTRAINT broadcaster_payout_status_period_format
        CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT broadcaster_payout_status_value
        CHECK (status IN ('Pending', 'Paid'))
);

CREATE INDEX IF NOT EXISTS idx_payout_status_period
    ON public.broadcaster_payout_status (business_id, period, status);

ALTER TABLE public.broadcaster_payout_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.broadcaster_payout_status ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.broadcaster_payout_rules FROM anon, authenticated;
REVOKE ALL ON TABLE public.broadcaster_payout_status FROM anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.broadcaster_payout_rules TO tangoops_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.broadcaster_payout_status TO tangoops_app;

DROP POLICY IF EXISTS tangoops_app_runtime ON public.broadcaster_payout_rules;
CREATE POLICY tangoops_app_runtime ON public.broadcaster_payout_rules
    FOR ALL TO tangoops_app USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS tangoops_app_runtime ON public.broadcaster_payout_status;
CREATE POLICY tangoops_app_runtime ON public.broadcaster_payout_status
    FOR ALL TO tangoops_app USING (true) WITH CHECK (true);
