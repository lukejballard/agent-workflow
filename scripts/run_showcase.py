#!/usr/bin/env python3
"""Showcase runner — populates the dashboard with many diverse pipelines.

Generates runs across several distinct pipeline names, versions, and
topologies (linear, fan-out, fan-in, diamond) so the UI has rich data
to display.

Prerequisites
-------------
Start the collector first::

    uvicorn pipeline_observe.collector.server:app --host 127.0.0.1 --port 4318

Then::

    python scripts/run_showcase.py

Options
-------
  --collector-url URL   Collector ingest URL (default: http://localhost:4318/ingest)
  --runs N              Number of runs per pipeline (default: 2)
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from pipeline_observe.sdk.api import observe_step, pipeline_run  # noqa: E402

# ---------------------------------------------------------------------------
# Pipeline 1 — ETL: linear (ingest → clean → enrich → load)
# ---------------------------------------------------------------------------
PIPELINE_ETL = "etl_orders"


@observe_step("ingest_raw_orders")
def ingest_raw_orders() -> pd.DataFrame:
    n = random.randint(800, 1200)
    print(f"  [ingest_raw_orders] Generating {n} rows")
    return pd.DataFrame(
        {
            "order_id": range(1, n + 1),
            "amount": [round(random.uniform(5, 500), 2) for _ in range(n)],
            "region": [random.choice(["US", "EU", "APAC"]) for _ in range(n)],
            "ts": pd.date_range("2026-01-01", periods=n, freq="h"),
        }
    )


@observe_step("clean_orders")
def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    print(f"  [clean_orders] {len(df)} rows → dropping nulls & negatives")
    df = df[df["amount"] > 0].dropna().copy()
    return df


@observe_step("enrich_orders")
def enrich_orders(df: pd.DataFrame) -> pd.DataFrame:
    print("  [enrich_orders] Adding currency conversion")
    rates = {"US": 1.0, "EU": 1.08, "APAC": 0.75}
    df["amount_usd"] = df.apply(
        lambda r: round(r["amount"] * rates.get(r["region"], 1.0), 2), axis=1
    )
    return df


@observe_step("load_warehouse")
def load_warehouse(df: pd.DataFrame) -> None:
    print(f"  [load_warehouse] Writing {len(df)} rows to warehouse (simulated)")
    time.sleep(random.uniform(0.05, 0.2))


def run_etl(version: str) -> None:
    os.environ["PIPELINE_NAME"] = PIPELINE_ETL
    with pipeline_run(pipeline_version=version):
        raw = ingest_raw_orders()
        cleaned = clean_orders(raw)
        enriched = enrich_orders(cleaned)
        load_warehouse(enriched)


# ---------------------------------------------------------------------------
# Pipeline 2 — ML training: fan-out (load data → [train_xgb, train_lr] → evaluate)
# ---------------------------------------------------------------------------
PIPELINE_ML = "ml_training"


@observe_step("load_training_data")
def load_training_data() -> pd.DataFrame:
    n = random.randint(500, 1000)
    print(f"  [load_training_data] {n} samples")
    return pd.DataFrame(
        {
            "feature_a": [random.gauss(0, 1) for _ in range(n)],
            "feature_b": [random.gauss(5, 2) for _ in range(n)],
            "label": [random.choice([0, 1]) for _ in range(n)],
        }
    )


@observe_step("train_xgboost")
def train_xgboost(df: pd.DataFrame) -> dict:
    print(f"  [train_xgboost] Training on {len(df)} samples …")
    time.sleep(random.uniform(0.1, 0.3))
    return {"model": "xgboost", "accuracy": round(random.uniform(0.85, 0.95), 4)}


@observe_step("train_logistic_regression")
def train_logistic_regression(df: pd.DataFrame) -> dict:
    print(f"  [train_logistic_regression] Training on {len(df)} samples …")
    time.sleep(random.uniform(0.05, 0.15))
    return {
        "model": "logistic_regression",
        "accuracy": round(random.uniform(0.78, 0.88), 4),
    }


@observe_step("evaluate_models")
def evaluate_models(xgb: dict, lr: dict) -> dict:
    best = xgb if xgb["accuracy"] > lr["accuracy"] else lr
    print(f"  [evaluate_models] Best: {best['model']} ({best['accuracy']})")
    return {"champion": best["model"], "accuracy": best["accuracy"]}


def run_ml(version: str) -> None:
    os.environ["PIPELINE_NAME"] = PIPELINE_ML
    with pipeline_run(pipeline_version=version):
        data = load_training_data()
        # fan-out: two models trained on same data
        xgb_result = train_xgboost(data)
        lr_result = train_logistic_regression(data)
        # fan-in: evaluate both
        evaluate_models(xgb_result, lr_result)


# ---------------------------------------------------------------------------
# Pipeline 3 — Data quality: diamond (source → [validate_schema, validate_stats] → report)
# ---------------------------------------------------------------------------
PIPELINE_DQ = "data_quality_checks"


@observe_step("fetch_source_snapshot")
def fetch_source_snapshot() -> pd.DataFrame:
    n = random.randint(200, 600)
    print(f"  [fetch_source_snapshot] {n} rows")
    return pd.DataFrame(
        {
            "id": range(n),
            "value": [random.uniform(0, 100) for _ in range(n)],
            "category": [random.choice(["A", "B", "C"]) for _ in range(n)],
        }
    )


@observe_step("validate_schema")
def validate_schema(df: pd.DataFrame) -> dict:
    expected = {"id", "value", "category"}
    actual = set(df.columns)
    missing = expected - actual
    extra = actual - expected
    print(f"  [validate_schema] missing={missing}, extra={extra}")
    return {
        "missing_cols": list(missing),
        "extra_cols": list(extra),
        "pass": len(missing) == 0,
    }


@observe_step("validate_statistics")
def validate_statistics(df: pd.DataFrame) -> dict:
    null_pct = df.isnull().mean().max()
    print(f"  [validate_statistics] max null%={null_pct:.2%}")
    return {
        "max_null_pct": round(float(null_pct), 4),
        "row_count": len(df),
        "pass": null_pct < 0.05,
    }


@observe_step("generate_dq_report")
def generate_dq_report(schema_result: dict, stats_result: dict) -> dict:
    overall = schema_result["pass"] and stats_result["pass"]
    print(f"  [generate_dq_report] Overall pass={overall}")
    return {
        "schema": schema_result,
        "statistics": stats_result,
        "overall_pass": overall,
    }


def run_dq(version: str) -> None:
    os.environ["PIPELINE_NAME"] = PIPELINE_DQ
    with pipeline_run(pipeline_version=version):
        snapshot = fetch_source_snapshot()
        # diamond: two branches from same source, then merge
        schema = validate_schema(snapshot)
        stats = validate_statistics(snapshot)
        generate_dq_report(schema, stats)


# ---------------------------------------------------------------------------
# Pipeline 4 — Reporting: linear with many steps (simulate a long pipeline)
# ---------------------------------------------------------------------------
PIPELINE_REPORT = "weekly_report"


@observe_step("query_sales_db")
def query_sales_db() -> pd.DataFrame:
    n = random.randint(1000, 3000)
    print(f"  [query_sales_db] {n} rows")
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-02-01", periods=n, freq="h"),
            "revenue": [round(random.uniform(100, 10000), 2) for _ in range(n)],
            "region": [
                random.choice(["NA", "EMEA", "APAC", "LATAM"]) for _ in range(n)
            ],
        }
    )


@observe_step("compute_kpis")
def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    print(f"  [compute_kpis] aggregating {len(df)} rows")
    return df.groupby("region", as_index=False).agg(
        total_revenue=("revenue", "sum"),
        avg_revenue=("revenue", "mean"),
        count=("revenue", "count"),
    )


@observe_step("format_report")
def format_report(df: pd.DataFrame) -> pd.DataFrame:
    print(f"  [format_report] {len(df)} regions")
    df["total_revenue"] = df["total_revenue"].round(2)
    df["avg_revenue"] = df["avg_revenue"].round(2)
    return df


@observe_step("send_email_report")
def send_email_report(df: pd.DataFrame) -> dict:
    print(f"  [send_email_report] Sending report with {len(df)} rows (simulated)")
    time.sleep(random.uniform(0.05, 0.15))
    return {"sent": True, "recipients": 3}


def run_report(version: str) -> None:
    os.environ["PIPELINE_NAME"] = PIPELINE_REPORT
    with pipeline_run(pipeline_version=version):
        raw = query_sales_db()
        kpis = compute_kpis(raw)
        formatted = format_report(kpis)
        send_email_report(formatted)


# ---------------------------------------------------------------------------
# Pipeline 5 — Failing pipeline (to show error states)
# ---------------------------------------------------------------------------
PIPELINE_INGEST = "event_ingestion"


@observe_step("pull_events")
def pull_events() -> pd.DataFrame:
    n = random.randint(100, 500)
    print(f"  [pull_events] {n} events")
    return pd.DataFrame({"event_id": range(n), "payload": ["data"] * n})


@observe_step("parse_events")
def parse_events(df: pd.DataFrame) -> pd.DataFrame:
    print(f"  [parse_events] Parsing {len(df)} events")
    return df


@observe_step("write_to_lake")
def write_to_lake(df: pd.DataFrame, should_fail: bool = False) -> None:
    if should_fail:
        raise RuntimeError("Simulated write failure: lake storage unavailable")
    print(f"  [write_to_lake] Writing {len(df)} events")


def run_ingest(version: str, should_fail: bool = False) -> None:
    os.environ["PIPELINE_NAME"] = PIPELINE_INGEST
    with pipeline_run(pipeline_version=version):
        events = pull_events()
        parsed = parse_events(events)
        write_to_lake(parsed, should_fail=should_fail)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

VERSIONS = ["1.0.0", "1.1.0", "1.2.0"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Showcase runner for pipeline-observe")
    parser.add_argument("--collector-url", default="http://localhost:4318/ingest")
    parser.add_argument(
        "--runs", type=int, default=2, help="Runs per pipeline per version"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Continuously generate showcase runs for live demos",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=20.0,
        help="Delay between live showcase cycles (default: 20s)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Number of live cycles to run (0 = infinite)",
    )
    args = parser.parse_args()

    os.environ["PIPELINE_OBSERVE_COLLECTOR_URL"] = args.collector_url

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          pipeline-observe  –  Showcase Runner           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Collector : {args.collector_url}")
    print(f"  Runs/ver  : {args.runs}")
    if args.live:
        cycles_label = "infinite" if args.cycles == 0 else str(args.cycles)
        print(
            f"  Live mode : ON  (cycles={cycles_label}, interval={args.interval_seconds:.1f}s)"
        )
    print()

    pipelines = [
        ("ETL Orders (linear)", run_etl),
        ("ML Training (fan-out/fan-in)", run_ml),
        ("Data Quality (diamond)", run_dq),
        ("Weekly Report (linear)", run_report),
    ]

    def _run_cycle(cycle_number: int) -> None:
        print(f"\n=== Showcase cycle {cycle_number} ===")
        for version in VERSIONS:
            for label, runner in pipelines:
                for i in range(args.runs):
                    print(f"[v{version}] {label}  run {i + 1}/{args.runs}")
                    runner(version)
                    time.sleep(0.3)

            # One successful + one failing ingestion per version
            print(f"[v{version}] Event Ingestion (success)")
            run_ingest(version, should_fail=False)
            time.sleep(0.3)

            print(f"[v{version}] Event Ingestion (failure)")
            try:
                run_ingest(version, should_fail=True)
            except RuntimeError:
                print("  (expected failure caught)")
            time.sleep(0.3)

    if not args.live:
        _run_cycle(1)
    else:
        cycle = 1
        while True:
            _run_cycle(cycle)
            if args.cycles > 0 and cycle >= args.cycles:
                break
            print(
                f"\nSleeping for {args.interval_seconds:.1f}s before next live cycle..."
            )
            time.sleep(max(0.0, args.interval_seconds))
            cycle += 1

    print()
    print("=" * 60)
    print("  Showcase complete — open http://localhost:3000")
    print("=" * 60)


if __name__ == "__main__":
    main()
