"""
Convert the big-room progressive-house arrangement spreadsheet to a Type 1 MIDI.

Layout:
  Row 0: section groupings (ignored)
  Row 1: headers: Bar, Section, Kick, Snare/Clap, Hi-Hat, Perc Layers,
         Serum Bass, Pad/Chords, Serum Lead, Female Vocal,
         Risers/Sweeps/FX, Energy %, Automation Notes
  Row 2+: one row per bar. Drum cells contain "✓ Label\nSTEP PATTERN"
          where STEP PATTERN is 16 tokens, X = hit, . = rest.
          Pitched cells contain "✓ Label" only.

Output: 120 BPM 4/4, 480 PPQ, ~153 bars.
  - Drum tracks on channel 10 (GM drum map).
  - Pitched tracks on their own channels with a placeholder root note per bar.
  - Section names as MIDI markers.
  - Energy % as CC1 (mod wheel) on a dedicated automation track.
"""
from __future__ import annotations
from pathlib import Path
import openpyxl
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

SRC = "/root/.claude/uploads/016e113e-9cce-57c8-9732-e199554bbf9f/8dcfe5fe-20260709bigroomprogressivehousearrangement.xlsx"
OUT = "/tmp/claude-0/-home-user-agency-agents/016e113e-9cce-57c8-9732-e199554bbf9f/scratchpad/big-room-arrangement.mid"

TEMPO = 128.0        # big-room house standard; tweak if wanted
PPQ = 480
BEATS_PER_BAR = 4
TICKS_PER_BAR = PPQ * BEATS_PER_BAR
TICKS_PER_16TH = PPQ // 4
STEPS_PER_BAR = 16

# GM drum map notes (channel 10 = index 9 in mido)
DRUM_NOTES = {
    "Kick":         36,   # C1  Bass Drum 1
    "Snare/Clap":   38,   # D1  Acoustic Snare
    "Hi-Hat":       42,   # F#1 Closed Hi-Hat
    "Perc Layers":  39,   # D#1 Hand Clap
}

# Chord progressions — 1 chord per bar, cycling every 4 bars.
# Voicings tight around F#3–A4; F#m and A share C#4 on top for glue.
# F#=54(F#3) G#=56 A=57 A#=58 B=59 C=60 C#=61 D=62 D#=63 E=64 F=65 F#=66
CHORD_MAIN = [        # F#m | D | A | E
    (30, [54, 57, 61]),  # F#m: F#1 bass, [F#3 A3 C#4]
    (38, [54, 57, 62]),  # D  : D2  bass, [F#3 A3 D4]  (keeps F# A common)
    (33, [52, 57, 61]),  # A  : A1  bass, [E3  A3 C#4] (top C# matches F#m)
    (40, [52, 56, 59]),  # E  : E2  bass, [E3  G#3 B3]
]
CHORD_ALT = [         # D | E | F#m | C#m
    (38, [54, 57, 62]),  # D
    (40, [52, 56, 59]),  # E
    (30, [54, 57, 61]),  # F#m
    (37, [49, 52, 56]),  # C#m: C#2 bass, [C#3 E3 G#3]
]

def progression_for(section: str | None) -> list[tuple[int, list[int]]]:
    """Return the 4-bar chord loop for a given section label."""
    if not section:
        return CHORD_MAIN
    s = section.upper()
    if "BREAKDOWN" in s or "CHORUS" in s or s.startswith("VERSE"):
        return CHORD_ALT
    return CHORD_MAIN

# Non-harmonic pitched tracks — keep as simple placeholder notes to sketch clip regions.
PITCHED_PLACEHOLDER = {
    "Serum Lead":     72,
    "Female Vocal":   67,
    "Risers/Sweeps/FX": 84,
}


def parse_pattern(cell) -> list[int] | None:
    """Extract a 16-step pattern list from a cell. Returns list of step indexes (0..15)
    where a hit occurs, or None if no pattern is present."""
    if not cell or not isinstance(cell, str):
        return None
    lines = [ln.strip() for ln in cell.splitlines() if ln.strip()]
    if not lines:
        return None
    # Pattern line is one with lots of X and . tokens
    for line in lines:
        tokens = line.split()
        # normalize: some patterns use X or . or x
        hit_tokens = [t.upper() for t in tokens if t.upper() in ("X", ".")]
        if len(hit_tokens) >= 8:  # at least half a bar of steps
            # Pad/truncate to 16
            steps = (hit_tokens + ["."] * STEPS_PER_BAR)[:STEPS_PER_BAR]
            return [i for i, s in enumerate(steps) if s == "X"]
    return None


def cell_active(cell) -> bool:
    if cell is None:
        return False
    if isinstance(cell, str):
        s = cell.strip()
        # ✓ = active, ⚡ = event/instruction (not a play)
        return s.startswith("✓") or s.startswith("X") or s.lower() in {"x", "yes", "y"}
    if isinstance(cell, (int, float)):
        return cell != 0
    return False


def add_absolute(track: MidiTrack, events: list[tuple[int, Message | MetaMessage]]):
    """Given (abs_tick, message) events, sort and convert to delta-time on the track."""
    events.sort(key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1))
    last = 0
    for tick, msg in events:
        msg.time = max(0, tick - last)
        track.append(msg)
        last = tick


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["Arrangement"]
    rows = list(ws.iter_rows(min_row=3, values_only=True))  # skip 2 header rows
    n_bars = len(rows)
    print(f"Parsing {n_bars} bars…")

    # Column indexes (from header row 1)
    COL = {
        "Bar": 0, "Section": 1,
        "Kick": 2, "Snare/Clap": 3, "Hi-Hat": 4, "Perc Layers": 5,
        "Serum Bass": 6, "Pad / Chords": 7, "Serum Lead": 8,
        "Female Vocal": 9, "Risers/Sweeps/FX": 10,
        "Energy %": 11, "Automation Notes": 12,
    }

    mid = MidiFile(type=1, ticks_per_beat=PPQ)

    # --- Tempo / marker track ---
    tempo_track = MidiTrack()
    tempo_events: list[tuple[int, MetaMessage]] = []
    tempo_events.append((0, MetaMessage("track_name", name="Tempo & Markers")))
    tempo_events.append((0, MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO))))
    tempo_events.append((0, MetaMessage("time_signature", numerator=4, denominator=4)))
    last_section = None
    for bar_i, row in enumerate(rows):
        sec = row[COL["Section"]]
        if sec and sec != last_section:
            tempo_events.append((bar_i * TICKS_PER_BAR,
                                 MetaMessage("marker", text=str(sec).encode("ascii", "replace").decode("ascii"))))
            last_section = sec
    add_absolute(tempo_track, tempo_events)
    tempo_track.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(tempo_track)

    # --- Drum tracks (channel 10 → mido channel=9) ---
    for name in ("Kick", "Snare/Clap", "Hi-Hat", "Perc Layers"):
        track = MidiTrack()
        events: list[tuple[int, Message]] = []
        events.append((0, MetaMessage("track_name", name=name[:32])))
        note = DRUM_NOTES[name]
        for bar_i, row in enumerate(rows):
            cell = row[COL[name]]
            if not cell_active(cell):
                continue
            steps = parse_pattern(cell)
            if steps is None:
                # Active but no explicit pattern → 4-on-the-floor for kick, off-beat for hats,
                # backbeat for snare/clap, syncopated for perc
                fallback = {
                    "Kick":        [0, 4, 8, 12],
                    "Snare/Clap":  [4, 12],
                    "Hi-Hat":      [2, 6, 10, 14],
                    "Perc Layers": [6, 14],
                }[name]
                steps = fallback
            bar_start = bar_i * TICKS_PER_BAR
            for s in steps:
                on = bar_start + s * TICKS_PER_16TH
                events.append((on, Message("note_on", channel=9, note=note, velocity=100)))
                events.append((on + TICKS_PER_16TH // 2,
                               Message("note_off", channel=9, note=note, velocity=0)))
        add_absolute(track, events)
        track.append(MetaMessage("end_of_track", time=0))
        mid.tracks.append(track)

    # --- Serum Bass: root note per bar (chord-driven) ---
    bass_track = MidiTrack()
    bass_events: list[tuple[int, Message]] = []
    bass_events.append((0, MetaMessage("track_name", name="Serum Bass")))
    for bar_i, row in enumerate(rows):
        if not cell_active(row[COL["Serum Bass"]]):
            continue
        prog = progression_for(row[COL["Section"]])
        bass_note, _ = prog[bar_i % 4]
        on = bar_i * TICKS_PER_BAR
        bass_events.append((on, Message("note_on", channel=0, note=bass_note, velocity=110)))
        bass_events.append((on + TICKS_PER_BAR,
                            Message("note_off", channel=0, note=bass_note, velocity=0)))
    add_absolute(bass_track, bass_events)
    bass_track.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(bass_track)

    # --- Pad / Chords: full triad per bar (chord-driven) ---
    pad_track = MidiTrack()
    pad_events: list[tuple[int, Message]] = []
    pad_events.append((0, MetaMessage("track_name", name="Pad / Chords")))
    for bar_i, row in enumerate(rows):
        if not cell_active(row[COL["Pad / Chords"]]):
            continue
        prog = progression_for(row[COL["Section"]])
        _, triad = prog[bar_i % 4]
        on = bar_i * TICKS_PER_BAR
        for n in triad:
            pad_events.append((on, Message("note_on", channel=1, note=n, velocity=90)))
            pad_events.append((on + TICKS_PER_BAR,
                               Message("note_off", channel=1, note=n, velocity=0)))
    add_absolute(pad_track, pad_events)
    pad_track.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(pad_track)

    # --- Placeholder pitched tracks (Lead / Vocal / Risers) ---
    # Merge consecutive active bars into one held note for cleaner clips.
    for ch_idx, (name, root) in enumerate(PITCHED_PLACEHOLDER.items(), start=2):
        track = MidiTrack()
        events: list[tuple[int, Message]] = []
        events.append((0, MetaMessage("track_name", name=name[:32])))
        run_start = None
        for bar_i in range(n_bars + 1):
            active = bar_i < n_bars and cell_active(rows[bar_i][COL[name]])
            if active and run_start is None:
                run_start = bar_i
            elif not active and run_start is not None:
                on = run_start * TICKS_PER_BAR
                off = bar_i * TICKS_PER_BAR
                events.append((on, Message("note_on", channel=ch_idx, note=root, velocity=96)))
                events.append((off, Message("note_off", channel=ch_idx, note=root, velocity=0)))
                run_start = None
        add_absolute(track, events)
        track.append(MetaMessage("end_of_track", time=0))
        mid.tracks.append(track)

    # --- Energy % as CC1 (mod wheel) on its own automation track ---
    auto_track = MidiTrack()
    auto_events: list[tuple[int, Message]] = []
    auto_events.append((0, MetaMessage("track_name", name="Energy (CC1)")))
    for bar_i, row in enumerate(rows):
        e = row[COL["Energy %"]]
        if e is None:
            continue
        try:
            val = int(round(float(e) * 127))
            val = max(0, min(127, val))
        except (TypeError, ValueError):
            continue
        auto_events.append((bar_i * TICKS_PER_BAR,
                            Message("control_change", channel=0, control=1, value=val)))
    add_absolute(auto_track, auto_events)
    auto_track.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(auto_track)

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    mid.save(OUT)
    print(f"Wrote {OUT}")
    print(f"Total length: {n_bars} bars = {n_bars * TICKS_PER_BAR} ticks @ {PPQ} PPQ / {TEMPO} BPM")
    print(f"Tracks: {len(mid.tracks)}")
    for t in mid.tracks:
        name = next((m.name for m in t if m.type == "track_name"), "?")
        print(f"  - {name}: {len(t)} events")


if __name__ == "__main__":
    main()
