FROM apache/spark:3.5.1

USER root

ENV PYTHONUNBUFFERED=1 \
    SPARK_HOME=/opt/spark \
    PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3 \
    PYTHONDONTWRITEBYTECODE=1 \
    IVY_HOME=/opt/ivy2

# Pre-fetch all connector JARs during build so container startup is instant.
# spark-submit --packages downloads to IVY_HOME which we bake into the image.
ENV SPARK_JARS_PACKAGES="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.4.0"

RUN /opt/spark/bin/spark-submit \
      --packages "${SPARK_JARS_PACKAGES}" \
      --conf spark.ivy.home=/opt/ivy2 \
      --class org.apache.spark.deploy.SparkSubmit \
      --conf spark.sql.catalogImplementation=in-memory \
      /opt/spark/examples/jars/spark-examples_2.12-3.5.1.jar 1 2>/dev/null || true

# Upgrade pip then install Python deps — prefer binary wheels to avoid compilation
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt

WORKDIR /opt/spark-jobs

COPY jobs /opt/spark-jobs
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /opt/spark/checkpoint /models

# Default CMD — overridden per service in docker-compose.yml
CMD ["/bin/bash"]
