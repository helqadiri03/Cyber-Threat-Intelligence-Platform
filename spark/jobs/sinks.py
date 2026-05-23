"""Write micro-batch results to MongoDB, Cassandra, and Redis."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient, UpdateOne
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

LOG = logging.getLogger(__name__)

SEVERITY_BY_ATTACK: dict[str, int] = {
    "Botnet": 85,
    "BruteForce": 75,
    "DoS/DDoS": 95,
    "Heartbleed": 90,
    "Infiltration": 88,
    "Normal": 5,
    "Recon": 60,
    "WebAttack": 70,
    "Unknown": 50,
}


def compute_risk_score(confidence: float, attack_type: str) -> float:
    """Compute risk score from a probability confidence in [0, 1].

    Formula: risk = (confidence * 100) * 0.6 + severity_weight * 0.4
    This keeps risk in [0, 100] and rewards both high confidence and
    inherently dangerous attack types.
    """
    severity = SEVERITY_BY_ATTACK.get(attack_type, 50)
    return round(min(100.0, confidence * 100.0 * 0.6 + severity * 0.4), 2)


def write_cassandra_events(df: DataFrame, keyspace: str) -> None:
    """Write raw network telemetry to Cassandra.

    ARCHITECTURE NOTE:
    Only raw network flow fields are stored here.
    AI outputs (predicted_attack, confidence, model_name) are written
    to MongoDB by write_mongo_predictions() — not here.
    """
    (
        df.select(
            F.col("sensor_id").alias("sensor_id"),
            F.col("event_time").alias("event_time"),
            F.col("source_ip").alias("source_ip"),
            F.col("Destination Port").cast("int").alias("destination_port"),
            F.col("Flow Duration").cast("long").alias("flow_duration"),
            F.col("Label").alias("label"),
            F.lit(None).cast("map<string,string>").alias("metadata"),
        )
        .write.format("org.apache.spark.sql.cassandra")
        .mode("append")
        .options(table="attack_events", keyspace=keyspace)
        .save()
    )


def write_mongo_predictions(
    rows: list[dict[str, Any]],
    mongo_uri: str,
    database: str,
) -> None:
    if not rows:
        return

    client = MongoClient(mongo_uri)
    db = client[database]
    now = datetime.now(timezone.utc)

    prediction_docs = []
    profile_ops: list[UpdateOne] = []

    for row in rows:
        attack = row["predicted_attack"]
        confidence = float(row.get("confidence") or 0.0)
        risk = compute_risk_score(confidence, attack)
        created = now

        event_fields = {
            k: row[k]
            for k in row.keys()
            if k
            not in {
                "predicted_attack",
                "confidence",
                "risk_score",
                "model_name",
                "sensor_id",
                "event_time",
                "source_ip",
            }
        }

        prediction_docs.append(
            {
                "source_ip": row["source_ip"],
                "predicted_attack": attack,
                # Stored as probability in [0, 1] — ML-standard representation.
                # Use risk_score for human-readable 0-100 severity.
                "confidence": confidence,
                "risk_score": risk,
                "prediction_latency_ms": row.get("prediction_latency_ms"),
                "model_name": row.get("model_name"),
                "actual_label": row.get("Label"),
                "sensor_id": row.get("sensor_id"),
                "event": event_fields,
                "created_at": created,
            }
        )

        profile_ops.append(
            UpdateOne(
                {"source_ip": row["source_ip"]},
                {
                    "$inc": {"event_count": 1, f"attack_counts.{attack}": 1},
                    "$set": {
                        "last_seen": created,
                        "latest_attack": attack,
                        "risk_score": risk,
                        "sensor_id": row.get("sensor_id"),
                    },
                    "$max": {"peak_risk_score": risk},
                },
                upsert=True,
            )
        )

    db.predictions.insert_many(prediction_docs, ordered=False)
    if profile_ops:
        db.attacker_profiles.bulk_write(profile_ops, ordered=False)
    client.close()
    LOG.info("MongoDB wrote %s predictions + %s profile upserts", len(prediction_docs), len(profile_ops))


def publish_redis_alerts(
    rows: list[dict[str, Any]],
    redis_url: str,
    *,
    risk_threshold: float,
    alerts_channel: str,
    alert_ttl_seconds: int = 3600,
) -> None:
    """Publish minimal hot-alert data to Redis pub/sub and store with TTL.

    ARCHITECTURE NOTE:
    Redis is an in-memory ephemeral store — keep alert payloads small.
    Full intelligence documents (confidence, model metadata, raw event fields)
    are stored in MongoDB. Redis stores only what the real-time dashboard needs:
      - attack_type, source_ip, risk_score, timestamp
    TTL ensures alerts expire automatically (default: 1 hour).
    """
    import redis

    if not rows:
        return

    client = redis.from_url(redis_url, decode_responses=True)
    pipe = client.pipeline()
    alert_count = 0

    for row in rows:
        attack = row["predicted_attack"]
        confidence = float(row.get("confidence") or 0.0)
        risk = compute_risk_score(confidence, attack)
        if risk < risk_threshold:
            continue

        ts_ms = int(time.time() * 1000)

        # Minimal payload — only what the real-time dashboard needs.
        # Full details are in MongoDB; Redis is the hot-path notification layer.
        alert = {
            "attack_type":  attack,
            "source_ip":    row["source_ip"],
            "risk_score":   risk,
            "sensor_id":    row.get("sensor_id"),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }

        # Store with TTL — alerts are ephemeral real-time data
        pipe.set(f"alert:{ts_ms}", json.dumps(alert), ex=alert_ttl_seconds)
        pipe.incr(f"counter:attack_type:{attack}")
        pipe.publish(alerts_channel, json.dumps(alert))
        alert_count += 1

    if alert_count:
        pipe.execute()
    client.close()
    LOG.info(
        "Redis published %s high-risk alerts (threshold=%s, ttl=%ss)",
        alert_count, risk_threshold, alert_ttl_seconds,
    )
