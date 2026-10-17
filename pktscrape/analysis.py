"""Small local analysis used by the offline demonstration."""

import re
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

from .models import Experience


def top_words(records: list[Experience], *, limit: int = 30) -> list[tuple[str, int]]:
    words = re.findall(r"[a-zA-Z]{2,}", " ".join(record.description.lower() for record in records))
    return Counter(words).most_common(limit)


def write_word_cloud(words: list[tuple[str, int]], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    WordCloud(width=900, height=450, collocations=False, background_color="white").generate_from_frequencies(dict(words)).to_file(output)
    return output
