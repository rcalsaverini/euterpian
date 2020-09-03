import pandas as pd
from itertools import permutations
from math import factorial
from tqdm import tqdm
from pychord.analyzer import get_all_rotated_notes, notes_to_positions
from pychord.analyzer import find_quality
from pychord import Chord

COMPLEXITY_CLASSES = {
    1: ["", "m", "5"],
    2: ["7", "m7"],
    3: ["M7", "mM7", "sus2", "sus4"],
    4: ["6", "9", "7+9", "7-9", "7sus4", "9sus4", "m9", "m6", "m7-5", "add9", "M9"],
    5: ["7+5", "7-5", "M7+5"],
    6: ["11", "add11", "7+11", "7-13"],
    10: ["aug", "dim", "dim6", "7#9b5", "9-5", "9+5", "7#9#5", "7b9b5", "7b9#5"],
}


COMPLEXITY = {
    quality: complexity
    for (complexity, qualities) in COMPLEXITY_CLASSES.items()
    for quality in qualities
}


def note_to_chord(notes, raise_on_error=False):
    root = notes[0]
    root_and_positions = [
        [rotated_notes[0], notes_to_positions(rotated_notes, rotated_notes[0])]
        for rotated_notes in get_all_rotated_notes(notes)
    ]
    for temp_root, positions in root_and_positions:
        quality = find_quality(positions)
        if quality is None:
            continue
        chord_name = (
            "{}{}".format(root, quality)
            if temp_root == root
            else "{}{}/{}".format(temp_root, quality, root)
        )
        try:
            chord = Chord(chord_name)
            yield chord
        except Exception as e:
            if raise_on_error:
                raise e


def relative_complexity(scale):
    def complexity(chord):
        degree = 1 + scale.index(chord.root)
        quality_complexity = COMPLEXITY[chord.quality.quality]
        is_inversion = int((chord.on is not None) and (chord.on != chord.root))
        return 3 * is_inversion + quality_complexity

    return complexity


def iterate_scale(scale, chord_size, verbose=0):
    scale_length = len(scale)
    iterator = permutations(scale, chord_size)
    if verbose == 0:
        yield from iterator
    else:
        size = factorial(scale_length) * factorial(scale_length - chord_size)
        desc = f"{scale}"
        yield from tqdm(iterator, desc=desc, total=size)



def chords_from_notes(notes, inversions=False):
    for chord in note_to_chord(notes):
        is_inversion = (chord.on is not None) and (chord.on != chord.root)
        if inversions or (not is_inversion):
            yield chord



def chords_from_scale(scale, inversions=False, diversity=(2, 5), verbose=0):
    min_diversity, max_diversity = diversity
    complexity = relative_complexity(scale)
    yield from (
        chord
        for k in range(min_diversity, max_diversity + 1)
        for notes in iterate_scale(scale, k, verbose=verbose)
        for chord in chords_from_notes(notes, inversions=inversions)
    )

def tabulate_chords_from_scale(scale, inversions=False, diversity=(2, 5), verbose=0):
    min_diversity, max_diversity = diversity
    complexity = relative_complexity(scale)
    return pd.DataFrame(
        [
            (k, chord, chord.root, chord.on, complexity(chord))
            for k in range(min_diversity, max_diversity + 1)
            for notes in iterate_scale(scale, k, verbose=verbose)
            for chord in chords_from_notes(notes, inversions=inversions)
        ],
        columns=["diversity", "chord", "root", "bass", "complexity"],
    )


def chord_table(scale, inversions=False, diversity=(2, 5), verbose=0, index=None, columns=None):
    complexity = relative_complexity(scale)

    def complexity_sort(xs):
        sorted_chords = sorted(list(xs), key=complexity)
        return ", ".join([chord.chord for chord in sorted_chords])

    chords = tabulate_chords_from_scale(scale, inversions=inversions, diversity=diversity, verbose=verbose)
    return chords.pivot_table(
        columns=columns or "complexity",
        index=index or "root",
        values="chord",
        aggfunc=complexity_sort,
    ).fillna("")


if __name__ == "__main__":
  scale = ["E", "F", "G#", "A#", "B", "C", "D"]
  table = chord_table(scale, inversions=False, columns=["complexity", "diversity"]).loc[scale]
  print(table)