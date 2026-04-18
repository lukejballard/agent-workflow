# Anomaly Detection Screenshot

This is a placeholder for the **Anomaly Detection** screenshot.

The anomaly detection panel shows:
- Detected anomalies listed by severity (critical / warning / info)
- Step name, metric name (duration_ms / output_row_count), and observed vs expected value
- Timeline chart of the anomalous metric with the threshold band highlighted
- Links back to the affected run for drill-down investigation

## To replace this placeholder

1. Start the full stack: `docker compose up -d`
2. Run the demo pipeline (anomaly mode): `python scripts/run_demo_pipeline.py --anomaly-only`
3. Open `http://localhost:3000` and navigate to **Anomaly Detection**
4. Take a screenshot and save it as `docs/images/anomaly_detection.png`
5. Remove this markdown file
