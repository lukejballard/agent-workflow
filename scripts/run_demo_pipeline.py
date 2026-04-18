#!/usr/bin/env python3
"""Demo pipeline runner script for pipeline-observe.

This script automates the full demo experience in a single command:

1. Generates the synthetic sales dataset (10,000 rows) if it does not exist.
2. Runs the demo pipeline once normally (baseline run).
3. Runs the pipeline a second time with intentional anomalies:
      - step-duration spike  (3-second artificial sleep in transform_sales)
      - row-count drop       (95 % of rows removed before aggregate_metrics)

The anomaly detector will flag the second run automatically.

Prerequisites
-------------
Start the collector service before running this script::

    uvicorn pipeline_observe.collector.server:app --host 127.0.0.1 --port 4318

Then in a separate terminal::

    python scripts/run_demo_pipeline.py

Or, if using Docker Compose::

    docker compose -f docker-compose.demo.yml up -d
    python scripts/run_demo_pipeline.py \\
        --collector-url http://localhost:4318/ingest

Options
-------
  --collector-url URL   Collector ingest URL
                        (default: http://localhost:4318/ingest)
  --input CSV           Path to the input sales CSV.
                        (default: examples/demo_pipeline/demo_sales.csv)
  --output CSV          Path to write the output report CSV.
                        (default: examples/demo_pipeline/demo_report.csv)
  --skip-generate       Skip dataset generation (use existing CSV).
  --baseline-only       Only run the baseline pipeline (skip anomaly run).
  --anomaly-only        Only run the anomaly-injected pipeline.

Usage
-----
    # Full demo (generate data + baseline run + anomaly run)
    python scripts/run_demo_pipeline.py

    # Skip dataset generation (CSV already exists)
    python scripts/run_demo_pipeline.py --skip-generate

    # Only trigger anomalies
    python scripts/run_demo_pipeline.py --anomaly-only
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the repository root is on sys.path so imports work when the script
# is run from any working directory.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Imports (after path setup)
# ---------------------------------------------------------------------------
from examples.demo_pipeline.generate_data import (  # noqa: E402
    DEFAULT_ROWS,
    generate_rows,
    write_csv,
)
from examples.demo_pipeline.pipeline import run as run_pipeline  # noqa: E402

_DEFAULT_INPUT = str(_REPO_ROOT / "examples" / "demo_pipeline" / "demo_sales.csv")
_DEFAULT_OUTPUT = str(_REPO_ROOT / "examples" / "demo_pipeline" / "demo_report.csv")
_DEFAULT_COLLECTOR = "http://localhost:4318/ingest"


def _separator(title: str) -> None:
    width = 60
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def _generate_dataset(input_csv: str, rows: int = DEFAULT_ROWS) -> None:
    """Generate the synthetic sales CSV if it does not already exist."""
    csv_path = Path(input_csv)
    if csv_path.exists():
        print(f"Dataset already exists: {csv_path}  (use --skip-generate to reuse it)")
        return
    print(f"Generating {rows:,} synthetic sales rows …")
    data = generate_rows(rows)
    write_csv(data, str(csv_path))
    print(f"Dataset written to: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the pipeline-observe demo pipeline (with optional anomalies).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--collector-url",
        default=_DEFAULT_COLLECTOR,
        help=f"Collector ingest URL (default: {_DEFAULT_COLLECTOR})",
    )
    parser.add_argument(
        "--input",
        default=_DEFAULT_INPUT,
        help=f"Input sales CSV path (default: {_DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        default=_DEFAULT_OUTPUT,
        help=f"Output report CSV path (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip dataset generation and use the existing CSV.",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Only run the baseline pipeline (no anomaly injection).",
    )
    parser.add_argument(
        "--anomaly-only",
        action="store_true",
        help="Only run the anomaly-injected pipeline.",
    )
    args = parser.parse_args()

    # Set the collector URL via environment variable (picked up by the SDK)
    os.environ["PIPELINE_OBSERVE_COLLECTOR_URL"] = args.collector_url

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           pipeline-observe  –  Demo Runner               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Collector URL : {args.collector_url}")
    print(f"  Input CSV     : {args.input}")
    print(f"  Output CSV    : {args.output}")

    # ------------------------------------------------------------------
    # Step 0 – generate synthetic dataset
    # ------------------------------------------------------------------
    if not args.skip_generate:
        _separator("Step 0: Generate Synthetic Dataset")
        _generate_dataset(args.input)

    # ------------------------------------------------------------------
    # Step 1 – baseline run (no anomalies)
    # ------------------------------------------------------------------
    if not args.anomaly_only:
        _separator("Step 1: Baseline Pipeline Run (no anomalies)")
        print("This run establishes a healthy baseline for the anomaly detector.")
        run_pipeline(input_csv=args.input, output_csv=args.output, inject_anomaly=False)

    # ------------------------------------------------------------------
    # Short pause between runs so the dashboard shows two distinct entries
    # ------------------------------------------------------------------
    if not args.baseline_only and not args.anomaly_only:
        print()
        print("Waiting 2 seconds before anomaly run …")
        time.sleep(2)

    # ------------------------------------------------------------------
    # Step 2 – anomaly run (intentional degradation)
    # ------------------------------------------------------------------
    if not args.baseline_only:
        _separator("Step 2: Anomaly-Injected Pipeline Run")
        print("Anomalies injected:")
        print("  • 3-second sleep in transform_sales  → duration spike")
        print("  • 95 % row drop before aggregate_metrics → row-count drop")
        print()
        run_pipeline(input_csv=args.input, output_csv=args.output, inject_anomaly=True)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    _separator("Demo Complete")
    print("Open the dashboard to explore the runs:")
    print("  http://localhost:3000")
    print()
    print("Useful API queries:")
    print("  curl http://localhost:4318/runs")
    print("  curl http://localhost:4318/anomalies")
    print()


if __name__ == "__main__":
    main()
