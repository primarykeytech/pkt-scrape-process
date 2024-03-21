from pyspark.sql import SparkSession
import pyspark.sql.functions as f
from pyspark.ml.feature import Tokenizer
from pyspark.ml.feature import StopWordsRemover
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

    df.select("description").show(5, False)

    df.withColumn('word', f.explode(f.split(f.col('description'), ' '))) \
        .groupBy('word') \
        .count() \
        .sort('count', ascending=False) \
        .show()

    # words = df.select("description").split(" "))
    # Count the words
    # word_counts = words.flatMap(lambda x: x).groupBy("value").count()
    # Print the word counts
    # word_counts.show()
    # df.show()
    # print(df.count())

    # To remove stop words (like "I", "The", ...), we need to provide arrays of words,
    # not strings. Here we use Apache Spark Tokenizer to do so.
    # We create a new column to push our arrays of words
    tokenizer = Tokenizer(inputCol="description", outputCol="words_token")
    tokenized = tokenizer.transform(df).select('uuid', 'words_token')

    print('############ Tokenized data extract:')
    tokenized.show()

    stop_words = cfg.STOP_WORDS
    stop_words.extend(StopWordsRemover().getStopWords())
    stop_words = list(set(stop_words))

    # Once in arrays, we can use the Apache Spark function StopWordsRemover
    # A new column "words_clean" is here as an output
    remover = StopWordsRemover(inputCol='words_token', outputCol='words_clean', stopWords=stop_words)
    data_clean = remover.transform(tokenized).select('uuid', 'words_clean')

    print('############ Data Cleaning extract:')
    data_clean.show()

    # Final step : like in the beginning, we can group again words and sort them by the most used
    result = data_clean.withColumn('word', f.explode(f.col('words_clean'))) \
        .groupBy('word') \
        .count().sort('count', ascending=False) \

    print('############ Top 20 most used words are:')
    result.show()

    # Stop Spark Process
    spark.stop()


if __name__ == '__main__':
    main()
