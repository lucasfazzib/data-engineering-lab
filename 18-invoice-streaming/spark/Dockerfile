FROM spark:4.1.3-scala2.13-java17-python3-ubuntu

USER root
RUN pip install --no-cache-dir pymongo==4.18.3 jupyterlab==4.5.11

# Bake the Kafka connector (and its dependencies) into Spark's classpath at build time:
# no --packages downloads when the stream starts, works offline.
RUN echo "" > /tmp/noop.py \
    && /opt/spark/bin/spark-submit --conf spark.jars.ivy=/tmp/ivy \
       --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.3 /tmp/noop.py \
    && cp /tmp/ivy/jars/*.jar /opt/spark/jars/ \
    && rm -rf /tmp/ivy /tmp/noop.py

# Named volume for checkpoints: created from this directory, so it is writable by the spark user
RUN mkdir -p /checkpoints && chown spark:spark /checkpoints

ENV HOME=/tmp
USER spark
