"""Framework-agnostic validation helpers.

Kept isolated from Flask and from the database on purpose: these
functions are pure, so they are trivial to unit test and can be reused
outside a request context (e.g. from the JSON API blueprint or a
future CLI/import script).
"""


def parse_weight(raw):
    """Parse user input into a positive numeric weight.

    Returns an int or float if valid, otherwise None.
    """
    try:
        weight = float(raw)
    except (TypeError, ValueError):
        return None

    if weight <= 0:
        return None

    return int(weight) if weight.is_integer() else weight


def parse_positive_int(raw):
    """Parse user input into a positive integer.

    Returns an int if valid, otherwise None.
    """
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None

    if value <= 0:
        return None

    return value
