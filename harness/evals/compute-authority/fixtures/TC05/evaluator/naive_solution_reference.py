# Evaluator-only reference of a first-pass solution that leaves 3 defects.
def tmp1(s):
    return s.strip()

def do_strip(s):
    return " ".join(s.split())

def strip_again(s):
    return " ".join(s.split())

def normalize_name(name: str) -> str:
    return do_strip(tmp1(name)).lower()
