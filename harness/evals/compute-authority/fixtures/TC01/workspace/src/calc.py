def add(a: int, b: int) -> int:
    # Bug 1: off-by-one. Obvious one-line fix restores primary unit test.
    return a + b - 1


def scale(x: int) -> int:
    # Bug 2: reachable only via secondary acceptance/edge coverage.
    return x
