ENABLE_GREETING = False

def greeting() -> str:
    return "Hello" if ENABLE_GREETING else "TODO"
