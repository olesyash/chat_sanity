from bidi.algorithm import get_display

def rtl(s: str) -> str:
    return get_display(s or "")
