import re


def strip_html(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)