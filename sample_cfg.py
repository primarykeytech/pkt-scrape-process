import os

# page on website that serves as base for archives.
HOME_URL = 'https://awebsite.org.com'
BASE_URL = 'https://awebsite.org/forum'

# used to distinguish records in the database.
# e.g. experience type 1 vs experience type 2.
CLASSIFICATION = '<classification>'

# only extract the links that have these strings
# as part of the urls.
BASE_MUST_CONTAIN = '/someword/'
PAGE_MUST_CONTAIN = '/someword/'

# used to identify the content sections on the page.
# e.g. <div class="content-div">...</div>
IDENTIFY_CONTENT = 'content-div'
IDENTIFY_BY = 'class'

# urls to use for testing.
TEST_SINGLE_PAGE_URL = \
    'https://awebsite.org/2019'
TEST_SINGLE_PAGE_CONTENT = \
    'https://awebsite.org/2019/experience1'

# forums will often use a subdirectory to categorize the experiences.
TEST_SINGLE_PAGE_CONTAINS = '/someword/'

# AWS resource settings.
AWS_REGION = 'your-region'
DB_TABLE = 'your-dynamodb-table'

# I am using a virtual environment in my IDE, so I needed to set the
# environment variables here for my AWS credentials.
os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "<full path to credentials>"
os.environ["AWS_DEFAULT_PROFILE"] = "<profile name>"
