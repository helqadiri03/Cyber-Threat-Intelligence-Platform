"""Step 9 — Stream Parquet rows to Kafka topic cyber_events_raw (batched, throttled, loopable)."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq
from confluent_kafka import Producer

LOG = logging.getLogger("cyber_events_producer")


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    return str(obj)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _delivery_factory(stats: dict):
    def _report(err, msg):
        if err is not None:
            stats["errors"] += 1
            LOG.error("Delivery failed: %s", err)
        else:
            stats["delivered"] += 1

    return _report


def iter_row_dicts(data_dir: Path, batch_size: int):
    """Yield (source_file, row_index, payload) using PyArrow batch reads."""
    for parquet_path in sorted(data_dir.glob("*.parquet")):
        parquet_file = pq.ParquetFile(parquet_path)
        row_base = 0
        for batch in parquet_file.iter_batches(batch_size=batch_size):
            frame = batch.to_pandas()
            for offset, row in frame.iterrows():
                yield parquet_path.name, row_base + int(offset), row.to_dict()
            row_base += len(frame)


def check_producer_status() -> str:
    """Poll FastAPI backend system endpoint to check if producer should run or pause."""
    import urllib.request
    import json
    try:
        # Use a short 2.0s timeout to avoid locking the producer thread if backend is rebooting
        url = os.getenv("BACKEND_URL", "http://backend:8000") + "/producer/status"
        with urllib.request.urlopen(url, timeout=2.0) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("status", "running")
    except Exception as exc:
        # Default to running if connection fails so the system doesn't unexpectedly stall
        return "running"


def publish_stream(
    producer: Producer,
    topic: str,
    data_dir: Path,
    *,
    batch_size: int,
    sleep_seconds: float,
    loop: bool,
    max_rows: int,
    stats: dict,
) -> None:
    sent = 0
    loop_id = 0

    while True:
        loop_id += 1
        LOG.info("Starting pass %s over %s", loop_id, data_dir)
        for source_file, row_idx, payload in iter_row_dicts(data_dir, batch_size):
            # Check if producer has been stopped via dashboard
            if sent % 100 == 0:
                is_first_pause_log = True
                while check_producer_status() == "stopped":
                    if is_first_pause_log:
                        LOG.info("=== PRODUCER PAUSED via dashboard action. Standing by... ===")
                        is_first_pause_log = False
                    time.sleep(1.0)
                if not is_first_pause_log:
                    LOG.info("=== PRODUCER RESUMED! Continuing traffic flow. ===")

            if max_rows and sent >= max_rows:
                LOG.info("Reached max_rows=%s, stopping.", max_rows)
                producer.flush()
                return

            key = f"{source_file}-{row_idx}"
            try:
                value = json.dumps(payload, default=_json_default).encode("utf-8")
            except (TypeError, ValueError) as exc:
                stats["errors"] += 1
                LOG.exception("Serialization error at %s:%s — %s", source_file, row_idx, exc)
                continue

            producer.produce(
                topic,
                key=key.encode("utf-8"),
                value=value,
                callback=_delivery_factory(stats),
            )
            sent += 1
            stats["published"] += 1

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            if sent % 500 == 0:
                producer.poll(0)
                elapsed = max(time.time() - stats["started_at"], 0.001)
                rate = sent / elapsed
                LOG.info(
                    "Published %s messages (%.1f msg/s, errors=%s)",
                    sent,
                    rate,
                    stats["errors"],
                )

        producer.flush()
        LOG.info("Finished pass %s — %s messages published so far", loop_id, sent)

        if not loop:
            break

        LOG.info("Loop mode enabled — replaying Parquet from the beginning")


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description="Produce cyber_events_raw from Parquet")
    parser.add_argument("--data-dir", default=os.getenv("STREAM_HOLDOUT_PATH", "/data/stream_holdout"))
    parser.add_argument("--bootstrap-servers", default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"))
    parser.add_argument("--topic", default=os.getenv("KAFKA_TOPIC", "cyber_events_raw"))
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("PRODUCER_BATCH_SIZE", "500")))
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=float(os.getenv("PRODUCER_SLEEP_SECONDS", "0")),
        help="Delay between each published message",
    )
    parser.add_argument("--loop", action="store_true", default=_env_bool("PRODUCER_LOOP", False))
    parser.add_argument("--max-rows", type=int, default=int(os.getenv("PRODUCER_MAX_ROWS", "0")))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        LOG.error("Data directory not found: %s", data_dir)
        return 1

    producer = Producer({"bootstrap.servers": args.bootstrap_servers})
    stats = {"published": 0, "delivered": 0, "errors": 0, "started_at": time.time()}

    LOG.info(
        "Producer config topic=%s batch_size=%s sleep=%.4fs loop=%s max_rows=%s",
        args.topic,
        args.batch_size,
        args.sleep_seconds,
        args.loop,
        args.max_rows or "all",
    )

    try:
        publish_stream(
            producer,
            args.topic,
            data_dir,
            batch_size=args.batch_size,
            sleep_seconds=args.sleep_seconds,
            loop=args.loop,
            max_rows=args.max_rows,
            stats=stats,
        )
    except KeyboardInterrupt:
        LOG.info("Interrupted by user")
    finally:
        producer.flush()

    elapsed = max(time.time() - stats["started_at"], 0.001)
    LOG.info(
        "Done. published=%s delivered=%s errors=%s elapsed=%.1fs rate=%.1f msg/s",
        stats["published"],
        stats["delivered"],
        stats["errors"],
        elapsed,
        stats["published"] / elapsed,
    )
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
