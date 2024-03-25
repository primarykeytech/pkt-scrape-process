import re


def strip_html(data):
    """
    This function strips html tags from a string.
    :param data: str html
    :return: str without html tags.
    """
    p = re.compile(r'<.*?>')
    return p.sub('', data)
