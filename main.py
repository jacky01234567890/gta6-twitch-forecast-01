#!/usr/bin/env python3
"""Hour-by-hour forecast of GTA VI's launch-day Twitch viewers.

For every case file found in the input directory this program writes one
forecast file to the output directory.  A case carries the first hour's
viewer count for the release day and the hourly counts of past big game
launches (the comparables).  For each hour of the day the program
combines two views of the launch-day shape, both in log space: a line
fitted across the comparables -- log viewers in that hour against log
viewers in the first hour -- and the median ratio of that hour's viewers
to the first hour's.  The line captures how the shape changes with the
size of the launch; the ratio keeps the forecast tied to this launch's
own first hour, which matters most where the launch is bigger than any
comparable.  Their average is the centre, and the spread is the wider
of the two views' spreads and half their disagreement, so hours the
views disagree about get wider bands.  Where too few comparables cover
an hour, the forecast falls back to whichever view has data, and where
there is nothing at all it holds the first hour's count with a band that
widens over the day.

Only the standard library is used.  The program is deterministic: the
same input always yields the same bytes.
"""

import json
import math
import os
from datetime import datetime
from pathlib import Path

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
# Standard normal quantiles at LEVELS.
Z = (-1.6448536269514722, -0.6744897501960817, 0.0,
     0.6744897501960817, 1.6448536269514722)
FORECAST_HOURS = range(2, 25)
MAX_VIEWERS = 1_000_000_000.0
MIN_SPREAD = 0.15
MAX_SPREAD = 0.9


def _parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _release_day_hours(comparable):
    """Map release-day hour (1..24) to viewers for one comparable."""
    day_start = _parse_time(comparable["day_start"])
    hours = {}
    for row in comparable.get("hourly") or []:
        try:
            when = _parse_time(row["from"])
            viewers = row.get("viewers")
        except (KeyError, TypeError, ValueError):
            continue
        hour = int((when - day_start).total_seconds() // 3600) + 1
        if 1 <= hour <= 24 and viewers is not None and viewers > 0:
            hours[hour] = float(viewers)
    return hours


def _ols(pairs):
    """Least squares y = a + b*x for [(x, y)]; returns (a, b, resid_std)."""
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    if sxx <= 0:
        return my, 0.0, 0.0
    b = sum((x - mx) * (y - my) for x, y in pairs) / sxx
    a = my - b * mx
    if n > 2:
        var = sum((y - (a + b * x)) ** 2 for x, y in pairs) / (n - 2)
        resid = math.sqrt(max(var, 0.0))
    else:
        resid = 0.0
    return a, b, resid


def _median(values):
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def _spread(values):
    """Robust spread of log ratios: half the interquartile range."""
    if len(values) < 2:
        return MIN_SPREAD
    vals = sorted(values)
    n = len(vals)
    q1 = vals[n // 4]
    q3 = vals[(3 * n) // 4]
    return max((q3 - q1) / 1.349, MIN_SPREAD)


def _forecast(first, days):
    """Forecast rows for hours 2..24 from a first-hour count and day maps."""
    log_first = math.log(max(float(first), 1.0))
    rows = []
    for hour in FORECAST_HOURS:
        pairs = [(math.log(d[1]), math.log(d[hour]))
                 for d in days if hour in d]
        ratios = [math.log(d[hour]) - math.log(d[1])
                  for d in days if hour in d]
        centre_ols = spread_ols = None
        if len(pairs) >= 8:
            a, b, resid = _ols(pairs)
            centre_ols = a + b * log_first
            spread_ols = min(max(resid, MIN_SPREAD), MAX_SPREAD)
            if len(pairs) < 15:
                spread_ols = max(spread_ols, 0.25)
        centre_rat = spread_rat = None
        if ratios:
            centre_rat = log_first + _median(ratios)
            spread_rat = min(max(_spread(ratios), MIN_SPREAD), MAX_SPREAD)
        if centre_ols is not None and centre_rat is not None:
            centre = (centre_ols + centre_rat) / 2.0
            spread = min(max(spread_ols, spread_rat,
                             abs(centre_ols - centre_rat) / 2.0),
                         MAX_SPREAD)
        elif centre_rat is not None:
            centre, spread = centre_rat, spread_rat
        elif centre_ols is not None:
            centre, spread = centre_ols, spread_ols
        else:
            centre = log_first
            spread = min(max(0.15 * math.sqrt(hour - 1),
                             MIN_SPREAD), MAX_SPREAD)
        quantiles = []
        prev = 0.0
        for z in Z:
            q = math.exp(centre + z * spread)
            q = min(max(q, 1.0), MAX_VIEWERS)
            q = round(q, 2)
            if q < prev:
                q = prev
            quantiles.append(q)
            prev = q
        rows.append({"hour": hour, "q": quantiles})
    return {"hours": rows}


def forecast_case(case):
    """Return the forecast object for one case dict."""
    known = case.get("known") or []
    first = 1.0
    if known:
        first = max(float(known[0].get("viewers") or 1), 1.0)
    days = []
    for comp in case.get("comparables") or []:
        hours = _release_day_hours(comp)
        if 1 in hours:
            days.append(hours)
    return _forecast(first, days)


def main():
    in_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR") or "/input")
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    for in_file in sorted(in_dir.glob("*.in")):
        with open(in_file, "r", encoding="utf-8") as fh:
            case = json.load(fh)
        forecast = forecast_case(case)
        out_file = out_dir / (in_file.stem + ".out")
        with open(out_file, "w", encoding="utf-8") as fh:
            json.dump(forecast, fh)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
