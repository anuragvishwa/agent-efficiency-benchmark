# Architecture

```mermaid
flowchart TD
  A["Terminal-Bench / SWE-agent datasets"] --> B["Raw Parquet + source metadata"]
  B --> C["Normalized runs and steps"]
  C --> D["Step signals"]
  D --> E["Run signals"]
  E --> F["Rule-based RCA"]
  F --> G["DuckDB benchmark tables"]
  G --> H["JSON/CSV reports"]
  H --> I["Streamlit dashboard"]
```

The OSS pipeline is file-backed and local. It reads raw Parquet, writes
dataset-specific normalized Parquet, materializes benchmark tables in separate
DuckDB files, and exports stable public artifacts for downstream display.
