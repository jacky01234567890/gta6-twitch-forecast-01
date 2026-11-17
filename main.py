import json, math, os, glob, statistics

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]

def read_cases(inp):
    for path in sorted(glob.glob(os.path.join(inp, "*.in"))):
        with open(path, encoding="utf-8") as f:
            yield json.load(f)

def ratio_curve(comp):
    rows = comp.get("hourly") or []
    by_hour = {}
    for row in rows:
        day = comp.get("day_start", "")[:10]
        start = row.get("from", "")
        if len(start) >= 13:
            try:
                h = int(start[11:13]) + 1
            except ValueError:
                continue
            by_hour[h] = max(1.0, float(row.get("viewers") or 1))
    if 1 not in by_hour:
        return None
    p = by_hour[1]
    return [by_hour.get(h, p) / p for h in range(1, 25)]

def forecast(case):
    known = case.get("known") or []
    p = float(known[0].get("viewers", 1) if known else 1)
    p = max(1.0, p)
    curves = []
    for comp in case.get("comparables") or []:
        curve = ratio_curve(comp)
        if curve:
            curves.append(curve)
    history = case.get("history_hourly") or []
    if len(history) >= 2:
        recent = max(1.0, float(history[-1].get("viewers") or p))
        first = max(1.0, float(history[0].get("viewers") or p))
        # A small trend adjustment, clipped to avoid unstable extrapolation.
        trend = max(0.75, min(1.35, recent / first))
    else:
        trend = 1.0
    rows = []
    for h in range(2, 25):
        ratios = [c[h-1] for c in curves if len(c) >= h and c[h-1] > 0]
        if ratios:
            center = statistics.median(ratios) * (trend ** min((h-1)/6, 1.0))
            dispersion = max(0.10, min(0.42, statistics.pstdev([math.log(x) for x in ratios]) if len(ratios) > 1 else 0.18))
        else:
            center = 1.0
            dispersion = 0.15 * math.sqrt(h - 1)
        center = max(0.05, min(10000.0, center))
        spread = max(0.10, min(0.8, dispersion * (0.9 + 0.12 * math.sqrt(h - 1))))
        qs = [round(max(1.0, min(1_000_000_000.0, p * center * math.exp(z * spread))), 2) for z in Z]
        qs = [max(qs[i], qs[i-1]) if i else qs[i] for i in range(5)]
        rows.append({"hour": h, "q": qs})
    return {"hours": rows}

def main():
    inp = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    for case in read_cases(inp):
        result = forecast(case)
        with open(os.path.join(out, f"{case['id']}.out"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, separators=(",", ":"), ensure_ascii=False)

if __name__ == "__main__":
    main()
