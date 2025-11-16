from bidi.algorithm import get_display
import unicodedata

def _sanitize_for_bidi(s: str) -> str:
    out = []
    for ch in s:
        if ch in ("\n", "\t"):
            out.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cs", "Cf"):
            continue
        out.append(ch)
    return "".join(out)

def rtl(s: str) -> str:
    text = _sanitize_for_bidi(s or "")
    lines = text.splitlines()
    out_lines = []
    for line in lines:
        try:
            out_lines.append(get_display(line))
        except Exception:
            out_lines.append(line)
    return "\n".join(out_lines)
