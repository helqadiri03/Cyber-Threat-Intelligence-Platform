#!/usr/bin/env bash
set -euo pipefail

PACKAGES="${SPARK_JARS_PACKAGES:-org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0}"

MASTER="${SPARK_MASTER_URL:-spark://spark-master:7077}"

echo "Submitting Spark streaming job to ${MASTER}"

exec /opt/spark/bin/spark-submit \
  --master "${MASTER}" \
  --deploy-mode client \
  --packages "${PACKAGES}" \
  --conf spark.ivy.home=/opt/ivy2 \
  --conf spark.cassandra.connection.host="${CASSANDRA_HOSTS:-cassandra}" \
  --conf spark.cassandra.connection.port="${CASSANDRA_PORT:-9042}" \
  --conf spark.sql.streaming.checkpointLocation="${SPARK_CHECKPOINT_DIR:-/opt/spark/checkpoint/cyber_events}" \
  --conf spark.driver.memory="${SPARK_DRIVER_MEMORY:-2g}" \
  --conf spark.executor.memory="${SPARK_EXECUTOR_MEMORY:-2g}" \
  /opt/spark-jobs/streaming_inference.py
