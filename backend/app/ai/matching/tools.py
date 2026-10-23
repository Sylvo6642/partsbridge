"""Tools the matching agent can call.

Each tool is a plain Python function plus a JSON schema that tells the model what it does and what arguments it takes.
The tools only *read* the public catalog, and they never take user or seller ids from the model.
"""

import json

import psycopg

from app.ai.matching import search

SEARCH_LIMIT = 8

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "search_catalog",
        "description": "Search the parts catalog. Returns up to 8 candidate parts with their specs. "
                       "Try different wording if the first search does not find a good fit.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for, e.g. '6205 sealed bearing'"},
                "part_number": {"type": ["string", "null"],
                                "description": "A part number from the buyer's line, or null"},
            },
            "required": ["query", "part_number"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "find_equivalent",
        "description": "List the same physical part made by other brands (interchangeable parts).",
        "parameters": {
            "type": "object",
            "properties": {"part_id": {"type": "integer", "description": "A part_id returned by search_catalog"}},
            "required": ["part_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

PART_COLUMNS = "id, brand, part_number, description, specs"


def _part_dict(row) -> dict:
    part_id, brand, part_number, description, specs = row
    return {"part_id": part_id, "brand": brand, "part_number": part_number, "description": description,
            "specs": specs}


def search_catalog(conn: psycopg.Connection, query: str, part_number: str | None) -> list[dict]:
    hits = search.hybrid(conn, query, part_number, limit=SEARCH_LIMIT)
    ids = [h.part_id for h in hits]
    rows = conn.execute(f"select {PART_COLUMNS} from parts where id = any(%s)", (ids,)).fetchall()
    by_id = {row[0]: _part_dict(row) for row in rows}
    return [by_id[i] for i in ids]  # keep the search ranking


def find_equivalent(conn: psycopg.Connection, part_id: int) -> list[dict]:
    rows = conn.execute(
        f"""select {PART_COLUMNS} from parts
            where interchange_group = (select interchange_group from parts where id = %s) and id <> %s
            order by brand""",
        (part_id, part_id),
    ).fetchall()
    return [_part_dict(r) for r in rows]


# ---------------------------------------------------------------- v2: one result per physical part
# v1 returned one row per brand, so the model saw "6205-2RS1, 6205DDU, 6205-2RSR" as three different parts and kept
# asking the buyer to choose. v2 groups brands under the physical part they belong to.

SEARCH_GROUPED_SCHEMA = {
    "type": "function",
    "name": "search_catalog",
    "description": "Search the parts catalog. Returns up to 6 physical parts with their specs. Each physical part "
                   "lists its brand options (part_id, brand, part_number); options of one part are interchangeable. "
                   "Try different wording if the first search does not find a good fit.",
    "parameters": TOOL_SCHEMAS[0]["parameters"],
    "strict": True,
}


def _physical_parts(conn: psycopg.Connection, groups: list[str]) -> list[dict]:
    """One entry per physical part (interchange group), with its brand options, in the given order."""
    rows = conn.execute(
        "select interchange_group, id, brand, part_number, description, specs from parts "
        "where interchange_group = any(%s) order by id", (groups,),
    ).fetchall()
    physical: dict[str, dict] = {}
    for group, part_id, brand, pn, description, specs in rows:
        entry = physical.setdefault(group, {"description": description.rsplit(" Brand:", 1)[0], "specs": specs,
                                            "options": []})
        entry["options"].append({"part_id": part_id, "brand": brand, "part_number": pn})
    return [physical[g] for g in groups]


def search_catalog_grouped(conn: psycopg.Connection, query: str, part_number: str | None) -> list[dict]:
    hits = search.hybrid(conn, query, part_number, limit=20)
    groups = list(dict.fromkeys(h.interchange_group for h in hits))[:6]  # keep ranking order
    return _physical_parts(conn, groups)


# ---------------------------------------------------------------- v3: exact filtering on specs
# Search is fuzzy about numbers ("11 kW" ranked below "7.5 kW"), and so is the model when it reads results.
# filter_catalog lets the model state the specs and lets the database compare the numbers exactly.

def _nullable(kind: str, description: str, enum: list | None = None) -> dict:
    prop = {"type": [kind, "null"], "description": description}
    if enum:
        prop["enum"] = enum + [None]
    return prop


FILTER_FIELDS = {
    "bore_mm": _nullable("number", "bearing: inner diameter (shaft size) in mm"),
    "outer_diameter_mm": _nullable("number", "bearing or air filter: outer diameter in mm"),
    "width_mm": _nullable("number", "bearing: width in mm"),
    "sealing": _nullable("string", "bearing: open, shielded (ZZ, 2Z, metal shields) or sealed (2RS, DDU, rubber seals)",
                         ["open", "shielded", "sealed"]),
    "section": _nullable("string", "belt section", ["A", "B", "SPA", "SPB"]),
    "length": _nullable("number", "belt: inches for A and B (inner length), mm for SPA and SPB (datum length). "
                                  "Convert if needed: inches = mm / 25.4"),
    "kind": _nullable("string", "filter type", ["hydraulic", "spin-on", "air"]),
    "micron": _nullable("number", "hydraulic filter rating in micron"),
    "length_mm": _nullable("number", "hydraulic filter element length in mm"),
    "height_mm": _nullable("number", "spin-on or air filter height in mm"),
    "thread": _nullable("string", "spin-on filter thread", ["3/4-16 UNF", "1-12 UN", "M20x1.5"]),
    "power_kw": _nullable("number", "motor power in kW"),
    "poles": _nullable("integer", "motor poles: 2 (about 2900 rpm) or 4 (about 1450 rpm)"),
    "mounting": _nullable("string", "motor mounting: B3 = foot, B5 = flange", ["B3", "B5"]),
}

FILTER_SCHEMA = {
    "type": "function",
    "name": "filter_catalog",
    "description": "Find every physical part in a category whose specs equal the values given. Fill in only what the "
                   "buyer stated and leave the rest null. Returns the matching physical parts with brand options "
                   "(at most 8 shown) and how many there are in total.",
    "parameters": {
        "type": "object",
        "properties": {"category": {"type": "string", "enum": ["bearing", "belt", "filter", "motor"]},
                       **FILTER_FIELDS},
        "required": ["category", *FILTER_FIELDS],
        "additionalProperties": False,
    },
    "strict": True,
}


def filter_catalog(conn: psycopg.Connection, category: str, **specs) -> list[dict]:
    wanted = {k: v for k, v in specs.items() if v is not None and k in FILTER_FIELDS}
    rows = conn.execute(
        "select distinct interchange_group from parts where category = %s and specs @> %s::jsonb order by 1",
        (category, json.dumps(wanted)),
    ).fetchall()
    groups = [r[0] for r in rows]
    if not groups:
        return [{"result": f"no {category} has exactly these specs: {wanted}"}]
    found = _physical_parts(conn, groups[:8])
    if len(groups) > 8:
        found.append({"result": f"{len(groups) - 8} more parts not shown; the buyer must give more specs"})
    return found


TOOLSETS = {
    "matching_v1": [TOOL_SCHEMAS[0], TOOL_SCHEMAS[1]],
    "matching_v2": [SEARCH_GROUPED_SCHEMA],
    "matching_v3": [SEARCH_GROUPED_SCHEMA, FILTER_SCHEMA],
    "matching_v4": [SEARCH_GROUPED_SCHEMA, FILTER_SCHEMA],
}


def run_tool(conn: psycopg.Connection, name: str, arguments_json: str, grouped: bool = False) -> list[dict]:
    """Run the tool the model asked for. Unknown tools or bad arguments come back as an error the model can read."""
    try:
        args = json.loads(arguments_json)
        if name == "search_catalog":
            fn = search_catalog_grouped if grouped else search_catalog
            return fn(conn, args["query"], args.get("part_number"))
        if name == "find_equivalent":
            return find_equivalent(conn, int(args["part_id"]))
        if name == "filter_catalog":
            return filter_catalog(conn, **args)
        return [{"error": f"unknown tool {name}"}]
    except Exception as e:  # noqa: BLE001 (the model sees the error and can try again)
        return [{"error": f"{type(e).__name__}: {e}"}]
