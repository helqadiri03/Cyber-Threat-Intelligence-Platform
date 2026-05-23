"""
Phase 5 — Spark Structured Streaming: Kafka → inference → MongoDB / Cassandra / Redis.
"""

from __future__ import annotations

import logging
import os
import sys

from pyspark.ml.functions import vector_to_array
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# Allow `python streaming_inference.py` from /opt/spark-jobs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_loader import ModelBundle, load_models
from schema import EVENT_SCHEMA
from sinks import (
    SEVERITY_BY_ATTACK,
    compute_risk_score,
    publish_redis_alerts,
    write_cassandra_events,
    write_mongo_predictions,
)

LOG = logging.getLogger("streaming_inference")


def build_spark(app_name: str) -> SparkSession:
    master = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
    checkpoint = os.getenv("SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoint/cyber_events")

    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.sql.streaming.checkpointLocation", checkpoint)
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "8"))
        .config("spark.cassandra.connection.host", os.getenv("CASSANDRA_HOSTS", "cassandra"))
        .config("spark.cassandra.connection.port", os.getenv("CASSANDRA_PORT", "9042"))
        .config("spark.sql.catalogImplementation", "in-memory")
    )

    jars = os.getenv("SPARK_JARS_PACKAGES")
    if jars:
        builder = builder.config("spark.jars.packages", jars)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(os.getenv("SPARK_LOG_LEVEL", "WARN"))
    return spark


def read_kafka_stream(spark: SparkSession) -> DataFrame:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    topic = os.getenv("KAFKA_TOPIC", "cyber_events_raw")
    starting = os.getenv("KAFKA_STARTING_OFFSETS", "earliest")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", starting)
        .option("failOnDataLoss", "false")
        .load()
    )

    default_sensor = os.getenv("DEFAULT_SENSOR_ID", "sensor-01")
    parsed = (
        raw.select(
            F.col("key").cast("string").alias("kafka_key"),
            F.col("timestamp").alias("kafka_timestamp"),
            F.from_json(F.col("value").cast("string"), EVENT_SCHEMA).alias("data"),
        )
        .select("kafka_key", "kafka_timestamp", "data.*")
        .withColumn("sensor_id", F.lit(default_sensor))
        .withColumn("event_time", F.coalesce(F.col("kafka_timestamp"), F.current_timestamp()))
        .withColumn(
            "source_ip",
            F.concat(
                F.lit("10.0."),
                ((F.col("Destination Port") % F.lit(250)) + F.lit(1)).cast("string"),
                F.lit(".1"),
            ),
        )
    )
    return parsed


def run_inference(df: DataFrame, models: ModelBundle, label_map_bc) -> DataFrame:
    featured = models.feature_pipeline.transform(df)
    predicted = models.classifier.transform(featured)

    @F.udf(StringType())
    def decode_label(idx):
        return label_map_bc.value.get(float(idx), "Unknown")

    # Store confidence as a probability in [0, 1] — mathematically correct for ML scores.
    # risk_score is derived as: confidence * 100 * 0.6 + severity_weight * 0.4
    confidence_col = F.round(
        F.array_max(vector_to_array(F.col("probability"))), 6
    )

    result = (
        predicted.withColumn("predicted_attack", decode_label(F.col("prediction")))
        .withColumn("confidence", confidence_col)
        .withColumn("model_name", F.lit(models.classifier_name))
    )

    severity_expr = F.lit(50)
    for attack, severity in SEVERITY_BY_ATTACK.items():
        severity_expr = F.when(
            F.col("predicted_attack") == attack, F.lit(severity)
        ).otherwise(severity_expr)

    # risk_score: normalise confidence to 0-100 scale first
    result = result.withColumn(
        "risk_score",
        F.round(F.col("confidence") * F.lit(100.0) * F.lit(0.6) + severity_expr * F.lit(0.4), 2),
    )
    return result


def create_batch_processor(spark: SparkSession, models: ModelBundle):
    label_map_bc = spark.sparkContext.broadcast(models.label_map)
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://admin:changeme@mongodb:27017/?authSource=admin")
    mongo_db = os.getenv("MONGODB_DATABASE", "cyber_intelligence")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cassandra_ks = os.getenv("CASSANDRA_KEYSPACE", "cyber_threats")
    risk_threshold = float(os.getenv("RISK_ALERT_THRESHOLD", "80"))
    alerts_channel = os.getenv("REDIS_ALERTS_CHANNEL", "channel:alerts")
    # Alerts are ephemeral — expire after 1 hour by default (configurable)
    alert_ttl_seconds = int(os.getenv("REDIS_ALERT_TTL_SECONDS", "3600"))

    def process_batch(batch_df: DataFrame, epoch_id: int) -> None:
        import time as _time
        if batch_df.rdd.isEmpty():
            LOG.info("[epoch=%s] empty batch", epoch_id)
            return

        n = batch_df.count()
        LOG.info("[epoch=%s] processing %s events", epoch_id, n)

        # Track inference latency in milliseconds
        _t0 = _time.monotonic()
        enriched = run_inference(batch_df, models, label_map_bc)
        skip_cols = {
            "features",
            "features_selected",
            "features_raw_sel",
            "rawPrediction",
            "probability",
        }
        output_cols = [c for c in enriched.columns if c not in skip_cols]
        flat_rows = [row.asDict() for row in enriched.select(*output_cols).collect()]
        _latency_ms = round((_time.monotonic() - _t0) * 1000)
        # Attach per-batch latency to every row
        for row in flat_rows:
            row["prediction_latency_ms"] = _latency_ms

        try:
            write_cassandra_events(enriched, cassandra_ks)
            LOG.info("[epoch=%s] Cassandra write complete", epoch_id)
        except Exception as exc:
            LOG.exception("[epoch=%s] Cassandra write failed: %s", epoch_id, exc)

        try:
            write_mongo_predictions(flat_rows, mongo_uri, mongo_db)
            LOG.info("[epoch=%s] MongoDB write complete", epoch_id)
        except Exception as exc:
            LOG.exception("[epoch=%s] MongoDB write failed: %s", epoch_id, exc)

        try:
            publish_redis_alerts(
                flat_rows,
                redis_url,
                risk_threshold=risk_threshold,
                alerts_channel=alerts_channel,
                alert_ttl_seconds=alert_ttl_seconds,
            )
            LOG.info("[epoch=%s] Redis alerts complete", epoch_id)
        except Exception as exc:
            LOG.exception("[epoch=%s] Redis publish failed: %s", epoch_id, exc)

        high_risk = sum(
            1
            for r in flat_rows
            if compute_risk_score(float(r.get("confidence") or 0), r.get("predicted_attack", ""))
            >= risk_threshold
        )
        LOG.info("[epoch=%s] done — high_risk=%s/%s", epoch_id, high_risk, n)

    return process_batch


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    feature_path = os.getenv(
        "MODEL_FEATURE_PIPELINE", "/models/preprocessing/feature_pipeline"
    )
    xgb_path = os.getenv(
        "MODEL_XGB_CLASSIFIER", "/models/classifiers/xgboost_intrusion_detector"
    )
    rf_path = os.getenv(
        "MODEL_RF_CLASSIFIER", "/models/classifiers/random_forest_fallback"
    )
    label_path = os.getenv(
        "MODEL_LABEL_INDEXER", "/models/label_decoder/string_indexer"
    )

    spark = build_spark("cyber-threats-streaming-inference")
    models = load_models(feature_path, xgb_path, rf_path, label_path)
    LOG.info("Active classifier: %s", models.classifier_name)

    stream_df = read_kafka_stream(spark)
    query = (
        stream_df.writeStream.foreachBatch(create_batch_processor(spark, models))
        .outputMode("append")
        .option(
            "checkpointLocation",
            os.getenv("SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoint/cyber_events"),
        )
        .trigger(processingTime=os.getenv("STREAM_TRIGGER_INTERVAL", "10 seconds"))
        .start()
    )

    LOG.info("Streaming query started (topic=%s)", os.getenv("KAFKA_TOPIC", "cyber_events_raw"))
    query.awaitTermination()


if __name__ == "__main__":
    main()
