# pkt-scrape-process
There are a number of qualitative research studies that gather experiences from participants for 
evaluation. The purpose of this project is to 
scrape a collection of experiences from a websites (e.g. a thread in a forum related to the use 
of a prescription drug), save the information 
to a NoSQL database, output it from there to a parquet file, and then utilize Amazon AWS 
Elastic MapReduce to count the occurrences of words provided within a list of words. The counts 
are then used to create a word cloud to visualize the data. This is obviously not the flow that 
would be used in real world scenario.

Because of reasons of copyright, this demo project will not provide the website from which 
the test was conducted. Obviously, each website used would need its own code to handle the 
scraping and processing of content.
 
This demo project uses:
+ Python 3.7
+ Amazon AWS DynamoDB
+ Apache Spark on Amazon AWS Elastic MapReduce (EMR)

Python libraries used:
+ Beautiful Soup 4.4
+ Selenium (the test website had blocked the use of vanilla web scraping libraries)
+ boto3 (Amazon AWS SDK for Python)
+ PySpark

You will need:
+ A Selenium-compliant driver added to a "drivers" folder. This project used a Firefox 
driver downloaded from [here](https://github.com/mozilla/geckodriver/releases).
+ A cfg.py file with constants set that are used for configuration and processing. sample_cfg.py 
is provided showing the constant declarations. 

Steps Completed:
+ Scraping
+ Writing to DynamoDB

TODO:
+ IaC with Terraform.
+ Processing using PySpark with Amazon AWS EMR.
+ Word cloud creation.
+ Final report.
