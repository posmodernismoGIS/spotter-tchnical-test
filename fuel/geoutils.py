import csv
import re

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

SUFFIX_RE = re.compile(r"\s+(city|town|village|borough|CDP|municipality|township)$", re.I)

def city_key(name: str) -> str:
    """'Mc Calla' -> 'MCCALLA', 'Saint Johns' -> 'STJOHNS', 'Mount Vernon' -> 'MTVERNON'."""
    key = re.sub(r"[^A-Z0-9 ]", "", name.upper())
    key = re.sub(r"\bSAINTE\b", "STE", key)
    key = re.sub(r"\bSAINT\b", "ST", key)
    key = re.sub(r"\bFORT\b", "FT", key)
    key = re.sub(r"\bMOUNT\b", "MT", key)
    return key.replace(" ", "")

def read_gazetteer(path):
    """Yield (name, state, lat, lon) from the Census Gazetteer places file."""
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = [h.strip() for h in next(reader)]
        idx = {h: i for i, h in enumerate(header)}
        for row in reader:
            name = SUFFIX_RE.sub("", row[idx["NAME"]].strip())
            yield (name, row[idx["USPS"]].strip(),
                   float(row[idx["INTPTLAT"]]), float(row[idx["INTPTLONG"]]))

