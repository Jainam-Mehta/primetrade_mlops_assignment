# primetrade_mlops_assignment

# MLOps Batch Signal Processing Pipeline

A deterministic, production ready pipeline that ingests historical cryptocurrency data streams, computes rolling means based on YAML configurations, and exports standardized performance telemetry matrices.

## Core Architecture Features
- **Determinism:** Random seeds locked across numpy environments (`seed: 42`).
- **Robust Exception Handling:** Automated system fault capture producing structured error JSON telemetry under all failure conditions.
- **Observability:** Generates detailed data splitting diagnostics inside `run.log`.

## Local Execution Instructions
Ensure your local environment modules are fully configured, then execute via terminal:
```bash
pip install -r requirements.txt
python run.py --input data.csv.csv --config config.yaml --output metrics.json --log-file run.log
```

## Docker Container Build and Execution Instructions
To evaluate this pipeline inside an isolated slim container layer, execute these explicit commands:
```bash
docker build -t mlops-task .
docker run --rm mlops-task
```

## Example Telemetry Output Schema (`metrics.json`)
```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4991,
  "latency_ms": 42,
  "seed": 42,
  "status": "success"
}
```
