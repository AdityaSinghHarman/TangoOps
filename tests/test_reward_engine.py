"""Tests for the Reward Plan Management System's calculation engine
(utils.py). Covers the engine-level focus areas from the feature's
verification checklist that don't require a live database: highest-tier,
cumulative, and incremental-difference calculation modes; monthly-vs-
lifetime dedup semantics; percentage rewards; cash/coin separation; and the
status state machine.

Effective-dated plan changes, DB-level duplicate prevention (the partial
unique indexes / EXCLUDE constraints), business isolation, and Sub-Agency
access restriction are proven instead by scripts/verify_tenant_isolation.py,
scripts/smoke_test_runtime_database.py, and manual/Supabase-Advisor
verification against the Dev project - they exercise real Postgres behavior
no pure-Python unit test can stand in for.
"""
import pandas as pd

import utils


def _milestone(key, threshold, reward_value, unit="coins", **kw):
    m = {"milestone_key": key, "threshold": threshold, "reward_value": reward_value, "unit": unit}
    m.update(kw)
    return m


STANDARD_TIERS = [
    _milestone("m1", 25000, 1000),
    _milestone("m2", 50000, 2500),
    _milestone("m3", 100000, 6000),
    _milestone("m4", 250000, 15000),
]


# ---------------- tier calculation modes ----------------

def test_highest_only_awards_single_top_tier():
    result = utils.calculate_milestone_reward(60000, STANDARD_TIERS, "highest_only", "monthly_once", set())
    assert [a["milestone_key"] for a in result["awarded"]] == ["m2"]
    assert result["total_coins"] == 2500
    assert result["total_cash"] == 0
    assert result["tier_reached"] == 50000


def test_highest_only_below_first_tier_awards_nothing():
    result = utils.calculate_milestone_reward(10000, STANDARD_TIERS, "highest_only", "monthly_once", set())
    assert result["awarded"] == []
    assert result["tier_reached"] is None


def test_cumulative_sums_every_crossed_tier():
    result = utils.calculate_milestone_reward(120000, STANDARD_TIERS, "cumulative", "lifetime_once", set())
    assert {a["milestone_key"] for a in result["awarded"]} == {"m1", "m2", "m3"}
    assert result["total_coins"] == 1000 + 2500 + 6000
    assert result["tier_reached"] == 100000


def test_cumulative_skips_already_awarded_milestones():
    result = utils.calculate_milestone_reward(120000, STANDARD_TIERS, "cumulative", "lifetime_once", {"m1"})
    assert {a["milestone_key"] for a in result["awarded"]} == {"m2", "m3"}
    assert result["total_coins"] == 2500 + 6000


def test_incremental_difference_awards_only_the_delta_since_last_tier():
    # First evaluation at 60,000 diamonds: nothing awarded yet, so tier 2's
    # full value (2500) is the delta from a previous value of 0.
    first = utils.calculate_milestone_reward(60000, STANDARD_TIERS, "incremental_difference",
                                              "monthly_once", set())
    assert first["total_coins"] == 2500

    # Next period, now at 120,000 diamonds (crossed tier 3): only the
    # difference between tier 3's value (6000) and the highest previously-
    # awarded tier's value (tier 2's 2500) is paid - not the full 6000, and
    # not 2500+6000 like cumulative mode would pay.
    second = utils.calculate_milestone_reward(120000, STANDARD_TIERS, "incremental_difference",
                                               "monthly_once", {"m2"})
    assert second["awarded"][0]["milestone_key"] == "m3"
    assert second["total_coins"] == 6000 - 2500


def test_incremental_difference_pays_nothing_for_the_same_tier_twice():
    result = utils.calculate_milestone_reward(60000, STANDARD_TIERS, "incremental_difference",
                                               "monthly_once", {"m2"})
    assert result["awarded"] == []
    assert result["total_coins"] == 0


# ---------------- monthly vs lifetime dedup ----------------

def test_lifetime_milestone_never_refires_once_already_awarded():
    milestone = {"milestone_key": "signup_bonus", "trigger_type": "signup_completed",
                 "reward_value": 500, "unit": "cash", "frequency": "lifetime_once"}
    result = utils.calculate_recruiter_milestone_reward(
        {"diamonds_redeemed": 0}, milestone,
        manual_event={"status": "Approved"}, already_awarded={"signup_bonus"},
    )
    assert result["eligible"] is False
    assert result["reason"] == "Already awarded."


def test_monthly_repeatable_milestone_can_fire_again():
    milestone = {"milestone_key": "monthly_diamonds", "trigger_type": "diamonds_redeemed_target",
                 "threshold": 10000, "reward_value": 200, "unit": "cash", "frequency": "monthly_once"}
    result = utils.calculate_recruiter_milestone_reward(
        {"diamonds_redeemed": 15000}, milestone, already_awarded=set(),
    )
    assert result["eligible"] is True
    assert result["reward_value"] == 200


def test_manual_repeatable_milestone_ignores_already_awarded():
    milestone = {"milestone_key": "manual_bonus", "trigger_type": "manual_approval",
                 "reward_value": 50, "unit": "cash", "frequency": "manual_repeatable"}
    result = utils.calculate_recruiter_milestone_reward(
        {}, milestone, manual_event={"status": "Approved"}, already_awarded={"manual_bonus"},
    )
    assert result["eligible"] is True


# ---------------- percentage rewards ----------------

def test_percentage_reward_matches_existing_payouts_formula():
    result = utils.calculate_percentage_reward(diamonds_redeemed=40000, agency_pct=15, payout_pct=10)
    assert result["redeemed_value"] == 200.0          # 40000 / 200
    assert result["agency_earnings"] == 30.0           # 200 * 15%
    assert result["broadcaster_reward"] == 20.0        # 200 * 10%
    assert result["net_earnings"] == 10.0
    assert result["eligible"] is True


def test_percentage_reward_below_minimum_diamonds_is_ineligible():
    result = utils.calculate_percentage_reward(diamonds_redeemed=1000, agency_pct=15, payout_pct=10,
                                                min_diamonds=5000)
    assert result["eligible"] is False
    assert result["broadcaster_reward"] == 0.0


def test_percentage_reward_respects_max_monthly_payout_cap():
    result = utils.calculate_percentage_reward(diamonds_redeemed=400000, agency_pct=20, payout_pct=20,
                                                max_monthly_payout=100)
    assert result["broadcaster_reward"] == 100.0
    assert result["net_earnings"] == result["agency_earnings"] - 100.0


# ---------------- cash / coin separation ----------------

def test_mixed_unit_milestones_never_sum_cash_and_coins():
    mixed = [
        _milestone("cash_tier", 10000, 50, unit="cash"),
        _milestone("coin_tier", 20000, 300, unit="coins"),
    ]
    result = utils.calculate_milestone_reward(25000, mixed, "cumulative", "lifetime_once", set())
    assert result["total_cash"] == 50
    assert result["total_coins"] == 300
    assert "total_amount" not in result  # no combined/blended total key exists at all


def test_calculate_fixed_reward_keeps_unit_explicit():
    cash = utils.calculate_fixed_reward(100, "cash")
    coins = utils.calculate_fixed_reward(500, "coins")
    assert cash["unit"] == "cash"
    assert coins["unit"] == "coins"


# ---------------- status state machine ----------------

def test_status_transitions_allow_the_documented_path():
    assert utils.validate_status_transition("Not Eligible", "In Progress")
    assert utils.validate_status_transition("Milestone Reached", "Awaiting Approval")
    assert utils.validate_status_transition("Awaiting Approval", "Approved")
    assert utils.validate_status_transition("Approved", "Paid")


def test_status_transitions_block_paying_before_approval():
    assert utils.validate_status_transition("Awaiting Approval", "Paid") is False
    assert utils.validate_status_transition("Milestone Reached", "Paid") is False


def test_paid_and_cancelled_are_terminal():
    assert utils.validate_status_transition("Paid", "Approved") is False
    assert utils.validate_status_transition("Cancelled", "Approved") is False


# ---------------- CSV-replace flagging ----------------

def test_diff_period_for_reward_flags_detects_changed_diamonds():
    old = pd.DataFrame([{"profile_url": "https://tango.me/a", "diamonds_earned": 100,
                          "diamonds_redeemed": 100, "streaming_days": 5, "streaming_hours": 10}])
    new = pd.DataFrame([{"profile_url": "https://tango.me/a", "diamonds_earned": 100,
                          "diamonds_redeemed": 250, "streaming_days": 5, "streaming_hours": 10}])
    assert utils.diff_period_for_reward_flags(old, new) == ["https://tango.me/a"]


def test_diff_period_for_reward_flags_ignores_unchanged_rows():
    old = pd.DataFrame([{"profile_url": "https://tango.me/a", "diamonds_earned": 100,
                          "diamonds_redeemed": 100, "streaming_days": 5, "streaming_hours": 10}])
    new = old.copy()
    assert utils.diff_period_for_reward_flags(old, new) == []


def test_diff_period_for_reward_flags_flags_removed_profile():
    old = pd.DataFrame([{"profile_url": "https://tango.me/a", "diamonds_earned": 100,
                          "diamonds_redeemed": 100, "streaming_days": 5, "streaming_hours": 10}])
    new = pd.DataFrame(columns=old.columns)
    assert utils.diff_period_for_reward_flags(old, new) == ["https://tango.me/a"]
