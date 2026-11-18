# GTA VI Twitch viewer forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/jacky01234567890/gta6-twitch-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/jacky01234567890/gta6-twitch-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecasts how many people watch Grand Theft Auto VI live on Twitch in
each hour of its release day, 2026-11-19 (UTC), from the first hour's
count and the launch-day shapes of past big game launches.

`python3 main.py` reads every `*.in` case file from `MAKEFUN_INPUT_DIR`
(or `/input`) and writes one `.out` forecast per case to
`MAKEFUN_OUTPUT_DIR` (or `/output`). Each forecast gives five quantiles
(5%, 25%, 50%, 75%, 95%) of the viewer count for hours 2 to 24.

Method: for each hour, the log-space line fitted across past launches
and the median log-ratio to the first hour are averaged, with a spread
that widens where the two views disagree. Standard library only;
deterministic.

Entry for make.fun's `gta6-twitch-ccu-forecast-01` bounty.
