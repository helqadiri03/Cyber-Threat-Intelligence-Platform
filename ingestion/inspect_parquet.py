"""Step 7 — Inspect stream_holdout Parquet and emit schema contract for producer/Spark."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


CRITICAL_FIELDS = ["Label", "Destination Port", "Flow Duration"]


def load_selected_features(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("rb") as fh:
        features = pickle.load(fh)
    if not isinstance(features, list):
        raise ValueError(f"Expected list in {path}, got {type(features)}")
    return [str(f) for f in features]


def inspect_dataset(data_dir: Path, selected_features_path: Path) -> dict:
    parquet_files = sorted(data_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files in {data_dir}")

    selected_features = load_selected_features(selected_features_path)
    pipeline_features = selected_features  # same list used by VectorAssembler in feature_pipeline

    import pyarrow as pa

    combined = pa.concat_tables([pq.read_table(p) for p in parquet_files])

    columns = combined.column_names
    schema_fields = {name: str(combined.schema.field(name).type) for name in columns}
    row_count = combined.num_rows

    nulls_total: dict[str, int] = {}
    nulls_critical: dict[str, int] = {}
    for name in columns:
        col = combined.column(name)
        null_count = col.null_count
        nulls_total[name] = null_count
        if name in CRITICAL_FIELDS:
            nulls_critical[name] = null_count

    parquet_cols = set(columns)
    missing_selected = [f for f in selected_features if f not in parquet_cols]
    extra_vs_selected = sorted(parquet_cols - set(selected_features) - {"Label"})

    contract = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(data_dir),
        "parquet_files": len(parquet_files),
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "dtypes": schema_fields,
        "null_counts": nulls_total,
        "critical_field_nulls": nulls_critical,
        "label_values": sorted(
            {str(v) for v in combined.column("Label").to_pylist() if v is not None}
        )
        if "Label" in parquet_cols
        else [],
        "selected_features": selected_features,
        "selected_feature_count": len(selected_features),
        "missing_selected_features": missing_selected,
        "non_feature_columns": extra_vs_selected,
        "contract_ok": len(missing_selected) == 0 and all(nulls_critical.get(f, 0) == 0 for f in CRITICAL_FIELDS if f in parquet_cols),
        "kafka_message_format": {
            "encoding": "json",
            "topic": os.getenv("KAFKA_TOPIC", "cyber_events_raw"),
            "required_fields": CRITICAL_FIELDS,
            "note": "Each Kafka message is one Parquet row as a JSON object with original column names.",
        },
    }
    return contract


def write_markdown(contract: dict, out_path: Path) -> None:
    lines = [
        "# Parquet → Kafka Schema Contract",
        "",
        f"_Generated: {contract['generated_at']}_",
        "",
        "## Dataset summary",
        "",
        f"| Property | Value |",
        f"|----------|-------|",
        f"| Source | `{contract['source']}` |",
        f"| Parquet files | {contract['parquet_files']} |",
        f"| Rows | {contract['row_count']:,} |",
        f"| Columns | {contract['column_count']} |",
        f"| Contract valid | **{contract['contract_ok']}** |",
        "",
        "## Critical fields (must be non-null)",
        "",
    ]
    for field in CRITICAL_FIELDS:
        nulls = contract["critical_field_nulls"].get(field, "N/A")
        lines.append(f"- `{field}` — nulls: **{nulls}**")

    lines.extend(
        [
            "",
            "## Label distribution (unique values)",
            "",
            ", ".join(f"`{v}`" for v in contract["label_values"]),
            "",
            "## Selected features check",
            "",
            f"- Expected (model): **{contract['selected_feature_count']}** features",
            f"- Missing in Parquet: {contract['missing_selected_features'] or '_none_'}",
            "",
            "## Column names & types",
            "",
            "```json",
            json.dumps(contract["dtypes"], indent=2),
            "```",
            "",
            "## Kafka contract",
            "",
            f"- Topic: `{contract['kafka_message_format']['topic']}`",
            "- Encoding: JSON (one row per message)",
            "- Producer and Spark consumer **must** preserve column names exactly.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect stream_holdout Parquet schema")
    parser.add_argument(
        "--data-dir",
        default=os.getenv("STREAM_HOLDOUT_PATH", "/data/stream_holdout"),
    )
    parser.add_argument(
        "--selected-features",
        default=os.getenv("SELECTED_FEATURES_PATH", "/app/models/selected_features.pkl"),
    )
    parser.add_argument(
        "--output-json",
        default="/app/ingestion/schema_contract.json",
    )
    parser.add_argument(
        "--output-md",
        default="/app/docs/PARQUET_SCHEMA.md",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    try:
        contract = inspect_dataset(data_dir, Path(args.selected_features))
    except Exception as exc:
        print(f"Inspection failed: {exc}", file=sys.stderr)
        return 1

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(contract, out_md)

    print(json.dumps(
        {
            "rows": contract["row_count"],
            "columns": contract["column_count"],
            "contract_ok": contract["contract_ok"],
            "missing_selected_features": contract["missing_selected_features"],
            "critical_nulls": contract["critical_field_nulls"],
            "labels": contract["label_values"],
            "json": str(out_json),
            "markdown": str(out_md),
        },
        indent=2,
    ))
    return 0 if contract["contract_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
