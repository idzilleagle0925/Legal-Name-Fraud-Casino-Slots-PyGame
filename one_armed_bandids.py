#!/usr/bin/env python3
"""
ONE-ARMED BAND-IDS  -  a legal-name-fraud themed 5x3 slot machine, written in pygame.

Your ID is bad. Your birth certificate is bad. Every win is a CORD CUT: scissors
snip the payline and sever your ties to the LEGAL NAME. BCCRSS and CRSSNOW are the
ultimate bonus symbols.

Everything (symbols, lever, lights, coins, sounds) is generated in code - no asset files.

    pip install pygame-ce        (or pygame)
    python one_armed_bandids.py

Options:
    python one_armed_bandids.py --sim 1000000   # headless RTP / hit-rate simulation
    python one_armed_bandids.py --reset         # wipe the save file

SYMBOLS (low to high): BAD ID, BAD B-CERT, LEGAL NAME, DENIED, SCISSORS, CUT CORD,
GOLD SEAL, UNCHAINED.  CRSSNOW = WILD (substitutes for everything except BCCRSS and
pays the most).  BCCRSS = BONUS: 3+ anywhere pay a total-bet multiplier and start the
CORD-CUT BONUS (free spins, all line wins x2, retriggerable).
JANE DOE-755 (LEGAL NAME) and JUDGE BOWS pay on lines and also trigger their own
bonuses.  A spin with no win gets the red REJECTED stamp.  After a win you can
risk it: CUT OR DENIED — guess red or black on a real 52-card deck, up to 5 rounds.

CONTROLS
    SPACE / ENTER or click the ARM   spin, quick-stop, skip win counter
    UP / DOWN      bet per line         LEFT / RIGHT   lines
    M max bet   A auto-spin   T turbo   G gamble   P paytable   S sound   F11 fullscreen
    (in gamble: R red, B black, C collect)      ESC close paytable / quit
    Title screen: SPACE / PLAY to start
"""

import array
import json
import math
import random
import sys
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
W, H = 1280, 720
FPS = 60
TITLE = "LEGAL NAME FRAUD TRUTH CHANNEL"

CELL = 132            # size of one symbol cell (pixels)
GAP = 6               # gap between reels
REEL_W = 5 * CELL + 4 * GAP
REEL_H = 3 * CELL
RX = (W - REEL_W) // 2
RY = 96
PANEL_Y = 584

START_CREDITS = 1000
BET_OPTIONS = [1, 2, 5, 10, 25, 50, 100]
MAX_LINES = 10
FREE_SPIN_MULT = 2

try:
    SAVE_PATH = Path(__file__).with_name("bandids_save.json")
except NameError:  # interactive use
    SAVE_PATH = Path("bandids_save.json")

GOLD = (255, 208, 64)
GOLD_D = (190, 140, 20)
RED = (225, 40, 55)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (70, 210, 100)
PURPLE = (150, 70, 220)
FONT_NAMES = "impact,arialblack,arial,helvetica,dejavusans"

# ---------------------------------------------------------------------------
# SYMBOLS, PAYTABLE, REELS, PAYLINES
# ---------------------------------------------------------------------------
ID_ILLEGAL, LEGAL_NAME_FRAUD, LEGAL_NAME, JUDGE_BOWS, SCISSORS, CUT_CORD, GOLD_10, UNCHAINED, WILD, SCATTER = range(10)
SYMBOL_NAMES = ["ID Illegal", "Legal Name Fraud", "JANE DOE-755", "JUDGE BOWS", "SCISSORS", "CUT CORD", "GOLD 10",
                "UNCHAINED", "CRSSNOW", "BCCRSS"]

# multiplier of the BET PER LINE for 3 / 4 / 5 of a kind
PAYTABLE = {
    ID_ILLEGAL:  (5, 12, 36),
    LEGAL_NAME_FRAUD:   (5, 14, 48),
    LEGAL_NAME:  (7, 19, 72),
    JUDGE_BOWS:    (10, 24, 96),
    SCISSORS:    (14, 48, 192),
    CUT_CORD:     (24, 96, 360),
    GOLD_10:   (48, 192, 960),
    UNCHAINED: (72, 360, 1920),
    WILD:    (120, 600, 3600),
}
# multiplier of the TOTAL BET for 3 / 4 / 5 scatters, plus free spins awarded
SCATTER_PAY = {3: 2, 4: 10, 5: 50}
SCATTER_FREE_SPINS = {3: 10, 4: 15, 5: 20}

# extra prize (credits) + free spins for 3 / 4 / 5 of a kind on a payline
# pay is computed in evaluate() from bet / total bet
DOE_BONUS = {
    3: {"pay_kind": "bet", "mult": 8, "free_spins": 0,
        "title": "JANE DOE-755 BONUS", "sub": "THE NAME IS VOID"},
    4: {"pay_kind": "total", "mult": 3, "free_spins": 5,
        "title": "JANE DOE-755 BONUS", "sub": "+5 CORD-CUT SPINS"},
    5: {"pay_kind": "total", "mult": 10, "free_spins": 10,
        "title": "JANE DOE-755 BONUS", "sub": "+10 CORD-CUT SPINS"},
}
JUDGE_BONUS = {
    3: {"pay_kind": "bet", "mult": 12, "free_spins": 0,
        "title": "JUDGE BOWS BONUS", "sub": "THE COURT YIELDS"},
    4: {"pay_kind": "total", "mult": 5, "free_spins": 5,
        "title": "JUDGE BOWS BONUS", "sub": "+5 CORD-CUT SPINS"},
    5: {"pay_kind": "total", "mult": 15, "free_spins": 10,
        "title": "JUDGE BOWS BONUS", "sub": "+10 CORD-CUT SPINS"},
}

CARD_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_SUITS = ("hearts", "diamonds", "clubs", "spades")  # first two are red

# number of each symbol on each reel strip (32 stops per reel)
#               CHR LEM ORG PLM BEL CUT_CORD SEV DIA WLD SCT
REEL_COUNTS = [
    (7, 6, 5, 5, 3, 2, 1, 1, 1, 1),
    (6, 5, 5, 4, 3, 3, 2, 1, 2, 1),
    (6, 5, 4, 4, 3, 3, 2, 1, 3, 1),
    (6, 5, 5, 4, 3, 3, 2, 1, 2, 1),
    (7, 6, 5, 5, 3, 2, 1, 1, 1, 1),
]

# row index (0 = top, 1 = middle, 2 = bottom) for each of the 5 reels
PAYLINES = [
    [1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0],
    [2, 2, 2, 2, 2],
    [0, 1, 2, 1, 0],
    [2, 1, 0, 1, 2],
    [0, 0, 1, 2, 2],
    [2, 2, 1, 0, 0],
    [1, 0, 0, 0, 1],
    [1, 2, 2, 2, 1],
    [1, 0, 1, 2, 1],
]
LINE_COLORS = [
    (255, 80, 80), (80, 200, 255), (120, 255, 120), (255, 200, 60), (230, 110, 255),
    (255, 140, 60), (90, 255, 220), (255, 120, 180), (190, 255, 90), (150, 160, 255),
]


def build_strips():
    """Fixed, shuffled reel strips (seeded so the machine is identical every run)."""
    rng = random.Random(777)
    strips = []
    for counts in REEL_COUNTS:
        symbols = [s for s, c in enumerate(counts) for _ in range(c)]
        best = symbols[:]
        for _ in range(2000):
            rng.shuffle(symbols)
            ok = all(symbols[i] != symbols[(i + 1) % len(symbols)] for i in range(len(symbols)))
            if ok:
                best = symbols[:]
                break
        strips.append(best)
    return strips


STRIPS = build_strips()


# ---------------------------------------------------------------------------
# GAME MATH (pure functions, no pygame needed)
# ---------------------------------------------------------------------------
def eval_line(syms):
    """Return (symbol, count) for a 5-symbol payline or None. Wild substitutes."""
    if syms[0] == SCATTER:
        return None
    leading_wilds = 0
    for s in syms:
        if s == WILD:
            leading_wilds += 1
        else:
            break
    base, count = None, 0
    for s in syms:
        if s == SCATTER:
            break
        if s == WILD:
            count += 1
        elif base is None:
            base, count = s, count + 1
        elif s == base:
            count += 1
        else:
            break
    best, best_pay = None, 0
    if base is not None and count >= 3:
        best, best_pay = (base, count), PAYTABLE[base][count - 3]
    if leading_wilds >= 3 and PAYTABLE[WILD][leading_wilds - 3] > best_pay:
        best = (WILD, leading_wilds)
    return best


def _line_bonus(symbol, count, bet, lines, table):
    spec = table.get(count)
    if not spec:
        return None
    pay = (spec["mult"] * bet) if spec["pay_kind"] == "bet" else spec["mult"] * bet * lines
    return {
        "kind": "bonus", "symbol": symbol, "count": count, "pay": pay,
        "free_spins": spec["free_spins"], "title": spec["title"], "sub": spec["sub"],
        "cells": [],
    }


def evaluate(grid, lines, bet, free):
    """grid[reel][row] -> (line_wins, scatter_info, extra_bonuses)."""
    mult = FREE_SPIN_MULT if free else 1
    wins = []
    for li in range(lines):
        rows = PAYLINES[li]
        syms = [grid[r][rows[r]] for r in range(5)]
        res = eval_line(syms)
        if res:
            sym, count = res
            wins.append({
                "kind": "line", "line": li, "symbol": sym, "count": count,
                "pay": PAYTABLE[sym][count - 3] * bet * mult,
                "cells": [(r, rows[r]) for r in range(count)],
            })
    cells = [(r, row) for r in range(5) for row in range(3) if grid[r][row] == SCATTER]
    n = len(cells)
    scatter = {"kind": "scatter", "count": n, "cells": cells, "pay": 0, "free_spins": 0}
    if n >= 3:
        n = min(n, 5)
        scatter["pay"] = SCATTER_PAY[n] * bet * lines
        scatter["free_spins"] = SCATTER_FREE_SPINS[n]
    bonuses = []
    for symbol, table in ((LEGAL_NAME, DOE_BONUS), (JUDGE_BOWS, JUDGE_BONUS)):
        best = max((w["count"] for w in wins if w["symbol"] == symbol), default=0)
        b = _line_bonus(symbol, best, bet, lines, table)
        if b:
            b["cells"] = [c for w in wins if w["symbol"] == symbol for c in w["cells"]]
            if free:
                b["pay"] *= FREE_SPIN_MULT
            bonuses.append(b)
    return wins, scatter, bonuses


def random_result():
    """Pick a random stop for each reel; returns (stop_indices, symbols[reel][row])."""
    idxs, rows = [], []
    for strip in STRIPS:
        i = random.randrange(len(strip))
        idxs.append(i)
        rows.append([strip[(i + r) % len(strip)] for r in range(3)])
    return idxs, rows


def simulate(spins=1_000_000, lines=10, bet=1):
    wagered = won = hits = fs_triggers = free_played = 0
    free_left = 0
    for _ in range(spins):
        free = free_left > 0
        if free:
            free_left -= 1
            free_played += 1
        else:
            wagered += lines * bet
        _, grid = random_result()
        wins, sc, bonuses = evaluate(grid, lines, bet, free)
        total = sum(w["pay"] for w in wins) + sc["pay"] + sum(b["pay"] for b in bonuses)
        won += total
        if total:
            hits += 1
        extra_fs = sc["free_spins"] + sum(b["free_spins"] for b in bonuses)
        if extra_fs:
            free_left += extra_fs
            fs_triggers += 1
    print(f"Spins (paid+free): {spins:,}   paid spins: {spins - free_played:,}")
    print(f"RTP: {won / wagered * 100:.2f}%")
    print(f"Hit frequency: {hits / spins * 100:.2f}%")
    print(f"Free-spin trigger: 1 in {spins / max(1, fs_triggers):.0f} spins")


# ---------------------------------------------------------------------------
# SAVE / LOAD
# ---------------------------------------------------------------------------
def default_save():
    return {"credits": START_CREDITS, "bet_idx": 1, "lines": 10, "sound": True,
            "turbo": False,
            "stats": {"spins": 0, "wagered": 0, "won": 0, "best": 0}}


def load_save():
    data = default_save()
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for k, v in loaded.items():
            if k == "stats" and isinstance(v, dict):
                data["stats"].update(v)
            elif k in data:
                data[k] = v
    except (OSError, ValueError):
        pass
    data["bet_idx"] = max(0, min(len(BET_OPTIONS) - 1, int(data["bet_idx"])))
    data["lines"] = max(1, min(MAX_LINES, int(data["lines"])))
    data["credits"] = max(0, int(data["credits"]))
    return data


def write_save(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------------
def vgrad(w, h, top, bottom, alpha=255):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        c = (int(top[0] + (bottom[0] - top[0]) * t),
             int(top[1] + (bottom[1] - top[1]) * t),
             int(top[2] + (bottom[2] - top[2]) * t), alpha)
        pygame.draw.line(s, c, (0, y), (w, y))
    return s


def radial(r, color):
    s = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
    for i in range(r, 0, -1):
        a = int(255 * (1 - i / r) ** 2)
        pygame.draw.circle(s, (*color, a), (r, r), i)
    return s


def ease_out_back(u, c1=1.4):
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def ease_out_cubic(u):
    return 1 - (1 - u) ** 3


def polyline_point(pts, f):
    """Point and direction at fraction f (0..1) along a polyline."""
    segs = [(pts[i], pts[i + 1], math.dist(pts[i], pts[i + 1])) for i in range(len(pts) - 1)]
    d = f * sum(l for _, _, l in segs)
    for a, b, l in segs:
        if d <= l:
            u = d / l if l else 0
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), (b[0] - a[0], b[1] - a[1])
        d -= l
    return pts[-1], (1, 0)


def polyline_slice(pts, f):
    """The part of the polyline from fraction f to the end."""
    start, _ = polyline_point(pts, f)
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    out, acc = [start], 0.0
    for i in range(len(pts) - 1):
        acc += math.dist(pts[i], pts[i + 1])
        if acc > f * total:
            out.append(pts[i + 1])
    return out


def fmt(n):
    return f"{int(n):,}"


def blit_center(dst, img, cx, cy):
    r = img.get_bounding_rect()
    if r.w == 0:
        return
    dst.blit(img, (cx - r.x - r.w // 2, cy - r.y - r.h // 2))


def outlined(font, text, fill, outline, thick):
    base = font.render(text, True, fill)
    w, h = base.get_size()
    surf = pygame.Surface((w + 2 * thick, h + 2 * thick), pygame.SRCALPHA)
    o = font.render(text, True, outline)
    for a in range(0, 360, 20):
        dx = int(round(math.cos(math.radians(a)) * thick))
        dy = int(round(math.sin(math.radians(a)) * thick))
        surf.blit(o, (thick + dx, thick + dy))
    surf.blit(base, (thick, thick))
    return surf


def draw_text(surf, text, font, color, pos, anchor="center", shadow=True, shadow_color=(0, 0, 0)):
    img = font.render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        sh = font.render(text, True, shadow_color)
        surf.blit(sh, rect.move(2, 3))
    surf.blit(img, rect)
    return rect


def deal_card():
    rank = random.choice(CARD_RANKS)
    suit = random.choice(CARD_SUITS)
    return {"rank": rank, "suit": suit, "color": "red" if suit in ("hearts", "diamonds") else "black"}


def draw_suit(s, suit, cx, cy, size, color):
    k = size
    if suit == "hearts":
        pygame.draw.circle(s, color, (int(cx - 0.28 * k), int(cy - 0.12 * k)), int(0.32 * k))
        pygame.draw.circle(s, color, (int(cx + 0.28 * k), int(cy - 0.12 * k)), int(0.32 * k))
        pygame.draw.polygon(s, color, [
            (cx - 0.58 * k, cy - 0.02 * k), (cx + 0.58 * k, cy - 0.02 * k), (cx, cy + 0.62 * k)])
    elif suit == "diamonds":
        pygame.draw.polygon(s, color, [
            (cx, cy - 0.62 * k), (cx + 0.42 * k, cy), (cx, cy + 0.62 * k), (cx - 0.42 * k, cy)])
    elif suit == "clubs":
        pygame.draw.circle(s, color, (int(cx), int(cy - 0.28 * k)), int(0.28 * k))
        pygame.draw.circle(s, color, (int(cx - 0.30 * k), int(cy + 0.08 * k)), int(0.28 * k))
        pygame.draw.circle(s, color, (int(cx + 0.30 * k), int(cy + 0.08 * k)), int(0.28 * k))
        pygame.draw.polygon(s, color, [
            (cx - 0.12 * k, cy), (cx + 0.12 * k, cy), (cx + 0.18 * k, cy + 0.62 * k),
            (cx - 0.18 * k, cy + 0.62 * k)])
    else:  # spades
        pygame.draw.polygon(s, color, [
            (cx, cy - 0.62 * k), (cx + 0.58 * k, cy + 0.08 * k), (cx - 0.58 * k, cy + 0.08 * k)])
        pygame.draw.circle(s, color, (int(cx - 0.26 * k), int(cy + 0.10 * k)), int(0.26 * k))
        pygame.draw.circle(s, color, (int(cx + 0.26 * k), int(cy + 0.10 * k)), int(0.26 * k))
        pygame.draw.polygon(s, color, [
            (cx - 0.12 * k, cy), (cx + 0.12 * k, cy), (cx + 0.18 * k, cy + 0.62 * k),
            (cx - 0.18 * k, cy + 0.62 * k)])


def draw_playing_card(s, rect, card, fonts):
    """Draw a face-up playing card. fonts = (rank_font, small_font) or a single font."""
    rank_font = fonts[0] if isinstance(fonts, tuple) else fonts
    pygame.draw.rect(s, WHITE, rect, border_radius=12)
    pygame.draw.rect(s, (40, 40, 50), rect, 3, border_radius=12)
    col = (200, 25, 40) if card["color"] == "red" else (22, 22, 28)
    pad = max(6, rect.w // 12)
    if rect.w < 36:
        pygame.draw.rect(s, col, rect.inflate(-8, -8), border_radius=6)
        return
    draw_text(s, card["rank"], rank_font, col, (rect.left + pad + 8, rect.top + pad + 10),
              shadow=False)
    draw_suit(s, card["suit"], rect.left + pad + 10, rect.top + pad + 36, max(8, rect.w * 0.12), col)
    draw_suit(s, card["suit"], rect.centerx, rect.centery + 8, rect.w * 0.22, col)
    # mirrored corner
    rx, ry = rect.right - pad - 8, rect.bottom - pad - 10
    img = rank_font.render(card["rank"], True, col)
    rot = pygame.transform.rotate(img, 180)
    s.blit(rot, rot.get_rect(center=(rx, ry)))
    draw_suit(s, card["suit"], rx, ry - 26, max(8, rect.w * 0.12), col)


def draw_chi_rho(s, cx, cy, k=1.0, color=(150, 30, 40), thick=8):
    """Chi Rho (☧): Chi (X) with Rho (P) sharing the vertical."""
    t = max(2, int(thick * k))

    def stroke(a, b):
        pygame.draw.line(s, color, a, b, t)
        pygame.draw.circle(s, color, (int(a[0]), int(a[1])), max(1, t // 2))
        pygame.draw.circle(s, color, (int(b[0]), int(b[1])), max(1, t // 2))

    stroke((cx - 40 * k, cy - 26 * k), (cx + 40 * k, cy + 38 * k))
    stroke((cx + 40 * k, cy - 26 * k), (cx - 40 * k, cy + 38 * k))
    stroke((cx, cy + 46 * k), (cx, cy - 50 * k))
    loop_cx, loop_cy, loop_r = cx, cy - 26 * k, 24 * k
    steps = 14
    for i in range(steps):
        a0 = -math.pi / 2 + i * math.pi / steps
        a1 = -math.pi / 2 + (i + 1) * math.pi / steps
        p0 = (loop_cx + math.cos(a0) * loop_r, loop_cy + math.sin(a0) * loop_r)
        p1 = (loop_cx + math.cos(a1) * loop_r, loop_cy + math.sin(a1) * loop_r)
        stroke(p0, p1)


# ---------------------------------------------------------------------------
# SOUND (synthesised - no files)
# ---------------------------------------------------------------------------
RATE = 22050


def _wave(kind, phase):
    if kind == "sine":
        return math.sin(phase)
    if kind == "tri":
        return 2 / math.pi * math.asin(math.sin(phase))
    if kind == "square":
        return 0.6 if math.sin(phase) >= 0 else -0.6
    if kind == "saw":
        return 2 * ((phase / (2 * math.pi)) % 1.0) - 1
    return 0.0


def synth(freq, dur, vol=0.4, kind="sine", f_end=None, attack=0.004, decay=6.0, noise=0.0):
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        t = i / RATE
        u = i / max(1, n - 1)
        f = freq if f_end is None else freq + (f_end - freq) * u
        phase += 2 * math.pi * f / RATE
        env = min(1.0, t / attack) * math.exp(-decay * u)
        s = _wave(kind, phase) * (1 - noise) + random.uniform(-1, 1) * noise
        out.append(s * env * vol)
    return out


def mix(parts):
    length = max(int(RATE * st) + len(buf) for st, buf in parts)
    out = [0.0] * length
    for st, buf in parts:
        off = int(RATE * st)
        for i, v in enumerate(buf):
            out[off + i] += v
    return out


class Sfx:
    def __init__(self):
        global RATE
        self.ok = False
        self.enabled = True
        self.snd = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            RATE, _fmt, self.channels = pygame.mixer.get_init()
            self.ok = True
        except pygame.error:
            return
        self._build()

    def _make(self, samples, volume=1.0):
        buf = array.array("h")
        for v in samples:
            v = max(-1.0, min(1.0, v))
            s = int(v * 32000)
            for _ in range(self.channels):
                buf.append(s)
        snd = pygame.mixer.Sound(buffer=buf.tobytes())
        snd.set_volume(volume)
        return snd

    def _build(self):
        notes = {"C5": 523, "E5": 659, "G5": 784, "C6": 1047, "E6": 1319, "G6": 1568}
        S = self.snd
        S["click"] = self._make(synth(900, 0.05, 0.25, "square", decay=8), 0.6)
        S["tick"] = self._make(synth(1500, 0.02, 0.2, "square", decay=6), 0.4)
        S["spin"] = self._make(mix([
            (0, synth(180, 0.45, 0.22, "saw", f_end=640, decay=2.2)),
            (0, synth(0, 0.45, 0.12, "sine", noise=1.0, decay=3)),
        ]), 0.7)
        S["stop"] = self._make(mix([
            (0, synth(140, 0.14, 0.7, "sine", f_end=55, decay=7)),
            (0, synth(0, 0.05, 0.3, "sine", noise=1.0, decay=9)),
        ]), 0.9)
        S["scatter"] = self._make(mix([
            (i * 0.07, synth(f, 0.3, 0.25, "sine", decay=4)) for i, f in
            enumerate([1319, 1568, 2093, 2637])]), 0.7)
        S["anticipate"] = self._make(synth(400, 0.6, 0.18, "tri", f_end=900, decay=1.5), 0.6)
        S["snip"] = self._make(mix([
            (0, synth(2600, 0.05, 0.3, "square", f_end=1400, decay=7, noise=0.4)),
            (0.11, synth(2600, 0.05, 0.3, "square", f_end=1400, decay=7, noise=0.4))]), 0.7)
        S["win_small"] = self._make(mix([
            (i * 0.09, synth(notes[n], 0.25, 0.3, "tri", decay=4))
            for i, n in enumerate(["C5", "E5", "G5"])]), 0.8)
        S["win_big"] = self._make(mix([
            (i * 0.1, synth(notes[n], 0.5, 0.28, "tri", decay=3))
            for i, n in enumerate(["C5", "E5", "G5", "C6", "E6", "G6", "C6", "G6"])] + [
            (0.8, synth(523, 1.0, 0.2, "sine", decay=2)),
            (0.8, synth(784, 1.0, 0.2, "sine", decay=2)),
            (0.8, synth(1047, 1.0, 0.2, "sine", decay=2))]), 0.9)
        S["coin"] = self._make(mix([
            (0, synth(1318, 0.12, 0.3, "square", decay=5)),
            (0.07, synth(1760, 0.3, 0.3, "square", decay=4))]), 0.5)
        S["lose"] = self._make(synth(330, 0.3, 0.25, "tri", f_end=200, decay=3), 0.7)
        S["free"] = self._make(mix([
            (i * 0.06, synth(440 * 2 ** (i / 6), 0.2, 0.25, "tri", decay=4)) for i in range(12)]), 0.8)
        S["gamble_win"] = self._make(mix([
            (0, synth(660, 0.15, 0.3, "tri")), (0.1, synth(990, 0.3, 0.3, "tri"))]), 0.8)
        S["gamble_lose"] = self._make(synth(300, 0.5, 0.3, "saw", f_end=90, decay=3), 0.7)
        self.music = self._make(self._casino_loop(), 0.38)
        pygame.mixer.set_reserved(1)
        self.music_ch = pygame.mixer.Channel(0)

    def _casino_loop(self):
        """Bouncy 8-bit casino-night loop (square lead, triangle bass, noise hats)."""
        bpm = 128
        beat = 60.0 / bpm
        beats = 32
        n = int(RATE * beat * beats)
        buf = [0.0] * n

        def blit(samples, t):
            off = int(t * RATE)
            for i, v in enumerate(samples):
                j = off + i
                if j >= n:
                    break
                buf[j] += v

        def hz(midi):
            return 440.0 * (2 ** ((midi - 69) / 12.0))

        # bass: C F G C | A F G C  (root + octave, quarters)
        bass_roots = [36, 36, 36, 36, 41, 41, 41, 41, 43, 43, 43, 43, 36, 36, 36, 36,
                      33, 33, 33, 33, 41, 41, 41, 41, 43, 43, 38, 38, 36, 36, 43, 36]
        for i, m in enumerate(bass_roots):
            blit(synth(hz(m), beat * 0.92, 0.22, "tri", decay=3.2), i * beat)
            blit(synth(hz(m + 12), beat * 0.55, 0.10, "tri", decay=4.0), i * beat)

        # off-beat chord stabs (Nintendo party bounce)
        chords = {
            36: (60, 64, 67), 41: (65, 69, 72), 43: (67, 71, 74),
            33: (57, 60, 64), 38: (62, 65, 69),
        }
        for i, m in enumerate(bass_roots):
            if i % 2 == 1:
                for note in chords.get(m, (60, 64, 67)):
                    blit(synth(hz(note), beat * 0.28, 0.07, "square", decay=7), i * beat)

        # melody — bouncy major-key casino hook
        melody = [
            (0.0, 72, 0.5), (0.5, 76, 0.5), (1.0, 79, 0.5), (1.5, 76, 0.5),
            (2.0, 72, 0.5), (2.5, 76, 0.5), (3.0, 79, 0.25), (3.25, 81, 0.25), (3.5, 84, 0.5),
            (4.0, 77, 0.5), (4.5, 81, 0.5), (5.0, 84, 0.5), (5.5, 81, 0.5),
            (6.0, 77, 0.5), (6.5, 72, 0.5), (7.0, 77, 0.25), (7.25, 81, 0.25), (7.5, 84, 0.5),
            (8.0, 79, 0.5), (8.5, 83, 0.5), (9.0, 86, 0.5), (9.5, 83, 0.5),
            (10.0, 79, 0.5), (10.5, 74, 0.5), (11.0, 71, 0.5), (11.5, 67, 0.5),
            (12.0, 72, 0.5), (12.5, 76, 0.5), (13.0, 79, 0.5), (13.5, 84, 0.5),
            (14.0, 79, 0.5), (14.5, 76, 0.5), (15.0, 72, 0.5), (15.5, 67, 0.5),
            (16.0, 76, 0.5), (16.5, 79, 0.5), (17.0, 84, 0.5), (17.5, 79, 0.5),
            (18.0, 76, 0.25), (18.25, 74, 0.25), (18.5, 72, 0.5), (19.0, 76, 0.5), (19.5, 79, 0.5),
            (20.0, 77, 0.5), (20.5, 81, 0.5), (21.0, 84, 0.25), (21.25, 86, 0.25), (21.5, 84, 0.5),
            (22.0, 81, 0.5), (22.5, 77, 0.5), (23.0, 72, 0.5), (23.5, 77, 0.5),
            (24.0, 79, 0.5), (24.5, 83, 0.5), (25.0, 86, 0.5), (25.5, 91, 0.5),
            (26.0, 86, 0.5), (26.5, 83, 0.5), (27.0, 79, 0.5), (27.5, 74, 0.5),
            (28.0, 72, 0.5), (28.5, 76, 0.5), (29.0, 79, 0.5), (29.5, 84, 0.5),
            (30.0, 79, 0.25), (30.25, 76, 0.25), (30.5, 72, 0.5), (31.0, 67, 0.5), (31.5, 72, 0.5),
        ]
        for t, midi, dur in melody:
            blit(synth(hz(midi), dur * beat * 0.92, 0.16, "square", decay=4.5, attack=0.004), t * beat)
            blit(synth(hz(midi + 12), dur * beat * 0.55, 0.05, "tri", decay=6.0), t * beat)

        # hats + kick
        for i in range(beats * 2):
            blit(synth(9000, 0.045, 0.045 if i % 2 == 0 else 0.07, "sine", noise=1.0, decay=16, attack=0.001),
                 i * beat * 0.5)
        for i in range(beats):
            if i % 2 == 0:
                blit(synth(90, 0.11, 0.18, "sine", f_end=42, decay=9), i * beat)
        return buf

    def play(self, name):
        if self.ok and self.enabled and name in self.snd:
            self.snd[name].play()

    def start_music(self):
        if not self.ok or not hasattr(self, "music"):
            return
        self.music_ch.play(self.music, loops=-1)
        if not self.enabled:
            self.music_ch.pause()

    def set_enabled(self, on):
        self.enabled = on
        if not self.ok or not hasattr(self, "music_ch"):
            return
        if on:
            if not self.music_ch.get_busy():
                self.music_ch.play(self.music, loops=-1)
            else:
                self.music_ch.unpause()
        else:
            self.music_ch.pause()


# ---------------------------------------------------------------------------
# SPRITES (all drawn procedurally at 2x then downscaled for anti-aliasing)
# ---------------------------------------------------------------------------
class Assets:
    U = 280  # drawing space for symbol glyphs

    def __init__(self):
        sysfont = pygame.font.SysFont
        self.f_title = sysfont(FONT_NAMES, 56)
        self.f_huge = sysfont(FONT_NAMES, 110)
        self.f_big = sysfont(FONT_NAMES, 44)
        self.f_med = sysfont(FONT_NAMES, 28)
        self.f_small = sysfont(FONT_NAMES, 20)
        self.f_tiny = sysfont(FONT_NAMES, 15)
        self._f_banner = sysfont(FONT_NAMES, 44)
        self._f_tag = sysfont(FONT_NAMES, 78)
        self._f_stamp = sysfont(FONT_NAMES, 55)
        self._f_lbl = sysfont(FONT_NAMES, 30)

        self.sprites, self.blurred = [], []
        borders = [(120, 130, 175)] * 4 + [(230, 170, 40)] * 2 + [(230, 60, 60)] * 2 \
            + [(255, 220, 80), (190, 90, 255)]
        glyphs = [self.g_id_illegal, self.g_legal_name_fraud, self.g_legal_name, self.g_judge_bows, self.g_scissors,
                  self.g_cut_cord, self.g_gold_10, self.g_unchained, self.g_wild, self.g_scatter]
        for sym in range(10):
            big = self.make_tile(borders[sym])
            glyphs[sym](big)
            spr = pygame.transform.smoothscale(big, (CELL, CELL))
            self.sprites.append(spr)
            small = pygame.transform.smoothscale(spr, (CELL, CELL // 9))
            blur = pygame.transform.smoothscale(small, (CELL, CELL))
            blur.set_alpha(215)
            self.blurred.append(blur)

        icon = pygame.Surface((280, 280), pygame.SRCALPHA)
        self.draw_scissors(icon, 140, 118, 1.0)
        bb = icon.get_bounding_rect()
        icon = icon.subsurface(bb).copy()
        self.scissor_icon = pygame.transform.smoothscale(icon, (max(1, int(bb.w * 64 / bb.h)), 64))
        img = self.f_huge.render("LEGAL NAME FRAUD", True, (225, 35, 45))
        img = img.subsurface(img.get_bounding_rect()).copy()
        st = pygame.Surface((img.get_width() + 50, img.get_height() + 40), pygame.SRCALPHA)
        st.blit(img, (25, 20))
        pygame.draw.rect(st, (225, 35, 45), st.get_rect(), 10, border_radius=14)
        pygame.draw.rect(st, (225, 35, 45), st.get_rect().inflate(-26, -26), 3, border_radius=10)
        self.stamp = pygame.transform.rotate(st, 12)

        # backgrounds, shading, glow
        self.bg = self.make_background(top=(16, 62, 48), bottom=(4, 14, 12))
        self.bg_free = self.make_background(top=(50, 12, 90), bottom=(8, 4, 20))
        self.reel_shade = self.make_reel_shade()
        self.cell_glow = self.make_cell_glow()
        self.bulb_glow = radial(16, (255, 220, 110))
        self.panel_bg = vgrad(W, H - PANEL_Y, (46, 18, 34), (14, 6, 14))

    # ----- backgrounds -----
    def make_background(self, top, bottom):
        bg = vgrad(W, H, top, bottom)
        lat = pygame.Surface((W, H), pygame.SRCALPHA)
        step = 70
        for x in range(-step, W + step, step):
            for y in range(-step, H + step, step):
                pts = [(x, y - step // 2), (x + step // 2, y), (x, y + step // 2), (x - step // 2, y)]
                pygame.draw.polygon(lat, (255, 255, 255, 9), pts, 1)
        bg.blit(lat, (0, 0))
        vig = pygame.Surface((64, 36), pygame.SRCALPHA)
        for yy in range(36):
            for xx in range(64):
                d = math.hypot((xx - 31.5) / 32, (yy - 17.5) / 18)
                vig.set_at((xx, yy), (0, 0, 0, int(min(1, max(0, d - 0.45)) * 200)))
        bg.blit(pygame.transform.smoothscale(vig, (W, H)), (0, 0))
        return bg.convert()

    def make_reel_shade(self):
        s = pygame.Surface((REEL_W, REEL_H), pygame.SRCALPHA)
        for y in range(70):
            a = int(170 * (1 - y / 70) ** 1.6)
            pygame.draw.line(s, (0, 0, 0, a), (0, y), (REEL_W, y))
            pygame.draw.line(s, (0, 0, 0, a), (0, REEL_H - 1 - y), (REEL_W, REEL_H - 1 - y))
        return s

    def make_cell_glow(self):
        pad = 18
        s = pygame.Surface((CELL + 2 * pad, CELL + 2 * pad), pygame.SRCALPHA)
        for i in range(pad, 0, -2):
            a = int(200 * (1 - i / pad) ** 1.5)
            pygame.draw.rect(s, (255, 225, 100, a), (pad - i, pad - i, CELL + 2 * i, CELL + 2 * i),
                             3, border_radius=16 + i)
        return s

    # ----- symbol tile -----
    def make_tile(self, border):
        U = self.U
        t = pygame.Surface((U, U), pygame.SRCALPHA)
        body = vgrad(256, 256, (58, 34, 74), (20, 10, 30))
        mask = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, 256, 256), border_radius=34)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        t.blit(body, (12, 12))
        gloss = pygame.Surface((236, 100), pygame.SRCALPHA)
        for y in range(100):
            pygame.draw.line(gloss, (255, 255, 255, int(55 * (1 - y / 100))), (0, y), (236, y))
        gm = pygame.Surface((236, 100), pygame.SRCALPHA)
        pygame.draw.rect(gm, (255, 255, 255, 255), (0, 0, 236, 100), border_radius=28)
        gloss.blit(gm, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        t.blit(gloss, (22, 18))
        pygame.draw.rect(t, border, (12, 12, 256, 256), 6, border_radius=34)
        return t

    # ----- glyph helpers -----
    def txt(self, s, text, font, color, center, maxw=None, outline=None, thick=2):
        img = outlined(font, text, color, outline, thick) if outline else font.render(text, True, color)
        bb = img.get_bounding_rect()
        if bb.w == 0:
            return
        img = img.subsurface(bb).copy()
        if maxw and img.get_width() > maxw:
            k = maxw / img.get_width()
            img = pygame.transform.smoothscale(img, (int(maxw), max(1, int(img.get_height() * k))))
        s.blit(img, img.get_rect(center=center))

    def banner(self, s, text, cy, fill=(200, 20, 40), fcol=WHITE, w=216, h=48):
        r = pygame.Rect(0, 0, w, h)
        r.center = (140, cy)
        pygame.draw.rect(s, fill, r, border_radius=12)
        pygame.draw.rect(s, GOLD, r, 5, border_radius=12)
        self.txt(s, text, self._f_banner, fcol, r.center, w - 26, outline=(30, 0, 10), thick=2)

    def stamp_text(self, s, text, font, color, angle, center, border=6):
        img = font.render(text, True, color)
        img = img.subsurface(img.get_bounding_rect()).copy()
        pad = 14
        surf = pygame.Surface((img.get_width() + 2 * pad, img.get_height() + 2 * pad), pygame.SRCALPHA)
        surf.blit(img, (pad, pad))
        pygame.draw.rect(surf, color, surf.get_rect(), border, border_radius=8)
        surf = pygame.transform.rotate(surf, angle)
        s.blit(surf, surf.get_rect(center=center))

    @staticmethod
    def taper(s, p0, p1, w0, w1, color, edge=None):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        pts = [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
               (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]
        pygame.draw.polygon(s, color, pts)
        if edge:
            pygame.draw.polygon(s, edge, pts, 3)

    def draw_scissors(self, s, cx, cy, k=1.0):
        def P(x, y):
            return (cx + x * k, cy + y * k)
        steel, edge, handle = (210, 215, 228), (80, 85, 105), (230, 60, 50)
        for sg in (-1, 1):                                   # handles + rings
            self.taper(s, P(0, 0), P(-sg * 52, 88), 16 * k, 13 * k, (170, 40, 40))
            c = P(-sg * 58, 114)
            pygame.draw.circle(s, (120, 20, 25), c, int(32 * k), max(1, int(15 * k)))
            pygame.draw.circle(s, handle, c, int(30 * k), max(1, int(11 * k)))
        for sg in (-1, 1):                                   # blades
            self.taper(s, P(0, 0), P(sg * 62, -100), 22 * k, 3 * k, steel, edge)
        pygame.draw.circle(s, (120, 85, 10), P(0, 0), int(15 * k))
        pygame.draw.circle(s, GOLD, P(0, 0), int(10 * k))

    # ----- glyphs -----
    def g_id_illegal(self, s):
        card = pygame.Rect(36, 44, 208, 140)
        pygame.draw.rect(s, (205, 214, 228), card, border_radius=12)
        pygame.draw.rect(s, (60, 90, 170), (36, 44, 208, 30), border_top_left_radius=12, border_top_right_radius=12)
        self.txt(s, "ID CARD", self._f_lbl, WHITE, (140, 59), 120)
        pygame.draw.rect(s, (70, 80, 110), card, 5, border_radius=12)
        pygame.draw.rect(s, (120, 140, 175), (52, 88, 64, 80), border_radius=6)
        pygame.draw.circle(s, (80, 95, 125), (84, 114), 15)
        pygame.draw.ellipse(s, (80, 95, 125), (60, 134, 48, 34))
        for i, w in enumerate((92, 76, 60)):
            pygame.draw.rect(s, (120, 130, 150), (128, 92 + i * 24, w, 11), border_radius=5)
        pygame.draw.line(s, (225, 30, 40), (56, 62), (224, 170), 16)
        pygame.draw.line(s, (225, 30, 40), (224, 62), (56, 170), 16)
        self.banner(s, "ID Illegal", 224)

    def g_legal_name_fraud(self, s):
        paper = pygame.Rect(40, 32, 200, 156)
        pygame.draw.rect(s, (246, 236, 202), paper, border_radius=6)
        pygame.draw.rect(s, (150, 110, 50), paper, 5, border_radius=6)
        pygame.draw.rect(s, (190, 150, 80), paper.inflate(-18, -18), 2, border_radius=4)
        self.txt(s, "BIRTH CERTIFICATE", self._f_lbl, (90, 60, 20), (140, 56), 150)
        for i, w in enumerate((140, 120, 140, 90)):
            pygame.draw.rect(s, (150, 140, 120), (70, 78 + i * 18, w, 8), border_radius=4)
        pygame.draw.circle(s, (180, 30, 40), (202, 160), 18)
        pygame.draw.circle(s, (230, 190, 70), (202, 160), 18, 4)
        self.stamp_text(s, "VOID", self._f_stamp, (215, 30, 40), 20, (140, 118))
        self.banner(s, "Legal Name Fraud", 224)

    def g_legal_name(self, s):
        tag = pygame.Rect(34, 24, 212, 158)
        pygame.draw.rect(s, WHITE, tag, border_radius=14)
        pygame.draw.rect(s, (200, 25, 40), (34, 24, 212, 40), border_top_left_radius=14, border_top_right_radius=14)
        self.txt(s, "LEGAL NAME", self._f_lbl, WHITE, (140, 44), 170)
        pygame.draw.rect(s, (40, 40, 40), tag, 5, border_radius=14)
        self.txt(s, "JANE", self._f_tag, (20, 20, 20), (140, 102), 170)
        self.txt(s, "DOE-755", self._f_tag, (20, 20, 20), (140, 154), 170)
        self.banner(s, "BONUS", 236, fill=(180, 20, 50), w=150, h=36)

    def g_judge_bows(self, s):
        pygame.draw.rect(s, (120, 70, 30), (112, 22, 56, 54), border_radius=18)
        pygame.draw.rect(s, (165, 105, 48), (118, 26, 18, 46), border_radius=8)
        pygame.draw.rect(s, (60, 40, 30), (84, 72, 112, 24), border_radius=6)
        pygame.draw.rect(s, (30, 20, 20), (92, 94, 96, 10), border_radius=4)
        self.stamp_text(s, "JUDGE BOWS", self._f_stamp, (225, 35, 45), 10, (140, 148), 5)
        self.banner(s, "BONUS", 236, fill=(150, 40, 20), w=150, h=36)

    def g_scissors(self, s):
        self.draw_scissors(s, 140, 124, 1.0)

    def g_cut_cord(self, s):
        rope, edge = (205, 165, 95), (110, 75, 30)
        for x0, x1 in ((26, 112), (168, 254)):
            r = pygame.Rect(x0, 128, x1 - x0, 34)
            pygame.draw.rect(s, edge, r.inflate(6, 6), border_radius=10)
            pygame.draw.rect(s, rope, r, border_radius=8)
            for x in range(x0 + 6, x1 - 6, 14):
                pygame.draw.line(s, edge, (x, 130), (x + 12, 160), 4)
        for fx, d in ((112, 1), (168, -1)):
            for i in range(5):
                y = 130 + i * 8
                pygame.draw.line(s, rope, (fx, y), (fx + d * (8 + (i % 3) * 5), y + (i - 2) * 3), 3)
        self.draw_scissors(s, 140, 74, 0.55)
        self.banner(s, "CUT CORD", 224, fill=(14, 14, 14), fcol=GOLD)

    def g_gold_10(self, s):
        rib = (170, 25, 35)
        pygame.draw.polygon(s, rib, [(98, 180), (140, 180), (116, 252), (98, 236), (78, 244)])
        pygame.draw.polygon(s, rib, [(140, 180), (182, 180), (202, 244), (182, 236), (164, 252)])
        pts = []
        for i in range(32):
            a = i * math.pi / 16
            r = 100 if i % 2 == 0 else 90
            pts.append((140 + r * math.cos(a), 116 + r * math.sin(a)))
        pygame.draw.polygon(s, (170, 120, 10), pts)
        pygame.draw.circle(s, (245, 195, 50), (140, 116), 80)
        pygame.draw.circle(s, (170, 120, 10), (140, 116), 68, 5)
        star = []
        for i in range(10):
            r = 54 if i % 2 == 0 else 24
            a = -math.pi / 2 + i * math.pi / 5
            star.append((140 + r * math.cos(a), 118 + r * math.sin(a)))
        pygame.draw.polygon(s, (255, 236, 140), star)
        pygame.draw.polygon(s, (170, 120, 10), star, 4)
        draw_chi_rho(s, 140, 118, 0.72, (150, 28, 38), 9)
        draw_chi_rho(s, 140, 118, 0.72, (90, 12, 18), 4)

    def g_unchained(self, s):
        gold, dark = (240, 190, 50), (130, 90, 10)
        for cx, ang in ((80, 28), (200, -28)):
            t = pygame.Surface((280, 280), pygame.SRCALPHA)
            r = pygame.Rect(0, 0, 100, 56)
            r.center = (140, 140)
            pygame.draw.rect(t, dark, r.inflate(8, 8), 18, border_radius=34)
            pygame.draw.rect(t, gold, r, 12, border_radius=30)
            t = pygame.transform.rotate(t, ang)
            s.blit(t, t.get_rect(center=(cx, 108)))
        for i in range(8):
            a = i * math.pi / 4 + 0.2
            r0, r1 = 12, 34 if i % 2 == 0 else 24
            pygame.draw.line(s, (255, 245, 150), (140 + r0 * math.cos(a), 108 + r0 * math.sin(a)),
                             (140 + r1 * math.cos(a), 108 + r1 * math.sin(a)), 6)
        self.banner(s, "UNCHAINED", 224, fill=(30, 110, 70))

    def g_wild(self, s):
        pts = []
        for i in range(32):
            a = i * math.pi / 16
            r = 102 if i % 2 == 0 else 84
            pts.append((140 + r * math.cos(a), 108 + r * math.sin(a)))
        pygame.draw.polygon(s, (170, 25, 35), pts)
        pygame.draw.circle(s, (130, 90, 10), (140, 108), 78)
        pygame.draw.circle(s, GOLD, (140, 108), 74)
        pygame.draw.circle(s, (255, 236, 140), (140, 108), 62)
        self.draw_scissors(s, 140, 104, 0.52)
        self.banner(s, "CRSSNOW", 224, w=232)

    def g_scatter(self, s):
        pygame.draw.circle(s, (60, 20, 110), (140, 108), 94)
        pygame.draw.circle(s, GOLD, (140, 108), 94, 7)
        pygame.draw.circle(s, (110, 50, 170), (140, 108), 78)
        pygame.draw.circle(s, (190, 130, 255), (140, 108), 78, 3)
        self.draw_scissors(s, 140, 104, 0.6)
        self.banner(s, "BCCRSS", 224, fill=(110, 40, 170))


# ---------------------------------------------------------------------------
# REEL
# ---------------------------------------------------------------------------
class Reel:
    """
    pos = float strip index shown at the top row. Decreasing pos scrolls DOWN.
    The symbol with absolute index k is drawn at y = (k - pos) * CELL.
    Before a reel lands we write the predetermined result into `override`, so
    stopping always takes the same (short) distance and the reels stop in order.
    """
    SLOPE = 1.4 + 3.0   # derivative of ease_out_back at u=0

    def __init__(self, strip):
        self.strip = strip
        self.n = len(strip)
        self.pos = float(random.randrange(self.n))
        self.state = "IDLE"      # IDLE WAIT SPIN APPROACH TWEEN STOPPED
        self.speed = 0.0
        self.vel = 0.0
        self.delay = 0.0
        self.override = {}
        self.target = 0
        self.approach = 3
        self.just_stopped = False
        self.p0 = self.t = self.dur = 0.0
        self.anticipate = False

    def sym(self, k):
        return self.override.get(k, self.strip[k % self.n])

    def start(self, delay):
        self.state = "WAIT"
        self.delay = delay
        self.speed = 0.0

    def request_stop(self, rows, quick=False):
        if self.state == "WAIT":
            self.state = "SPIN"
            self.speed = max(self.speed, 20.0)
        margin = 2 if quick else 6
        self.approach = 1 if quick else 3
        self.target = math.floor(self.pos) - margin
        for r in range(3):
            self.override[self.target + r] = rows[r]
        self.state = "APPROACH"

    def update(self, dt, vmax):
        prev = self.pos
        if self.state == "WAIT":
            self.delay -= dt
            if self.delay <= 0:
                self.state = "SPIN"
                self.speed = -4.0           # little wind-up (moves up first)
        elif self.state in ("SPIN", "APPROACH"):
            self.speed = min(vmax, self.speed + 150 * dt)
            self.pos -= self.speed * dt
            if self.state == "APPROACH" and self.pos <= self.target + self.approach:
                self.state = "TWEEN"
                self.p0, self.t = self.pos, 0.0
                dist = max(0.5, self.p0 - self.target)
                self.dur = max(0.22, min(0.7, self.SLOPE * dist / max(8.0, self.speed)))
        elif self.state == "TWEEN":
            self.t += dt
            u = min(1.0, self.t / self.dur)
            self.pos = self.p0 + (self.target - self.p0) * ease_out_back(u)
            if u >= 1.0:
                self.pos = float(self.target)
                self.state = "STOPPED"
                self.just_stopped = True
                self.speed = 0.0
        self.vel = (prev - self.pos) / dt if dt > 0 else 0.0
        top = math.floor(self.pos) + 4
        for k in [k for k in self.override if k > top]:
            del self.override[k]

    @property
    def moving(self):
        return self.state in ("WAIT", "SPIN", "APPROACH", "TWEEN")


# ---------------------------------------------------------------------------
# UI WIDGETS & PARTICLES
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label, cb, font, enabled=None, active=None, visible=None,
                 color=(78, 34, 70), kind="rect", label_fn=None):
        self.rect = pygame.Rect(rect)
        self.label, self.cb, self.font = label, cb, font
        self.enabled = enabled or (lambda: True)
        self.active = active or (lambda: False)
        self.visible = visible or (lambda: True)
        self.color, self.kind, self.label_fn = color, kind, label_fn

    def hit(self, pos):
        if not self.visible() or not self.enabled():
            return False
        if self.kind == "round":
            c = self.rect.center
            return math.hypot(pos[0] - c[0], pos[1] - c[1]) <= self.rect.w / 2
        return self.rect.collidepoint(pos)

    def draw(self, s, mouse, down):
        if not self.visible():
            return
        en, act = self.enabled(), self.active()
        hover = en and (self.hit(mouse))
        pressed = hover and down
        base = (60, 200, 90) if (act and self.kind == "rect") else self.color
        if self.kind == "round":
            base = (40, 190, 80) if en else (70, 70, 70)
        if not en:
            base = (50, 40, 50)
        col = tuple(min(255, int(c * (1.25 if hover else 1.0))) for c in base)
        r = self.rect.move(0, 2 if pressed else 0)
        text_col = WHITE if en else (120, 110, 120)
        label = self.label_fn() if self.label_fn else self.label
        if self.kind == "round":
            c = r.center
            pygame.draw.circle(s, (0, 0, 0), (c[0] + 3, c[1] + 5), r.w // 2)
            pygame.draw.circle(s, (160, 110, 20), c, r.w // 2)
            pygame.draw.circle(s, col, c, r.w // 2 - 6)
            pygame.draw.circle(s, tuple(min(255, v + 50) for v in col), (c[0], c[1] - 8), r.w // 2 - 22, 0)
            pygame.draw.circle(s, col, (c[0], c[1] + 4), r.w // 2 - 20)
            lines = label.split("\n")
            for i, ln in enumerate(lines):
                y = c[1] + (i - (len(lines) - 1) / 2) * 30 + 2
                draw_text(s, ln, self.font, text_col, (c[0], y))
        else:
            pygame.draw.rect(s, (0, 0, 0), r.move(0, 3), border_radius=10)
            pygame.draw.rect(s, col, r, border_radius=10)
            pygame.draw.rect(s, GOLD_D if en else (80, 70, 70), r, 2, border_radius=10)
            draw_text(s, label, self.font, text_col, r.center, shadow=en)


class Coin:
    def __init__(self, x, y, spread=1.0):
        a = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = random.uniform(250, 760) * spread
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.size = random.randint(9, 17)
        self.ph = random.random() * 6.28
        self.spin = random.uniform(7, 15)

    def update(self, dt):
        self.vy += 1500 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ph += self.spin * dt

    def draw(self, s):
        w = max(3, int(abs(math.cos(self.ph)) * self.size * 2))
        h = self.size * 2
        pygame.draw.ellipse(s, (170, 115, 10), (self.x - w / 2, self.y - h / 2, w, h))
        pygame.draw.ellipse(s, (255, 214, 70), (self.x - w / 2 + 2, self.y - h / 2 + 2, max(1, w - 4), h - 4))
        if w > 10:
            pygame.draw.ellipse(s, (255, 240, 160), (self.x - w / 4, self.y - h / 4, w / 2, h / 2), 2)


# ---------------------------------------------------------------------------
# THE GAME
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((W, H)).convert()
        self.clock = pygame.time.Clock()
        self.A = Assets()
        self.sfx = Sfx()
        self.save = load_save()
        self.credits = self.save["credits"]
        self.bet_idx = self.save["bet_idx"]
        self.lines = self.save["lines"]
        self.turbo = bool(self.save["turbo"])
        self.sfx.set_enabled(bool(self.save["sound"]))
        self.stats = self.save["stats"]

        self.reels = [Reel(STRIPS[i]) for i in range(5)]
        self.state = "TITLE"      # TITLE IDLE SPIN RESULT BIGWIN GAMBLE
        self.time = 0.0
        self.mouse_down = False
        self.paytable_open = False
        self.auto = False
        self.auto_t = None
        self.free_spins = 0
        self.fs_active = False
        self.fs_total = 0
        self.spin_is_free = False
        self.spin_bet = self.spin_lines = 0
        self.spin_total_bet = 0
        self.spin_t = 0.0
        self.stop_at = [0] * 5
        self.results = [[0] * 3 for _ in range(5)]
        self.win_entries = []
        self.scatter_info = None
        self.last_win = 0
        self.present_t = 0.0
        self.banner = None
        self.pending_banner = None
        self.pending_delay = 1.0
        self.flash = None
        self.gamble = None
        self.bigwin = None
        self.particles = []
        self.shake = 0.0
        self.lever_t = 9.0
        self.lever_rect = pygame.Rect(1080, 140, 190, 340)
        self.shown_credits = float(self.credits)
        self.shown_win = 0.0
        self.msg_override = None
        self.overlay = pygame.Surface((REEL_W, REEL_H), pygame.SRCALPHA)
        self.frame_rect = pygame.Rect(RX - 18, RY - 18, REEL_W + 36, REEL_H + 36)
        self.bulbs = self.make_bulbs()
        self.build_ui()
        self.clamp_bet()
        self.sfx.start_music()

    # ------------------------------------------------------------------ setup
    @property
    def bet(self):
        return BET_OPTIONS[self.bet_idx]

    @property
    def total_bet(self):
        return self.bet * self.lines

    @property
    def broke(self):
        return (self.state in ("IDLE", "RESULT") and self.credits < 1
                and self.free_spins == 0 and not self.fs_active)

    @property
    def can_edit_bet(self):
        return self.state in ("IDLE", "RESULT") and self.free_spins == 0

    def make_bulbs(self):
        r = self.frame_rect.inflate(30, 30)
        pts, step = [], 30
        x = r.left
        while x < r.right:
            pts.append((x, r.top))
            x += step
        y = r.top
        while y < r.bottom:
            pts.append((r.right, y))
            y += step
        x = r.right
        while x > r.left:
            pts.append((x, r.bottom))
            x -= step
        y = r.bottom
        while y > r.top:
            pts.append((r.left, y))
            y -= step
        return pts

    def build_ui(self):
        A = self.A
        S = self
        self.buttons = [
            Button((24, 16, 120, 34), "", self.toggle_sound, A.f_small,
                   label_fn=lambda: "SOUND ON" if S.sfx.enabled else "SOUND OFF"),
            Button((24, 180, 130, 34), "PAYTABLE", self.toggle_paytable, A.f_small),
            Button((430, 632, 44, 44), "-", lambda: self.change_bet(-1), A.f_big, enabled=lambda: S.can_edit_bet),
            Button((546, 632, 44, 44), "+", lambda: self.change_bet(1), A.f_big, enabled=lambda: S.can_edit_bet),
            Button((604, 632, 44, 44), "-", lambda: self.change_lines(-1), A.f_big, enabled=lambda: S.can_edit_bet),
            Button((720, 632, 44, 44), "+", lambda: self.change_lines(1), A.f_big, enabled=lambda: S.can_edit_bet),
            Button((778, 668, 160, 34), "MAX BET", self.max_bet, A.f_small,
                   enabled=lambda: S.can_edit_bet and S.credits > 0, color=(150, 40, 40)),
            Button((950, 618, 110, 40), "AUTO", self.toggle_auto, A.f_med, active=lambda: S.auto),
            Button((950, 666, 110, 40), "TURBO", self.toggle_turbo, A.f_med, active=lambda: S.turbo),
            Button((1106, 588, 128, 128), "SPIN", self.on_spin, A.f_big, kind="round",
                   enabled=lambda: S.state in ("IDLE", "RESULT", "SPIN", "BIGWIN") and not S.broke,
                   label_fn=self.spin_label),
            Button((1030, 524, 220, 40), "GAMBLE  (G)", self.start_gamble, A.f_small,
                   visible=lambda: S.can_gamble(), color=(140, 60, 160)),
        ]
        can_pick = lambda: S.gamble is not None and S.gamble["phase"] == "choose"
        self.gamble_buttons = [
            Button((430, 520, 200, 56), "RED  (R)", lambda: self.gamble_pick("red"), A.f_med, enabled=can_pick, color=(170, 25, 40)),
            Button((650, 520, 200, 56), "BLACK  (B)", lambda: self.gamble_pick("black"), A.f_med, enabled=can_pick, color=(30, 30, 40)),
            Button((545, 596, 190, 50), "COLLECT  (C)", self.gamble_collect, A.f_med, enabled=can_pick, color=(40, 140, 70)),
        ]
        self.reset_button = Button((470, 440, 340, 60), "LEGAL NAME IS FRAUD", self.reset_credits, A.f_med,
                                   color=(40, 140, 70))
        self.title_play = Button((W // 2 - 150, 530, 300, 70), "PLAY", self.begin_play, A.f_big,
                                 color=(40, 150, 70))

    def spin_label(self):
        if self.state == "SPIN":
            return "STOP"
        if self.state == "BIGWIN":
            return "SKIP"
        return "FREE\nSPIN" if self.free_spins > 0 else "SPIN"

    # --------------------------------------------------------------- settings
    def persist(self):
        self.save.update(credits=self.credits, bet_idx=self.bet_idx, lines=self.lines,
                         sound=self.sfx.enabled, turbo=self.turbo)
        write_save(self.save)

    def toggle_sound(self):
        self.sfx.set_enabled(not self.sfx.enabled)
        self.sfx.play("click")
        self.persist()

    def begin_play(self):
        if self.state != "TITLE":
            return
        self.state = "IDLE"
        self.sfx.play("coin")
        self.emit_coins(40, W // 2, 280)

    def toggle_turbo(self):
        self.turbo = not self.turbo
        self.sfx.play("click")
        self.persist()

    def toggle_auto(self):
        self.auto = not self.auto
        self.sfx.play("click")
        if self.auto and self.state in ("IDLE", "RESULT") and self.auto_t is None:
            self.auto_t = 0.3
        if not self.auto and self.free_spins == 0:
            self.auto_t = None

    def toggle_paytable(self):
        self.paytable_open = not self.paytable_open
        self.sfx.play("click")

    def change_bet(self, d):
        if not self.can_edit_bet:
            return
        new = max(0, min(len(BET_OPTIONS) - 1, self.bet_idx + d))
        if BET_OPTIONS[new] * self.lines > self.credits and d > 0:
            self.set_flash("NOT ENOUGH CREDITS", RED)
            return
        self.bet_idx = new
        self.sfx.play("click")
        self.persist()

    def change_lines(self, d):
        if not self.can_edit_bet:
            return
        new = max(1, min(MAX_LINES, self.lines + d))
        if self.bet * new > self.credits and d > 0:
            self.set_flash("NOT ENOUGH CREDITS", RED)
            return
        self.lines = new
        self.sfx.play("click")
        self.persist()

    def max_bet(self):
        if not self.can_edit_bet or self.credits < 1:
            return
        self.lines = MAX_LINES if self.credits >= MAX_LINES else max(1, self.credits)
        self.bet_idx = 0
        for i, b in enumerate(BET_OPTIONS):
            if b * self.lines <= self.credits:
                self.bet_idx = i
        self.sfx.play("click")
        self.persist()
        self.start_spin()

    def clamp_bet(self):
        changed = False
        while self.total_bet > self.credits and (self.bet_idx > 0 or self.lines > 1):
            if self.bet_idx > 0:
                self.bet_idx -= 1
            else:
                self.lines -= 1
            changed = True
        if changed and self.credits >= 1:
            self.set_flash("BET LOWERED TO FIT YOUR CREDITS", GOLD)

    def reset_credits(self):
        if not self.broke:
            return
        self.credits = START_CREDITS
        self.shown_credits = 0.0
        self.bet_idx, self.lines = 1, 10
        self.auto = False
        self.sfx.play("coin")
        self.persist()

    def set_flash(self, text, color=WHITE, dur=2.0):
        self.flash = [text, color, dur]

    # ------------------------------------------------------------------ spin
    def on_spin(self):
        if self.paytable_open or self.state == "GAMBLE":
            return
        if self.state in ("IDLE", "RESULT"):
            self.start_spin()
        elif self.state == "SPIN":
            self.quick_stop()
        elif self.state == "BIGWIN":
            self.skip_bigwin()

    def start_spin(self):
        free = self.free_spins > 0
        if not free and self.credits < self.total_bet:
            self.set_flash("NOT ENOUGH CREDITS - LOWER YOUR BET", RED)
            self.sfx.play("lose")
            self.auto = False
            self.auto_t = None
            return
        self.auto_t = None
        self.banner = None
        self.spin_is_free = free
        self.spin_bet, self.spin_lines = self.bet, self.lines
        self.spin_total_bet = self.total_bet
        if free:
            self.free_spins -= 1
        else:
            self.credits -= self.total_bet
            self.stats["wagered"] += self.total_bet
        self.stats["spins"] += 1
        self.last_win = 0
        self.win_entries = []
        self.scatter_info = None
        self.state = "SPIN"
        self.spin_t = 0.0
        idxs, self.results = random_result()
        first, gap = (0.25, 0.12) if self.turbo else (0.7, 0.35)
        t, self.stop_at = first, []
        for i in range(5):
            if i > 0:
                t += gap
            before = sum(1 for j in range(i) if SCATTER in self.results[j])
            self.reels[i].anticipate = False
            if before >= 2 and i >= 2 and not self.turbo:
                t += 0.8
                self.reels[i].anticipate = True
            self.stop_at.append(t)
        for i, r in enumerate(self.reels):
            r.start(i * 0.07)
        self.sfx.play("spin")
        self.lever_t = 0.0
        self.persist()

    def quick_stop(self):
        for i, r in enumerate(self.reels):
            if r.state in ("WAIT", "SPIN"):
                r.request_stop(self.results[i], quick=True)
                r.anticipate = False

    def on_reel_stop(self, i):
        self.sfx.play("stop")
        if SCATTER in self.results[i]:
            self.sfx.play("scatter")

    def finish_spin(self):
        grid = [[self.reels[r].sym(self.reels[r].target + row) for row in range(3)] for r in range(5)]
        wins, sc, bonuses = evaluate(grid, self.spin_lines, self.spin_bet, self.spin_is_free)
        total = sum(w["pay"] for w in wins) + sc["pay"] + sum(b["pay"] for b in bonuses)
        self.credits += total
        self.last_win = total
        self.stats["won"] += total
        self.stats["best"] = max(self.stats["best"], total)
        self.win_entries = wins + ([sc] if sc["count"] >= 3 else []) + bonuses
        self.scatter_info = sc
        self.present_t = 0.0
        self.shown_win = 0.0

        banner = None
        delay = 0.5
        extra_fs = sc["free_spins"] + sum(b["free_spins"] for b in bonuses)
        if extra_fs:
            first = not self.fs_active
            if first:
                self.fs_active = True
                self.fs_total = 0
            self.free_spins += extra_fs
            if sc["free_spins"]:
                title = "BCCRSS BONUS!" if first else "RETRIGGER!"
                sub = f"+{extra_fs} FREE SPINS - WINS x{FREE_SPIN_MULT}"
                color = PURPLE
            else:
                best = max(bonuses, key=lambda b: (b["free_spins"], b["pay"]))
                title = best["title"] if first else "RETRIGGER!"
                sub = f"{best['sub']}  -  WINS x{FREE_SPIN_MULT}"
                color = GOLD
            banner = {"title": title, "sub": sub, "t": 0.0, "dur": 3.0, "color": color}
            self.sfx.play("free")
            delay = 3.6
        elif bonuses:
            best = max(bonuses, key=lambda b: b["pay"])
            banner = {"title": best["title"], "sub": f"{best['sub']}   +{fmt(sum(b['pay'] for b in bonuses))}",
                      "t": 0.0, "dur": 2.4, "color": GOLD}
            delay = 2.6
        if self.spin_is_free:
            self.fs_total += total
            if self.free_spins == 0:
                self.fs_active = False
                banner = {"title": "BONUS COMPLETE", "sub": f"TOTAL WIN  {fmt(self.fs_total)}",
                          "t": 0.0, "dur": 3.4, "color": GOLD}
                delay = 4.0
            elif not extra_fs:
                delay = 2.0 if total else 1.0

        if total >= 10 * self.spin_total_bet:
            self.start_bigwin(total)
            self.pending_banner = banner
            self.auto_t = None
            self.pending_delay = delay
        else:
            self.state = "RESULT"
            if total:
                self.sfx.play("snip")
                self.sfx.play("win_small")
                self.emit_coins(min(60, 10 + int(total / max(1, self.spin_total_bet) * 4)))
                delay = max(delay, 2.0)
            elif not banner:
                self.sfx.play("lose") if not self.spin_is_free else None
            self.banner = banner
            self.schedule_next(delay)
        self.clamp_bet()
        self.persist()

    def schedule_next(self, delay):
        self.auto_t = delay if (self.free_spins > 0 or self.auto) else None

    # --------------------------------------------------------------- big win
    def start_bigwin(self, total):
        mult = total / max(1, self.spin_total_bet)
        if mult >= 100:
            name, dur = "CRSSNOW!", 6.0
        elif mult >= 50:
            name, dur = "NO LEGAL NAME!", 5.0
        elif mult >= 25:
            name, dur = "TIES SEVERED!", 4.0
        else:
            name, dur = "CORD CUT!", 3.0
        self.bigwin = {"target": total, "name": name, "dur": dur, "t": 0.0, "hold": 0.0,
                       "next_coin": 0.0, "last_tick": 0.0}
        self.state = "BIGWIN"
        self.shake = 0.5
        self.sfx.play("win_big")

    def skip_bigwin(self):
        b = self.bigwin
        if not b:
            return
        if b["t"] < b["dur"]:
            b["t"] = b["dur"]
        else:
            b["hold"] = 99

    def end_bigwin(self):
        self.bigwin = None
        self.state = "RESULT"
        self.banner = self.pending_banner
        self.pending_banner = None
        self.shown_win = float(self.last_win)
        self.schedule_next(max(self.pending_delay, 1.0))

    # ---------------------------------------------------------------- gamble
    def can_gamble(self):
        return (self.state == "RESULT" and self.last_win > 0 and self.free_spins == 0
                and not self.fs_active and not self.paytable_open and self.gamble is None)

    def start_gamble(self):
        if not self.can_gamble():
            return
        self.credits -= self.last_win           # the win is now at risk
        self.gamble = {"stake": self.last_win, "rounds": 0, "hist": [], "phase": "choose",
                       "t": 0.0, "outcome": None, "pick": None}
        self.state = "GAMBLE"
        self.auto = False
        self.auto_t = None
        self.sfx.play("click")

    def gamble_pick(self, color):
        g = self.gamble
        if self.state != "GAMBLE" or g["phase"] != "choose":
            return
        g["pick"] = color
        g["card"] = deal_card()
        g["outcome"] = g["card"]["color"]
        g["phase"] = "flip"
        g["t"] = 0.0
        self.sfx.play("click")

    def gamble_collect(self):
        g = self.gamble
        if self.state != "GAMBLE" or g["phase"] != "choose":
            return
        self.credits += g["stake"]
        self.last_win = g["stake"]
        self.stats["best"] = max(self.stats["best"], self.last_win)
        self.end_gamble(coins=True)

    def end_gamble(self, coins=False):
        if coins:
            self.sfx.play("coin")
            self.emit_coins(30)
        self.gamble = None
        self.state = "IDLE"
        self.win_entries = []
        self.shown_win = float(self.last_win)
        self.clamp_bet()
        self.persist()

    def update_gamble(self, dt):
        g = self.gamble
        g["t"] += dt
        if g["phase"] == "flip" and g["t"] >= 0.9:
            g["phase"], g["t"] = "reveal", 0.0
            won = g["outcome"] == g["pick"]
            g["won"] = won
            if won:
                g["stake"] *= 2
                g["rounds"] += 1
                g["hist"].append(g["card"])
                self.sfx.play("gamble_win")
            else:
                g["stake"] = 0
                g["hist"].append(g["card"])
                self.sfx.play("gamble_lose")
        elif g["phase"] == "reveal" and g["t"] >= 1.0:
            if not g["won"]:
                self.last_win = 0
                self.end_gamble()
            elif g["rounds"] >= 5:
                self.credits += g["stake"]
                self.last_win = g["stake"]
                self.stats["best"] = max(self.stats["best"], self.last_win)
                self.end_gamble(coins=True)
            else:
                g["phase"], g["t"] = "choose", 0.0

    # ------------------------------------------------------------- particles
    def emit_coins(self, n, x=None, y=None):
        for _ in range(n):
            self.particles.append(Coin(x if x is not None else random.randint(RX, RX + REEL_W),
                                       y if y is not None else RY + REEL_H * 0.6))
        del self.particles[:-350]

    # ---------------------------------------------------------------- update
    def update(self, dt):
        self.time += dt
        vmax = 44.0 if self.turbo else 30.0
        for r in self.reels:
            r.update(dt, vmax)
        self.shake = max(0.0, self.shake - dt)
        self.lever_t += dt

        if self.state == "SPIN":
            self.spin_t += dt
            for i, r in enumerate(self.reels):
                if r.state in ("WAIT", "SPIN") and self.spin_t >= self.stop_at[i]:
                    r.request_stop(self.results[i])
                    if r.anticipate:
                        self.sfx.play("anticipate")
                if r.just_stopped:
                    r.just_stopped = False
                    r.anticipate = False
                    self.on_reel_stop(i)
            if all(r.state == "STOPPED" for r in self.reels):
                self.finish_spin()
        elif self.state == "RESULT":
            self.present_t += dt
        elif self.state == "BIGWIN":
            self.update_bigwin(dt)
        elif self.state == "GAMBLE":
            self.update_gamble(dt)

        # automatic next spin (auto-play / free spins)
        if self.auto_t is not None and self.state in ("IDLE", "RESULT") and not self.paytable_open:
            self.auto_t -= dt
            if self.auto_t <= 0:
                self.auto_t = None
                if self.free_spins > 0 or (self.auto and self.credits >= self.total_bet):
                    self.start_spin()
                else:
                    self.auto = False

        if self.banner:
            self.banner["t"] += dt
            if self.banner["t"] >= self.banner["dur"]:
                self.banner = None
        if self.flash:
            self.flash[2] -= dt
            if self.flash[2] <= 0:
                self.flash = None

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.y < H + 40]

        # smooth counters
        target = self.credits
        if self.state == "BIGWIN" and self.bigwin:
            target = self.credits - self.bigwin["target"] + int(self.shown_win)
        diff = target - self.shown_credits
        step = max(1.0, abs(diff) * dt * 6)
        self.shown_credits = target if abs(diff) <= step else self.shown_credits + math.copysign(step, diff)
        wt = self.last_win if self.state != "BIGWIN" else self.shown_win
        if self.state != "BIGWIN":
            d = wt - self.shown_win
            s2 = max(1.0, abs(d) * dt * 5)
            self.shown_win = wt if abs(d) <= s2 else self.shown_win + math.copysign(s2, d)

    def update_bigwin(self, dt):
        b = self.bigwin
        b["t"] += dt
        u = min(1.0, b["t"] / b["dur"])
        self.shown_win = b["target"] * ease_out_cubic(u)
        if u < 1.0:
            b["next_coin"] -= dt
            if b["next_coin"] <= 0:
                b["next_coin"] = 0.035
                self.emit_coins(4, random.randint(200, 1080), RY + REEL_H + 60)
            b["last_tick"] -= dt
            if b["last_tick"] <= 0:
                b["last_tick"] = 0.07
                self.sfx.play("tick")
        else:
            self.shown_win = b["target"]
            b["hold"] += dt
            if b["hold"] >= 1.6:
                self.end_bigwin()

    # ---------------------------------------------------------------- events
    def handle(self, e):
        if e.type == pygame.QUIT:
            self.quit()
        elif e.type == pygame.KEYDOWN:
            self.on_key(e.key)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.mouse_down = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse_down = False
            self.on_click(e.pos)

    def on_click(self, pos):
        if self.state == "TITLE":
            if self.buttons[0].hit(pos):
                self.buttons[0].cb()
            elif self.title_play.hit(pos):
                self.title_play.cb()
            return
        if self.paytable_open:
            self.paytable_open = False
            return
        if self.broke:
            if self.reset_button.hit(pos):
                self.reset_button.cb()
            return
        if self.state == "GAMBLE":
            for b in self.gamble_buttons:
                if b.hit(pos):
                    b.cb()
                    return
            return
        if self.state == "BIGWIN":
            self.skip_bigwin()
            return
        for b in self.buttons:
            if b.hit(pos):
                b.cb()
                return
        if self.lever_rect.collidepoint(pos) and self.state in ("IDLE", "RESULT"):
            self.on_spin()

    def on_key(self, key):
        K = pygame
        if key == K.K_ESCAPE:
            if self.paytable_open:
                self.paytable_open = False
            else:
                self.quit()
            return
        if key == K.K_F11:
            pygame.display.toggle_fullscreen()
            return
        if self.state == "TITLE":
            if key == K.K_s:
                self.toggle_sound()
            elif key in (K.K_SPACE, K.K_RETURN):
                self.begin_play()
            return
        if key == K.K_p and self.state != "SPIN":
            self.toggle_paytable()
            return
        if self.paytable_open:
            return
        if key == K.K_s:
            self.toggle_sound()
        if self.state == "GAMBLE":
            if key == K.K_r:
                self.gamble_pick("red")
            elif key == K.K_b:
                self.gamble_pick("black")
            elif key in (K.K_c, K.K_SPACE, K.K_RETURN):
                self.gamble_collect()
            return
        if self.broke:
            if key == K.K_r:
                self.reset_credits()
            return
        if key in (K.K_SPACE, K.K_RETURN):
            self.on_spin()
        elif key == K.K_UP:
            self.change_bet(1)
        elif key == K.K_DOWN:
            self.change_bet(-1)
        elif key == K.K_RIGHT:
            self.change_lines(1)
        elif key == K.K_LEFT:
            self.change_lines(-1)
        elif key == K.K_m:
            self.max_bet()
        elif key == K.K_a:
            self.toggle_auto()
        elif key == K.K_t:
            self.toggle_turbo()
        elif key == K.K_g:
            self.start_gamble()

    def quit(self):
        if self.state == "GAMBLE" and self.gamble:
            self.credits += self.gamble["stake"]      # don't lose a pending gamble stake
        self.persist()
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------ draw
    def current_message(self):
        if self.flash:
            return self.flash[0], self.flash[1]
        if self.state == "BIGWIN":
            return f"CORD CUT!  +{fmt(self.last_win)}", GOLD
        if self.state == "SPIN":
            return ("BCCRSS BONUS - CUT FREE!" if self.spin_is_free else "VERIFYING NO ID..."), WHITE
        if self.state == "RESULT" and self.win_entries:
            if self.present_t < 1.6 or len(self.win_entries) == 1 and self.present_t < 1.6:
                return f"CORD CUT!  +{fmt(self.last_win)}", GOLD
            e = self.win_entries[int((self.present_t - 1.6) // 1.3) % len(self.win_entries)]
            if e["kind"] == "line":
                return (f"LINE {e['line'] + 1}:  {e['count']} x {SYMBOL_NAMES[e['symbol']]}  "
                        f"PAYS {fmt(e['pay'])}"), LINE_COLORS[e["line"]]
            if e["kind"] == "bonus":
                txt = f"{e['title']}:  {e['count']} x {SYMBOL_NAMES[e['symbol']]}  PAYS {fmt(e['pay'])}"
                if e["free_spins"]:
                    txt += f"  +  {e['free_spins']} FREE SPINS"
                return txt, GOLD
            txt = f"{e['count']} BCCRSS PAY {fmt(e['pay'])}"
            if e["free_spins"]:
                txt += f"  +  {e['free_spins']} FREE SPINS"
            return txt, (220, 160, 255)
        if self.state == "RESULT" and self.last_win == 0 and self.stats["spins"]:
            return "ID IS ILLEGAL - NO WIN", (200, 190, 210)
        if self.free_spins > 0:
            return f"{self.free_spins} CORD-CUT SPINS REMAINING", (220, 160, 255)
        return "PLACE YOUR BET AND PULL THE ONE-ARMED BANDIT!", (230, 220, 240)

    def highlighted_cells(self):
        if self.state not in ("RESULT", "BIGWIN") or not self.win_entries:
            return [], None
        if self.state == "BIGWIN" or self.present_t < 1.6 or len(self.win_entries) == 1:
            cells = []
            for e in self.win_entries:
                cells += e["cells"]
            return cells, None
        e = self.win_entries[int((self.present_t - 1.6) // 1.3) % len(self.win_entries)]
        return e["cells"], e

    def draw(self):
        s = self.canvas
        A = self.A
        if self.state == "TITLE":
            self.draw_title(s)
            self.screen.fill((0, 0, 0))
            self.screen.blit(s, (0, 0))
            pygame.display.flip()
            return
        s.blit(A.bg_free if (self.free_spins > 0 or self.fs_active) else A.bg, (0, 0))
        self.draw_marquee(s)
        # title
        t = outlined(A.f_title, TITLE, GOLD, (110, 50, 0), 3)
        s.blit(t, t.get_rect(center=(W // 2, 42)).move(0, 3))
        self.draw_top_hud(s)
        self.draw_reels(s)
        self.draw_lever(s)
        self.draw_message(s)
        self.draw_reject(s)
        self.draw_panel(s)
        for p in self.particles:
            p.draw(s)
        self.draw_banner(s)
        if self.state == "BIGWIN":
            self.draw_bigwin(s)
        if self.state == "GAMBLE":
            self.draw_gamble(s)
        if self.broke:
            self.draw_broke(s)
        if self.paytable_open:
            self.draw_paytable(s)
        ox = oy = 0
        if self.shake > 0:
            m = self.shake * 22
            ox, oy = random.randint(-int(m), int(m)), random.randint(-int(m), int(m))
        self.screen.fill((0, 0, 0))
        self.screen.blit(s, (ox, oy))
        pygame.display.flip()

    def draw_title(self, s):
        A = self.A
        s.blit(A.bg, (0, 0))
        # twinkling border
        for i in range(40):
            a = self.time * 1.4 + i * 0.16
            x = 40 + (W - 80) * ((i % 20) / 19)
            y = 28 if i < 20 else H - 28
            on = math.sin(a * 3) > 0
            pygame.draw.circle(s, (255, 230, 120) if on else (90, 60, 20), (int(x), y), 6 if on else 4)
        pulse = 1.0 + 0.04 * math.sin(self.time * 4)
        name = outlined(A.f_huge, "ONE-ARMED BAND-IDS", GOLD, (110, 40, 0), 6)
        nw, nh = name.get_size()
        name = pygame.transform.smoothscale(name, (max(1, int(nw * min(1.0, 1180 / nw) * pulse)),
                                                   max(1, int(nh * pulse))))
        s.blit(name, name.get_rect(center=(W // 2, 150)))
        sub = outlined(A.f_title, TITLE, WHITE, (80, 30, 0), 3)
        s.blit(sub, sub.get_rect(center=(W // 2, 250)))
        draw_text(s, "CUT THE CORD  ·  VOID THE NAME  ·  THE JUDGE BOWS", A.f_small,
                  (230, 210, 160), (W // 2, 310))
        # symbol row
        icons = [ID_ILLEGAL, LEGAL_NAME, JUDGE_BOWS, GOLD_10, WILD, SCATTER]
        for i, sym in enumerate(icons):
            bob = math.sin(self.time * 3 + i * 0.7) * 10
            spr = A.sprites[sym]
            r = spr.get_rect(center=(140 + i * 180, 420 + bob))
            s.blit(spr, r)
        mouse = pygame.mouse.get_pos()
        self.title_play.draw(s, mouse, self.mouse_down)
        self.buttons[0].draw(s, mouse, self.mouse_down)
        blink = 0.5 + 0.5 * math.sin(self.time * 5)
        if blink > 0.35:
            draw_text(s, "PRESS SPACE OR CLICK PLAY", A.f_med, WHITE, (W // 2, 630))
        draw_text(s, "S  sound     F11  fullscreen     ESC  quit", A.f_tiny, (170, 150, 180),
                  (W // 2, 680), shadow=False)

    def draw_marquee(self, s):
        winning = self.state in ("RESULT", "BIGWIN") and self.last_win > 0
        tick = int(self.time * (16 if winning else 7))
        for i, (x, y) in enumerate(self.bulbs):
            on = (i + tick) % 3 == 0 if not winning else (i + tick) % 2 == 0
            if on:
                s.blit(self.A.bulb_glow, (x - 16, y - 16))
                pygame.draw.circle(s, (255, 245, 190), (x, y), 5)
            else:
                pygame.draw.circle(s, (120, 80, 30), (x, y), 4)

    def draw_top_hud(self, s):
        A = self.A
        for b in self.buttons[:2]:
            b.draw(s, pygame.mouse.get_pos(), self.mouse_down)
        if self.free_spins > 0 or self.fs_active:
            r = pygame.Rect(W - 330, 14, 306, 40)
            pygame.draw.rect(s, (90, 30, 150), r, border_radius=20)
            pygame.draw.rect(s, GOLD, r, 3, border_radius=20)
            draw_text(s, f"CORD-CUT SPINS: {self.free_spins}   x{FREE_SPIN_MULT}", A.f_small, WHITE, r.center)
        st = self.stats
        draw_text(s, f"SPINS {fmt(st['spins'])}   BEST WIN {fmt(st['best'])}", A.f_tiny, (190, 170, 200),
                  (W - 24, 66), anchor="midright")
        hints = ["SPACE / click ARM  spin", "UP / DOWN  bet", "LEFT / RIGHT  lines",
                 "M  max bet      A  auto", "T  turbo        G  gamble", "P  paytable     S  sound"]
        for i, h in enumerate(hints):
            draw_text(s, h, A.f_tiny, (150, 130, 160), (24, 72 + i * 18), anchor="midleft", shadow=False)

    def draw_reels(self, s):
        A = self.A
        fr = self.frame_rect
        pygame.draw.rect(s, (0, 0, 0), fr.move(0, 6), border_radius=26)
        pygame.draw.rect(s, GOLD_D, fr.inflate(10, 10), border_radius=30)
        pygame.draw.rect(s, GOLD, fr.inflate(4, 4), border_radius=28)
        pygame.draw.rect(s, (22, 10, 26), fr, border_radius=24)
        highlight, current = self.highlighted_cells()
        hl = set(highlight)

        for i, r in enumerate(self.reels):
            rx = RX + i * (CELL + GAP)
            rect = pygame.Rect(rx, RY, CELL, REEL_H)
            pygame.draw.rect(s, (12, 7, 16), rect)
            s.set_clip(rect)
            base = math.floor(r.pos)
            blur = abs(r.vel) > 13
            for k in range(base, base + 4):
                y = RY + (k - r.pos) * CELL
                sym = r.sym(k)
                spr = A.blurred[sym] if blur else A.sprites[sym]
                if not blur and r.state == "STOPPED" and (i, k - r.target) in hl:
                    continue                    # drawn animated below
                s.blit(spr, (rx, y))
            s.set_clip(None)
        s.blit(A.reel_shade, (RX, RY))

        # separators
        for i in range(1, 5):
            x = RX + i * (CELL + GAP) - GAP // 2
            pygame.draw.line(s, (60, 36, 70), (x, RY), (x, RY + REEL_H), 2)

        # anticipation glow
        for i, r in enumerate(self.reels):
            if r.anticipate and r.moving:
                w = 4 + int(3 * (1 + math.sin(self.time * 14)))
                pygame.draw.rect(s, (255, 230, 90),
                                 pygame.Rect(RX + i * (CELL + GAP), RY, CELL, REEL_H).inflate(6, 6),
                                 w, border_radius=8)

        # winning cells (pulsing) and payline strokes
        if highlight and all(r.state == "STOPPED" for r in self.reels):
            self.draw_win_cells(s, hl, current)
        self.draw_line_badges(s, current)

    def draw_win_cells(self, s, hl, current):
        A = self.A
        pulse = 0.5 + 0.5 * math.sin(self.time * 8)
        ov = self.overlay
        ov.fill((0, 0, 0, 0))
        # payline strokes
        entries = self.win_entries if current is None else [current]
        for e in entries:
            if e["kind"] != "line":
                continue
            rows = PAYLINES[e["line"]]
            pts = [(r * (CELL + GAP) + CELL // 2, rows[r] * CELL + CELL // 2) for r in range(5)]
            col = LINE_COLORS[e["line"]]
            pygame.draw.lines(ov, (*col, 60), False, pts, 14)
            pygame.draw.lines(ov, (*col, 110), False, pts, 3)            # already cut
            f = (self.time * 0.55 + e["line"] * 0.17) % 1.0
            live = polyline_slice(pts, f)
            if len(live) > 1:
                pygame.draw.lines(ov, (*col, 255), False, live, 5)       # cord still to be cut
            for p in pts[:e["count"]]:
                pygame.draw.circle(ov, (*col, 255), p, 7)
            pos, d = polyline_point(pts, f)
            ic = pygame.transform.rotate(self.A.scissor_icon, math.degrees(math.atan2(-d[0], -d[1])))
            ov.blit(ic, ic.get_rect(center=(int(pos[0]), int(pos[1]))))
        s.blit(ov, (RX, RY))
        for (r, row) in hl:
            x = RX + r * (CELL + GAP)
            y = RY + row * CELL
            sym = self.reels[r].sym(self.reels[r].target + row)
            sc = 1.0 + 0.07 * pulse
            size = int(CELL * sc)
            spr = pygame.transform.smoothscale(A.sprites[sym], (size, size))
            s.set_clip(pygame.Rect(x - 6, y - 6, CELL + 12, CELL + 12))
            s.blit(spr, (x - (size - CELL) // 2, y - (size - CELL) // 2))
            s.set_clip(None)
            glow = A.cell_glow
            glow.set_alpha(int(150 + 105 * pulse))
            s.blit(glow, (x - 18, y - 18))

    def draw_line_badges(self, s, current):
        A = self.A
        active_rows_left, active_rows_right = {}, {}
        for li in range(self.lines):
            rows = PAYLINES[li]
            active_rows_left.setdefault(rows[0], []).append(li)
            active_rows_right.setdefault(rows[4], []).append(li)
        win_lines = {e["line"] for e in self.win_entries if e["kind"] == "line"}
        if current is not None and current["kind"] == "line":
            win_lines = {current["line"]}
        for side, table in (("L", active_rows_left), ("R", active_rows_right)):
            for row, lis in table.items():
                n = len(lis)
                for j, li in enumerate(lis):
                    cy = RY + row * CELL + CELL // 2 + (j - (n - 1) / 2) * 27
                    cx = RX - 44 if side == "L" else RX + REEL_W + 44
                    lit = li in win_lines and self.state in ("RESULT", "BIGWIN")
                    col = LINE_COLORS[li] if (lit or self.state in ("IDLE",)) else tuple(c // 3 for c in LINE_COLORS[li])
                    if lit and int(self.time * 6) % 2:
                        col = WHITE
                    pygame.draw.circle(s, (0, 0, 0), (cx + 1, cy + 2), 13)
                    pygame.draw.circle(s, col, (cx, cy), 12)
                    pygame.draw.circle(s, (20, 10, 20), (cx, cy), 12, 2)
                    draw_text(s, str(li + 1), A.f_tiny, BLACK if sum(col) > 300 else WHITE, (cx, cy), shadow=False)

    def draw_message(self, s):
        text, col = self.current_message()
        draw_text(s, text, self.A.f_med, col, (W // 2, 546))
        if self.state == "SPIN" and self.spin_is_free is False and self.auto:
            draw_text(s, "AUTO", self.A.f_tiny, GREEN, (W // 2, 568))

    def draw_lever(self, s):
        px, py = 1120, 340
        pull = math.sin(math.pi * min(1.0, self.lever_t / 0.5)) if self.lever_t < 0.5 else 0.0
        a = math.radians(18 + pull * 125)
        kx, ky = px + 185 * math.sin(a), py - 185 * math.cos(a)
        pygame.draw.rect(s, (0, 0, 0), (px - 36, py - 26, 56, 118), border_radius=16)
        pygame.draw.rect(s, (70, 72, 86), (px - 40, py - 32, 56, 118), border_radius=16)
        pygame.draw.rect(s, GOLD_D, (px - 40, py - 32, 56, 118), 3, border_radius=16)
        pygame.draw.line(s, (0, 0, 0), (px + 5, py + 6), (kx + 5, ky + 7), 18)
        pygame.draw.line(s, (130, 135, 150), (px, py), (kx, ky), 16)
        pygame.draw.line(s, (225, 230, 240), (px - 3, py - 3), (kx - 3, ky - 3), 5)
        pygame.draw.circle(s, GOLD_D, (px, py), 20)
        pygame.draw.circle(s, GOLD, (px, py), 14)
        pygame.draw.circle(s, (110, 10, 20), (int(kx), int(ky)), 30)
        pygame.draw.circle(s, (215, 35, 45), (int(kx), int(ky)), 26)
        pygame.draw.circle(s, (255, 150, 150), (int(kx) - 8, int(ky) - 9), 8)

    def draw_reject(self, s):
        if not (self.state == "RESULT" and self.last_win == 0 and not self.win_entries
                and not self.spin_is_free and self.present_t < 1.6):
            return
        u = self.present_t
        k = 1.0 + max(0.0, (0.15 - u) / 0.15) * 0.9
        st = self.A.stamp
        img = pygame.transform.smoothscale(st, (int(st.get_width() * k), int(st.get_height() * k)))
        img.set_alpha(255 if u < 1.1 else max(0, int(255 * (1.6 - u) / 0.5)))
        s.blit(img, img.get_rect(center=(W // 2, RY + REEL_H // 2)))

    def draw_panel(self, s):
        A = self.A
        s.blit(A.panel_bg, (0, PANEL_Y))
        pygame.draw.line(s, GOLD, (0, PANEL_Y), (W, PANEL_Y), 4)
        pygame.draw.line(s, GOLD_D, (0, PANEL_Y + 4), (W, PANEL_Y + 4), 2)

        def box(x, y, w, h, label, value, vcol=WHITE):
            pygame.draw.rect(s, (8, 4, 10), (x, y, w, h), border_radius=12)
            pygame.draw.rect(s, GOLD_D, (x, y, w, h), 2, border_radius=12)
            draw_text(s, label, A.f_tiny, (190, 160, 120), (x + w // 2, y + 16), shadow=False)
            draw_text(s, value, A.f_big, vcol, (x + w // 2, y + h // 2 + 10))

        low = self.credits < self.total_bet and self.free_spins == 0
        box(24, 604, 190, 96, "CREDITS", fmt(self.shown_credits), RED if low else WHITE)
        win_col = GOLD if self.shown_win > 0 else (120, 110, 120)
        box(224, 604, 190, 96, "WIN", fmt(self.shown_win), win_col)

        for cx, label, value in ((510, "BET / LINE", fmt(self.bet)), (684, "LINES", str(self.lines))):
            draw_text(s, label, A.f_tiny, (190, 160, 120), (cx, 614), shadow=False)
            draw_text(s, value, A.f_big, WHITE, (cx, 654))
        draw_text(s, "TOTAL BET", A.f_tiny, (190, 160, 120), (858, 614), shadow=False)
        draw_text(s, fmt(self.total_bet), A.f_big, GOLD, (858, 645))

        mouse = pygame.mouse.get_pos()
        for b in self.buttons[2:]:
            b.draw(s, mouse, self.mouse_down)
        if self.auto:
            draw_text(s, "AUTO ON", A.f_tiny, GREEN, (1005, 710), shadow=False)

    def draw_banner(self, s):
        b = self.banner
        if not b:
            return
        u = min(1.0, b["t"] / 0.35)
        sc = ease_out_back(u, 2.0)
        fade = 1.0 if b["t"] < b["dur"] - 0.4 else max(0.0, (b["dur"] - b["t"]) / 0.4)
        band = pygame.Surface((W, 200), pygame.SRCALPHA)
        band.fill((0, 0, 0, int(190 * fade)))
        cy = RY + REEL_H // 2
        s.blit(band, (0, cy - 100))
        for ln, col in ((cy - 100, b["color"]), (cy + 98, b["color"])):
            pygame.draw.line(s, col, (0, ln), (W, ln), 4)
        title = outlined(self.A.f_title, b["title"], GOLD, (90, 40, 0), 3)
        w, h = title.get_size()
        title = pygame.transform.smoothscale(title, (max(1, int(w * sc * 1.3)), max(1, int(h * sc * 1.3))))
        title.set_alpha(int(255 * fade))
        s.blit(title, title.get_rect(center=(W // 2, cy - 30)))
        sub = self.A.f_med.render(b["sub"], True, WHITE)
        sub.set_alpha(int(255 * fade))
        s.blit(sub, sub.get_rect(center=(W // 2, cy + 42)))

    def draw_bigwin(self, s):
        b = self.bigwin
        A = self.A
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        s.blit(dim, (0, 0))
        for p in self.particles:
            p.draw(s)
        pulse = 1.0 + 0.04 * math.sin(self.time * 10)
        grow = min(1.0, b["t"] / 0.4)
        title = outlined(A.f_huge, b["name"], GOLD, (120, 40, 0), 5)
        w, h = title.get_size()
        k = ease_out_back(grow, 2.0) * pulse
        title = pygame.transform.smoothscale(title, (max(1, int(w * k)), max(1, int(h * k))))
        s.blit(title, title.get_rect(center=(W // 2, 250)))
        amt = outlined(A.f_huge, fmt(self.shown_win), WHITE, (40, 20, 70), 5)
        s.blit(amt, amt.get_rect(center=(W // 2, 400)))
        draw_text(s, "click or press SPACE to skip", A.f_tiny, (200, 190, 210), (W // 2, 480), shadow=False)

    def draw_gamble(self, s):
        A = self.A
        g = self.gamble
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 210))
        s.blit(dim, (0, 0))
        pr = pygame.Rect(300, 40, 680, 660)
        pygame.draw.rect(s, (28, 12, 34), pr, border_radius=24)
        pygame.draw.rect(s, GOLD, pr, 4, border_radius=24)
        draw_text(s, "CUT OR DENIED", A.f_title, GOLD, (W // 2, 88))
        draw_text(s, "Guess RED or BLACK on a 52-card deck", A.f_tiny, (200, 180, 160),
                  (W // 2, 128), shadow=False)
        draw_text(s, f"GAMBLE AMOUNT   {fmt(g['stake'])}", A.f_med, WHITE, (W // 2, 158))
        if g["stake"] > 0:
            draw_text(s, f"WIN  {fmt(g['stake'] * 2)}", A.f_med, GREEN, (W // 2, 192))
        card = pygame.Rect(0, 0, 168, 236)
        card.center = (W // 2, 340)
        face = None
        scale_x = 1.0
        if g["phase"] == "flip":
            u = g["t"] / 0.9
            scale_x = abs(math.cos(math.pi * 3 * u))
            face = g.get("card") if u >= 0.5 else None
        elif g["phase"] == "reveal":
            face = g.get("card")
        cw = max(4, int(card.w * scale_x))
        cr = pygame.Rect(0, 0, cw, card.h)
        cr.center = card.center
        if face is None:
            pygame.draw.rect(s, (50, 30, 140), cr, border_radius=14)
            pygame.draw.rect(s, WHITE, cr, 3, border_radius=14)
            if cw > 40:
                for dx in range(-1, 2):
                    for dy in range(-2, 3):
                        pygame.draw.circle(s, (120, 90, 220), (cr.centerx + dx * cw // 4, cr.centery + dy * 36), 8)
            if cw > 50:
                draw_text(s, "?", A.f_title, WHITE, cr.center)
        elif cw > 70:
            draw_playing_card(s, cr, face, (A.f_med, A.f_tiny))
        else:
            col = (200, 25, 40) if face["color"] == "red" else (20, 20, 25)
            pygame.draw.rect(s, WHITE, cr, border_radius=12)
            pygame.draw.rect(s, col, cr.inflate(-10, -10), border_radius=8)
        draw_text(s, "LAST CARDS", A.f_tiny, (190, 160, 120), (W // 2, 478), shadow=False)
        for i, hc in enumerate(g["hist"][-5:]):
            r = pygame.Rect(W // 2 - 115 + i * 46, 490, 40, 56)
            if isinstance(hc, dict):
                draw_playing_card(s, r, hc, (A.f_tiny, A.f_tiny))
            else:
                c = (200, 25, 40) if hc == "red" else (20, 20, 25)
                pygame.draw.rect(s, c, r, border_radius=6)
        if g["phase"] == "reveal":
            msg = "CORD CUT!" if g.get("won") else "DENIED!"
            draw_text(s, msg, A.f_big, GREEN if g.get("won") else RED, (W // 2, 455))
        mouse = pygame.mouse.get_pos()
        for b in self.gamble_buttons:
            b.draw(s, mouse, self.mouse_down)
        draw_text(s, f"ROUND {g['rounds'] + 1} / 5", A.f_tiny, (190, 160, 120), (W // 2, 665), shadow=False)

    def draw_broke(self, s):
        A = self.A
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        s.blit(dim, (0, 0))
        draw_text(s, "ID IS ILLEGAL", A.f_huge, RED, (W // 2, 300))
        draw_text(s, "Out of credits. Go to LEGALNAMEFRAUD.CARRD.CO", A.f_med, WHITE, (W // 2, 390))
        self.reset_button.draw(s, pygame.mouse.get_pos(), self.mouse_down)

    def draw_paytable(self, s):
        A = self.A
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 215))
        s.blit(dim, (0, 0))
        pr = pygame.Rect(90, 24, 1100, 672)
        pygame.draw.rect(s, (24, 12, 30), pr, border_radius=24)
        pygame.draw.rect(s, GOLD, pr, 4, border_radius=24)
        draw_text(s, "PAYTABLE", A.f_title, GOLD, (W // 2, 62))
        draw_text(s, f"Pays shown for 3 / 4 / 5 of a kind: multiplier of bet per line "
                     f"(credits at your current bet of {self.bet})", A.f_tiny, (190, 170, 200), (W // 2, 100),
                  shadow=False)
        layout = [([ID_ILLEGAL, LEGAL_NAME_FRAUD, LEGAL_NAME, JUDGE_BOWS, SCISSORS], 130), ([CUT_CORD, GOLD_10, UNCHAINED, WILD, SCATTER], 660)]
        for syms, x in layout:
            for row, sym in enumerate(syms):
                y = 120 + row * 82
                spr = pygame.transform.smoothscale(A.sprites[sym], (72, 72))
                s.blit(spr, (x, y))
                extra = ""
                if sym == WILD:
                    extra = " (WILD)"
                elif sym in (SCATTER, LEGAL_NAME, JUDGE_BOWS):
                    extra = " (BONUS)"
                draw_text(s, SYMBOL_NAMES[sym] + extra, A.f_small, GOLD, (x + 90, y + 8), anchor="midleft")
                if sym == SCATTER:
                    for j, n in enumerate((5, 4, 3)):
                        draw_text(s, f"{n} = x{SCATTER_PAY[n]} TOTAL BET  +  {SCATTER_FREE_SPINS[n]} FREE SPINS",
                                  A.f_tiny, WHITE, (x + 90, y + 28 + j * 16), anchor="midleft", shadow=False)
                else:
                    pays = PAYTABLE[sym]
                    for j, n in enumerate((5, 4, 3)):
                        m = pays[n - 3]
                        draw_text(s, f"{n} of a kind   x{m}   =   {fmt(m * self.bet)}", A.f_tiny, WHITE,
                                  (x + 90, y + 28 + j * 16), anchor="midleft", shadow=False)
        rules = [
            "CRSSNOW is WILD: it substitutes for every symbol except BCCRSS.   Lines pay left to right on adjacent reels; highest win per line only.",
            f"3+ BCCRSS anywhere start the CORD-CUT BONUS.  3+ JANE DOE-755 or JUDGE BOWS on a payline trigger their own bonuses (4+ add free spins).  Bonus line wins x{FREE_SPIN_MULT}.",
            "Wins of 10x your total bet or more trigger the CORD CUT celebration.   After any win you may risk it: guess RED or BLACK on a 52-card deck, up to 5 rounds.",
        ]
        for i, line in enumerate(rules):
            draw_text(s, line, A.f_tiny, (225, 215, 235), (W // 2, 545 + i * 20), shadow=False)
        # payline diagrams
        x0 = 140
        for li, rows in enumerate(PAYLINES):
            bx = x0 + li * 100
            by = 592
            pygame.draw.rect(s, (12, 6, 16), (bx, by, 92, 62), border_radius=6)
            pygame.draw.rect(s, (80, 60, 90), (bx, by, 92, 62), 1, border_radius=6)
            pts = []
            for r in range(5):
                for row in range(3):
                    pygame.draw.circle(s, (60, 45, 70), (bx + 12 + r * 17, by + 12 + row * 19), 3)
                pts.append((bx + 12 + r * 17, by + 12 + rows[r] * 19))
            pygame.draw.lines(s, LINE_COLORS[li], False, pts, 3)
            draw_text(s, f"LINE {li + 1}", A.f_tiny, LINE_COLORS[li], (bx + 46, by + 74), shadow=False)
        draw_text(s, "click anywhere or press P / ESC to close", A.f_tiny, (150, 130, 160), (W // 2, 686), shadow=False)

    # ------------------------------------------------------------------- run
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                self.handle(e)
            self.update(dt)
            self.draw()


# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if "--sim" in args:
        i = args.index("--sim")
        n = int(args[i + 1]) if i + 1 < len(args) else 1_000_000
        simulate(n)
        return
    if "--reset" in args:
        try:
            SAVE_PATH.unlink()
        except OSError:
            pass
        print("Save file reset.")
    pygame.mixer.pre_init(RATE, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption(TITLE)
    try:
        screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
    except pygame.error:
        screen = pygame.display.set_mode((W, H))
    Game(screen).run()


if __name__ == "__main__":
    main()
