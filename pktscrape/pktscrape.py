"""Compatibility functions for the original tutorial API."""

from . import config
from .models import Experience


def extract_experience(bs_content):
    return [item.get_text(" ", strip=True) for item in bs_content.find_all("div", config.IDENTIFY_CONTENT)]


def create_experience_obj(bs_content):
    descriptions = extract_experience(bs_content)
    return Experience.create(title=config.BASE_URL, classification=config.CLASSIFICATION,
                             description=descriptions[0] if descriptions else "")


def experience_objects_from_list(list_content):
    return [Experience.create(title=f"{index} - {config.BASE_URL}", classification=config.CLASSIFICATION,
                              description=description) for index, description in enumerate(list_content)]
