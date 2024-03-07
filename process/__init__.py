from pyspark.sql import SparkSession


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
    spark, sc = init_spark()
    nums = sc.parallelize([1, 2, 3, 4])
    print(nums.map(lambda x: x * x).collect())


if __name__ == '__main__':
    main()
