"""Degree descriptions collected from university websites, searched by keyword (BM25). No Streamlit calls.

data/degree_info.json holds one record per degree page (title, school, source link, text), an index from
"course_code|institution_name" to a record, the list of covered universities, and the website of every
institution in the DGES table. Only covered universities have text; for the others the caller gets the
institution's website instead of text, so nothing is described from memory.
"""
import json
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "degree_info.json"
STOP = set("a o as os de da do das dos e em no na nos nas um uma para por com que se ao aos the of and to in is for on".split())
CHUNK_CHARS = 700

def _plain(text):
    text = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()

def _tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", _plain(text)) if len(w) > 2 and w not in STOP]

def _stem(word):
    return word[:5]  # crude, but enough to match engenharia/engenheiro or aeroespacial/aeroespace

@lru_cache(maxsize=1)
def _data():
    if not DATA_PATH.exists():
        return {"records": [], "index": {}, "sites": {}, "covered": []}
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

def _chunks(record):
    """Short passages of a record, each starting with its heading when there is one."""
    chunks, heading, buf = [], "", ""
    for line in record["text"].split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) < 45 and not line.endswith((".", ":")) and not line.startswith("•"):
            if buf:
                chunks.append((heading, buf.strip()))
                buf = ""
            heading = line
            continue
        if len(buf) + len(line) > CHUNK_CHARS and buf:
            chunks.append((heading, buf.strip()))
            buf = ""
        buf += line + "\n"
    if buf.strip():
        chunks.append((heading, buf.strip()))
    return chunks

@lru_cache(maxsize=1)
def _index():
    """All passages with their term counts, for BM25."""
    entries = []
    for pid, record in enumerate(_data()["records"]):
        for heading, text in _chunks(record):
            terms = [_stem(t) for t in _tokens(f"{record['title']} {heading} {text}")]
            counts = {}
            for t in terms:
                counts[t] = counts.get(t, 0) + 1
            entries.append({"rec": pid, "heading": heading, "text": text, "counts": counts, "len": max(1, len(terms))})
    avg = sum(e["len"] for e in entries) / max(1, len(entries))
    df = {}
    for e in entries:
        for t in e["counts"]:
            df[t] = df.get(t, 0) + 1
    return entries, df, avg

def _score(entry, query_terms, df, n, avg, k1=1.4, b=0.75):
    s = 0.0
    for t in query_terms:
        f = entry["counts"].get(t, 0)
        if not f:
            continue
        idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
        s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * entry["len"] / avg))
    return s

def record_for(course_code, institution_name):
    """The degree record for one program, or None when its university is not covered."""
    code = str(course_code).strip()
    code = code[:-2] if code.endswith(".0") else code
    i = _data()["index"].get(f"{code}|{str(institution_name).strip()}")
    return None if i is None else _data()["records"][i]

def institution_site(institution_name):
    return _data()["sites"].get(str(institution_name).strip())

def covered_universities():
    return list(_data()["covered"])

def search(question, record=None, top=4):
    """Best passages for a question, from one record or from every collected degree."""
    entries, df, avg = _index()
    terms = list({_stem(t) for t in _tokens(question)})
    if not terms or not entries:
        return []
    records = _data()["records"]
    scored = []
    for e in entries:
        if record is not None and records[e["rec"]] is not record:
            continue
        s = _score(e, terms, df, len(entries), avg)
        if s > 0:
            scored.append((s, e))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], {}
    for s, e in scored:
        if record is None and seen.get(e["rec"], 0) >= 1:
            continue  # across degrees: one passage per degree
        seen[e["rec"]] = seen.get(e["rec"], 0) + 1
        r = records[e["rec"]]
        out.append({"degree": r["title"], "school": r["school"], "campus": r["campus"], "section": e["heading"],
                    "text": e["text"], "source_url": r["source_url"]})
        if len(out) >= top:
            break
    if record is not None and not out:  # nothing matched: give the opening passages
        for heading, text in _chunks(record)[:top]:
            out.append({"degree": record["title"], "school": record["school"], "campus": record["campus"],
                        "section": heading, "text": text, "source_url": record["source_url"]})
    return out
