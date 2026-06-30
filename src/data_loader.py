import json
import gzip
import os

def stream_candidates(file_path):
    """
    Streams candidates from a JSONL file one by one to keep memory usage low.
    Handles both raw .jsonl files and gzipped .jsonl.gz files.
    """
    # Choose standard open or gzip.open based on the file extension
    opener = gzip.open if file_path.endswith(".gz") else open
    mode = "rt" if file_path.endswith(".gz") else "r"
    
    with opener(file_path, mode, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
