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


def list_top_words(number_to_include=30):
    """
    Creates a list of lists with the top words in order. Two elements: word and count.
    :return: list with most used words.
    """
    # Initialize spark.
    spark = init_spark()

    # Read the csv file into a pandas dataframe.
    df = spark.read.csv(cfg.EXPORT_FILE, header=True, escape="\"")

    # Select just the description column and show just five rows.
    df.select("description").show(5, False)

    # Split the description column into words.
    df.withColumn('word', f.explode(f.split(f.col('description'), ' '))) \
        .groupBy('word') \
        .count() \
        .sort('count', ascending=False) \

    # Create arrays of words so that we can remove the stop words.
    # Use Apache Spark Tokenizer to do so.
    tokenizer = Tokenizer(inputCol="description", outputCol="words_token")
    tokenized = tokenizer.transform(df).select('uuid', 'words_token')

    # set the stop words using the array in the cfg file along with the
    # standard stop words in the StopWordsRemover class.
    stop_words = cfg.STOP_WORDS
    stop_words.extend(StopWordsRemover().getStopWords())
    stop_words = list(set(stop_words))

    # Remove the stop words.
    remover = StopWordsRemover(inputCol='words_token', outputCol='words_clean', stopWords=stop_words)
    data_clean = remover.transform(tokenized).select('uuid', 'words_clean')

    # Sort the words by count.
    result = data_clean.withColumn('word', f.explode(f.col('words_clean'))) \
        .groupBy('word') \
        .count().sort('count', ascending=False)

    print('Top used words are:')
    result.show(number_to_include, False)

    # list_result = result.collect()
    list_return = []

    # Retrieving multiple rows using collect() and for loop
    for row in result.collect()[:number_to_include]:
        row_return = [(row["word"]), row["count"]]
        list_return.append(row_return)

    # stop spark process.
    spark.stop()

    # return the list.
    return list_return


def build_word_string(top_words):
    """
    Builds a string of the top words based on a list of the top
    words and their counts.
    :param top_words: list of lists with the top words and counts.
    :return: str of the top words repeated the number of times based on the count.
    """
    # list to hold the words repeated.
    list_process = []

    # loop through the list and add the word the number
    # of times based on the count.
    for row in top_words:

        # loop based on a range of the count.
        for x in range(row[1]):

            # add the list.
            list_process.append(row[0])

    # create a string from the list.
    word_string = " ".join(list_process)

    # return the string.
    return word_string


def main():

    # get the top words.
    top_words = list_top_words(30)

    # build the string.
    word_string = build_word_string(top_words)

    # create the word cloud.


if __name__ == '__main__':
    main()
