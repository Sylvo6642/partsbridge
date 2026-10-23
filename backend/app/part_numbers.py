"""Part-number helpers.

Buyers type part numbers in many ways: "6205-2RS1", "6205 2rs1", "6205.2RS1".
Normalizing turns them into one form so they can be compared exactly.
"""

import re

_NOT_ALNUM = re.compile(r"[^A-Z0-9]")


def normalize_part_number(raw: str) -> str:
    """Uppercase and keep only letters and digits: '6205-2RS1' -> '62052RS1'."""
    return _NOT_ALNUM.sub("", raw.upper())
