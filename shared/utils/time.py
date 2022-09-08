def sec_format(secs: int, f: str = "{h}:{m}:{s}") -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return f.format(h=h, m=m, s=s)
