from pyspark.sql import SparkSession
import os

import cfg


def init_spark():
    """
    Initialize the spark session.
    :return: SparkSession
    """
    return (SparkSession.builder
            .appName("pkt-scrape-process")
            .config("spark.memory.offHeap.enabled", "true")
            .config("spark.memory.offHeap.size", "10g").getOrCreate())


def main():
    spark = init_spark()
    df = spark.read.csv(cfg.EXPORT_FILE, header=True, escape="\"")
    df.show()
    print(df.count())


if __name__ == '__main__':
    main()
