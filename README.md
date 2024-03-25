# pkt-scrape-process
There are a number of qualitative research studies that gather experiences from participants for 
evaluation. The purpose of this project is to 
scrape a collection of experiences from a websites (e.g. a thread in a forum related to the use 
of a prescription drug), save the information 
to a NoSQL database, output it from there to a csv file, and then utilize a Spark job to 
count the occurrences of words provided within a list of words. The counts 
are then used to create a word cloud to visualize the data. This is obviously not the flow that 
would be used in real world scenario.

Each step is intentionally run individually to show the processes of scraping, saving, reading, 
and processing the data. 

Because of reasons of copyright, this demo project will not provide the website from which 
the test was conducted. Obviously, each website used would need its own code to handle the 
scraping and processing of content.

![word cloud sample](https://github.com/primarykeytech/pkt-scrape-process/blob/master/public/omep_wordcloud.png?raw=true)

 
## This demo project uses:
+ Python 3.12
+ Amazon AWS DynamoDB (NoSQL database)
+ Apache Spark

## Python libraries used:
+ Beautiful Soup 4
+ Selenium (the test website had blocked the use of web scraping libraries)
+ boto3 (Amazon AWS SDK for Python)
+ PySpark
+ pandas
+ matplotlib
+ wordcloud
+ pytest

## Pre-flight setup:
+ A Selenium-compliant driver added to a "drivers" folder. This project used a Firefox 
driver downloaded from [here](https://github.com/mozilla/geckodriver/releases).
+ A cfg.py file with constants set that are used for configuration and processing. sample_cfg.py 
is provided showing the constant declarations. 
+ Install packages `pip install -r requirements.txt`

## Steps Completed:
+ Scraping
+ Writing to DynamoDB
+ Reading from DynamoDB
+ Writing to CSV
+ Spark job to count occurrences of words from CSV
+ Word cloud creation

## TODO:
+ Unit tests
+ Get Moto working for DynamoDB mocking - not currently working.

## Running the project:

### Scraping the website:

This step will scrape the website specified in the cfg.py file and save the data 
to DynamoDB.  
`python pktscrape/scrape.py`

### Export from DynamoDB to CSV:

This step will read the data from DynamoDB and save all data in the table 
specified in the cfg file to a CSV file so that it can be processed by Spark.  
`python export/csv_maker.py`

### Running the Spark job:

Once the CSV file is generated, the Spark job can be run to count the occurrences 
of each word in the description column of the CSV file and use that information to 
generate a word cloud. The console will show the counts of each word. A string is 
then generated based on these counts with each word repeated the number of times 
based on the count. This string is then used to generate the word cloud image. The 
word cloud image is displayed by matplotlib.  
`python process/job.py`

### Running Tests:

The unit tests are being refined and improved.
`pytest`
