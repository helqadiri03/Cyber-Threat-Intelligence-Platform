"""Consume messages from stream_holdout topic and print verification stats."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

from confluent_kafka import Consumer, KafkaError, KafkaException


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify stream_holdout Kafka topic")
    parser.add_argument(
        "--bootstrap-servers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("KAFKA_TOPIC", "stream_holdout"),
    )
    parser.add_argument("--max-messages", type=int, default=10, help="Messages to print (0 = count all)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Seconds to wait for messages")
    args = parser.parse_args()

    consumer = Consumer(
        {
            "bootstrap.servers": args.bootstrap_servers,
            "group.id": "stream-holdout-verify",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([args.topic])

    labels: Counter[str] = Counter()
    count = 0
    idle_seconds = 0.0
    limit = args.max_messages if args.max_messages > 0 else 30564

    try:
        while idle_seconds < args.timeout and count < limit:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                idle_seconds += 1.0
                continue

            idle_seconds = 0.0
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            count += 1
            record = json.loads(msg.value().decode("utf-8"))
            labels[record.get("Label", "UNKNOWN")] += 1

            if count <= min(5, limit):
                print(f"\n--- message {count} (partition {msg.partition()}, offset {msg.offset()}) ---")
                print(f"key: {msg.key().decode('utf-8') if msg.key() else None}")
                print(f"Label: {record.get('Label')}")
                print(f"Destination Port: {record.get('Destination Port')}")
                print(f"Flow Duration: {record.get('Flow Duration')}")
    finally:
        consumer.close()

    if count == 0:
        print(f"No messages received on topic '{args.topic}'. Was the producer run?", file=sys.stderr)
        return 1

    print(f"\n=== Verification summary ===")
    print(f"Topic: {args.topic}")
    print(f"Messages consumed: {count}")
    print(f"Label distribution (sampled from consumed messages):")
    for label, n in labels.most_common():
        print(f"  {label}: {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
