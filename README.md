# pkt-scrape-process
There are a number of qualitative research studies that gather experiences from participants for 
evaluation. The purpose of this project is to 
scrape a collection of experiences from a websites (e.g. a thread in a forum related to the use 
of a prescription drug), save the information 
to a NoSQL database, output it from there to a csv file, and then utilize a Spark job to 
count the occurrences of words provided within a list of words. The counts 
are then used to create a word cloud to visualize the data. This is obviously not the flow that 
would be used in real world scenario.

Because of reasons of copyright, this demo project will not provide the website from which 
the test was conducted. Obviously, each website used would need its own code to handle the 
scraping and processing of content.
 
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

## Pre-flight setup:
+ A Selenium-compliant driver added to a "drivers" folder. This project used a Firefox 
driver downloaded from [here](https://github.com/mozilla/geckodriver/releases).
+ A cfg.py file with constants set that are used for configuration and processing. sample_cfg.py 
is provided showing the constant declarations. 

## Steps Completed:
+ Scraping
+ Writing to DynamoDB
+ Reading from DynamoDB
+ Writing to CSV
+ Spark job to count occurrences of words from CSV
+ Word cloud creation

![alt text](https://github.com/primarykeytech/pkt-scrape-process/blob/master/public/omep_wordcloud.png?raw=true)


## TODO:
+ Unit tests
