from src.neighbor_a import expected_prefix
from src.neighbor_b import expected_suffix

def compose(name: str) -> str:
    # Bug: drops suffix required by neighbor_b contract.
    return expected_prefix() + name
