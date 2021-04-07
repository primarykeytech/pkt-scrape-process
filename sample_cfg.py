# page on website that serves as base for archives.
BASE_URL = \
    'https://awebsite.org/index'

# only extract the links that have these strings
# as part of the urls.
BASE_MUST_CONTAIN = '/someword/'
PAGE_MUST_CONTAIN = '/someword/'

# urls to use for testing.
TEST_SINGLE_PAGE_URL = \
    'https://awebsite.org/2019'
TEST_SINGLE_PAGE_CONTENT = \
    'https://awebsite.org/2019/experience1'
TEST_SINGLE_PAGE_CONTAINS = '/someword/'

# AWS resource settings.
AWS_REGION = 'your-region'
DB_TABLE = 'your-dynamodb-table'