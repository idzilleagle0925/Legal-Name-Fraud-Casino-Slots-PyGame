# LEGAL NAME FRAUD TRUTH CHANNEL: ONE-ARMED BAND-IDS

A themed 5x3 video slot machine written in Python with pygame. Every win is a **cord cut**: scissors snip the payline and sever your ties to the legal name.

Everything is generated in code, including the symbols, lever, lights, sound effects and chiptune music. There are no image or audio files to ship.

**Link:** https://legalnamefraud.carrd.co (also clickable inside the game)

> Entertainment only. Play credits have no cash value and no real money is involved.

---

## Features

- 5 reels x 3 rows, 10 selectable paylines, bet per line 1 to 100
- Title screen, animated pull-lever arm, motion-blur reels, bounce stops and anticipation glow
- Winning-line animation with scissors cutting the payline, pulsing symbols and a marquee light frame
- **BCCRSS** bonus symbol that triggers free spins (all line wins x2, retriggerable)
- **CRSSNOW** wild that substitutes for every symbol except BCCRSS
- **TIES SEVERED** meter that charges on every win, and charges faster on JUDGE BOWS and JANE DOE-755
- **Bonus wheel** with multipliers, free spins or the **CUT THE CORDS** pick game
- **Red or black card gamble** using a real 52-card deck, up to 5 rounds
- Big-win celebrations with a count-up, coin shower and screen shake
- Red **LEGAL NAME FRAUD** stamp on spins with no win
- Auto-spin, turbo mode, max bet and quick-stop
- Built-in paytable screen
- Synthesised sound effects and looping 8-bit style music
- Credits, bet settings and stats auto-save between sessions

## Install and run

Requires Python 3.9+.

```bash
pip install pygame-ce
python one_armed_bandids.py
```

`pygame-ce` is a drop-in fork of `pygame` (same `import pygame`). If `pip install pygame` fails to build on a very new Python version, use `pygame-ce` instead.

### Command-line options

```bash
python one_armed_bandids.py --sim 1000000   # headless RTP / hit-rate / bonus simulation
python one_armed_bandids.py --reset         # delete the save file and start fresh
```

## Controls

| Key / Mouse | Action |
|---|---|
| `SPACE` / `ENTER` or click the **arm** | Spin, quick-stop, skip win counter, spin the bonus wheel, pick a cord |
| `UP` / `DOWN` | Bet per line +/- |
| `LEFT` / `RIGHT` | Number of lines -/+ |
| `M` | Max bet and spin |
| `A` | Auto-spin on/off |
| `T` | Turbo on/off |
| `G` | Gamble the last win |
| `R` / `B` / `C` | In gamble: red / black / collect |
| `P` | Paytable |
| `S` / `N` | Sound effects / music on/off |
| `F11` | Fullscreen |
| `ESC` | Close paytable / quit |

## Symbols and paytable

Pays are a multiplier of **bet per line** for 3 / 4 / 5 of a kind, on adjacent reels from the left.

| Symbol | 3 | 4 | 5 |
|---|---|---|---|
| ID (burning) | 5 | 12 | 36 |
| BIRTH CERT (burning) | 5 | 14 | 48 |
| JANE DOE-755 (charges meter) | 7 | 19 | 72 |
| TRUTH BILLBOARD | 10 | 24 | 96 |
| SCISSORS | 14 | 48 | 192 |
| CUT CORD | 24 | 96 | 360 |
| CHI RHO | 36 | 150 | 600 |
| THE LAW | 48 | 192 | 960 |
| JUDGE BOWS (charges meter) | 60 | 300 | 1500 |
| UNCHAINED | 72 | 360 | 1920 |
| **CRSSNOW** (wild) | 120 | 600 | 3600 |

**BCCRSS (bonus):** 3 / 4 / 5 anywhere pay 2x / 10x / 50x your **total** bet and award 10 / 15 / 20 free spins.

## Bonus features

**Free spins:** all line wins are doubled, and 3+ BCCRSS during free spins retrigger more.

**TIES SEVERED meter:** every winning spin charges the meter, and JUDGE BOWS and JANE DOE-755 symbols charge it faster. When it fills, the **bonus wheel** appears. Prizes are 5x, 10x, 15x, 25x or 50x your total bet, **+8 free spins**, or the **CUT THE CORDS** pick game.

**CUT THE CORDS pick game:** 12 cords hang in front of you and you start with 3 cuts. Prizes range from 2x to 10x your total bet. Some cords give +2 extra cuts, and hitting a LEGAL NAME ends the round.

**Gamble:** after any win, guess the colour (red or black) of a card drawn from a 52-card deck to double your win, up to 5 rounds in a row.

## Math model

Measured with the built-in simulator (`--sim`, 10 lines):

- RTP about 96% (includes free spins and the bonus wheel / pick game)
- Hit frequency about 31%
- Free spins about 1 in 265 spins
- Bonus wheel about 1 in 115 spins

Reel strips are fixed and shuffled with a seeded generator, so the machine is identical every run. Symbol weights, paytable, meter size and bonus odds are all plain constants near the top of the file (`PAYTABLE`, `REEL_COUNTS`, `METER_MAX`, `WHEEL_WEIGHTS`, `PICK_PRIZES`), so they are easy to tweak.

## Save data

Credits, bet, lines, sound/music settings, meter and stats are saved to `bandids_save.json` next to the script. Delete the file or run with `--reset` to start over. You get 1,000 credits to start, and **PLAY AGAIN** appears when you run out.

one_armed_bandids.py 
