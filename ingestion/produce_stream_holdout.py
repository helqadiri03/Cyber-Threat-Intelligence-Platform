"""Read stream_holdout Parquet files and publish each row to Kafka as JSON."""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from confluent_kafka import Producer


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    return str(obj)


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce stream_holdout rows to Kafka")
    parser.add_argument(
        "--data-dir",
        default=os.getenv("STREAM_HOLDOUT_PATH", "/data/stream_holdout"),
        help="Directory containing part-*.parquet files",
    )
    parser.add_argument(
        "--bootstrap-servers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("KAFKA_TOPIC", "stream_holdout"),
    )
    parser.add_argument("--max-rows", type=int, default=0, help="Limit rows (0 = all)")
    parser.add_argument("--batch-flush", type=int, default=500, help="Flush every N messages")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    parquet_files = sorted(data_dir.glob("*.parquet"))
    if not parquet_files:
        print(f"No parquet files in {data_dir}", file=sys.stderr)
        return 1

    producer = Producer({"bootstrap.servers": args.bootstrap_servers})
    sent = 0
    started = time.time()

    for parquet_path in parquet_files:
        df = pd.read_parquet(parquet_path)
        for row_idx, row in df.iterrows():
            if args.max_rows and sent >= args.max_rows:
                break

            payload = row.to_dict()
            key = f"{parquet_path.stem}-{row_idx}"
            producer.produce(
                args.topic,
                key=key.encode("utf-8"),
                value=json.dumps(payload, default=_json_default).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
            if sent % args.batch_flush == 0:
                producer.poll(0)
                producer.flush()

        if args.max_rows and sent >= args.max_rows:
            break

    producer.flush()
    elapsed = time.time() - started
    print(
        f"Produced {sent} messages to topic '{args.topic}' "
        f"from {len(parquet_files)} parquet file(s) in {elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
