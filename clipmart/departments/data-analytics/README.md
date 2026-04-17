# Data Analytics Department as a Service

> Replace a data engineering team with AI agents that build pipelines, manage warehouses, and deliver metric reports — automatically.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Data Engineer ($160k) | $160,000/yr | $49/mo floor |
| Data Analyst ($120k) | $120,000/yr | $8/deliverable |
| dbt Cloud + Airflow | $18,000/yr | Included |
| **Total replaced** | **$298,000/yr** | **~$2,400/yr** |

## What This Department Does

1. **Pipeline Management** — Build, test, run, and monitor ETL/ELT pipelines
2. **Data Warehouse** — Schema design, table management, access control
3. **Data Quality** — Automated DQ checks, anomaly detection, freshness monitoring
4. **Metric Catalog** — Canonical metric definitions, lineage documentation
5. **Analytics Reports** — Daily/weekly/monthly metric dashboards for all departments

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Data pipeline built + tested | $30 |
| Daily pipeline run | $5 |
| Data quality audit | $20 |
| Metric dashboard setup | $25 |
| Full warehouse refresh | $15 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong data-pipeline          # Pipeline management
mekong data-daily-pipeline    # Run daily ETL
mekong data-ingest            # Data ingestion
mekong data-transform         # Data transformation
mekong data-warehouse         # Warehouse operations
mekong data-quality           # DQ checks
mekong data-query             # Ad-hoc queries
mekong data-metric            # Metric definitions
mekong data-catalog           # Data catalog management
mekong data-full-refresh      # Full warehouse refresh
mekong data-reverse-etl       # Reverse ETL (warehouse → CRM)
mekong data-access            # Access control management
```

## Install

```bash
mekong install dept-data-analytics
```

## Configuration

```bash
# .mekong/.env.dept-data-analytics
DEPT_DATA_WAREHOUSE=postgres  # postgres|bigquery|snowflake
DEPT_DATA_DB_URL=postgres://user:pass@host:5432/db
DEPT_DATA_ORCHESTRATOR=local  # local|airflow|prefect
DEPT_DATA_BI_TOOL=metabase  # metabase|looker|superset
DEPT_DATA_DAILY_PIPELINE_SCHEDULE=0 6 * * *  # cron: 6am UTC daily
```
