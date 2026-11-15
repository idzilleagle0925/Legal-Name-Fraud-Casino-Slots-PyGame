# LEGAL NAME FRAUD TRUTH CHANNEL: ONE-ARMED BAND-IDS

A themed 5x3 video slot machine written in Python with pygame. Every win is a **cord cut**: scissors snip the payline and sever your ties to the legal name.

Everything is generated in code, including the symbols, lever, lights, sound effects and chiptune music. There are no image or audio files to ship.

**Link:** https://legalnamefraud.carrd.co (also clickable inside the game)

> Entertainment only. Play credits have no cash value and no real money is involved.

.exe Windows file also available for fast/easy gameplay without the need for pygame/python.
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








# How to Play: Legal Name Fraud Casino Slots

No coding needed. Just follow the steps in order. When you see a gray box, type that exact text into the black window and press **Enter**.

---

## Step 1: Download the game file

1. On GitHub, open the file **one_armed_bandids.py**.
2. Click the **Download raw file** button (the download arrow, top right of the code box).
3. Save it anywhere you like (Desktop, Downloads, or a folder). Remember where you put it.

---

## Step 2: Open the terminal

The terminal is a black window where you type commands.

1. Press the **Windows key** on your keyboard.
2. Type **cmd**.
3. Press **Enter**.

A black window opens. Keep it open.

---

## Step 3: Check if you have Python

Type this and press Enter:

```
python --version
```

- If it shows something like `Python 3.12.3`, you have Python. **Go to Step 5.**
- If it says `'python' is not recognized`, or the Microsoft Store opens, you need Python. **Go to Step 4.**

---

## Step 4: Install Python (only if you needed it)

1. Go to **python.org/downloads**
2. Click the yellow **Download Python** button and open the file.
3. On the first screen, **tick the box "Add python.exe to PATH"**. This is important.
4. Click **Install Now**.
5. When it finishes, click **Close**.
6. **Close the black window and open a new one** (repeat Step 2).
7. Type `python --version` again. You should see a version number now.

---

## Step 5: Install pygame-ce

Pygame is the add-on that lets the game run. Type this and press Enter:

```
python -m pip install pygame-ce
```

Wait until it says **Successfully installed**. This only has to be done once.

---

## Step 6: Go to the folder where you saved the game

Type `cd` followed by a **space**, then **drag your folder** from File Explorer into the black window. It fills in the folder path for you. Press Enter.

Example of what it looks like when done:

```
cd C:\Users\YourName\Downloads
```

**If you saved the file to the Desktop or Downloads, you can also type:**

```
cd Desktop
```

or

```
cd Downloads
```

**Check you are in the right place.** Type this and press Enter:

```
dir
```

You should see **one_armed_bandids.py** in the list. If you do not, go back and try Step 6 again.

---

## Step 7: Run the game

Type this and press Enter:

```
python one_armed_bandids.py
```

The game opens. Click **PLAY** or press **SPACE**.

**To play again another day:** open the terminal (Step 2), go to the folder (Step 6), and run the game (Step 7). You do not need to install anything again.

---

## Controls

| Action | Key |
|---|---|
| Spin / quick-stop | `SPACE` or click the red lever |
| Bet up / down | `UP` / `DOWN` arrows |
| Lines more / fewer | `RIGHT` / `LEFT` arrows |
| Max bet | `M` |
| Auto-spin | `A` |
| Turbo | `T` |
| Gamble last win | `G` |
| Paytable | `P` |
| Sound on / off | `S` |
| Fullscreen | `F11` |
| Quit | `ESC` |

---

## Problems?

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Python isn't installed, or "Add python.exe to PATH" wasn't ticked. Redo Step 4, then open a **new** black window. |
| `Failed to build pygame` | Use `python -m pip install pygame-ce` (Step 5). If it still fails, install **Python 3.12** from python.org and try again. |
| `No module named pygame` | Redo Step 5. |
| `can't open file one_armed_bandids.py` | You're in the wrong folder. Redo Step 6 and check with `dir`. |
| Want a fresh start with 1,000 credits | Run `python one_armed_bandids.py --reset` once. |

*Mac users: use `python3` instead of `python` everywhere, and open Terminal with Command + Space, then type Terminal.*

*For entertainment only. Credits have no cash value.*
