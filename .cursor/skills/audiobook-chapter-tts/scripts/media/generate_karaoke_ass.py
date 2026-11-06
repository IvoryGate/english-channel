"""Stable phrase cards with exact aligned-word highlighting; no bouncing text."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from media.media_layout import ASS_FONT_SIZE, HEIGHT, WIDTH
from media.thumbnail_tokens import ThumbnailTokens

SERIES_FONT_NAME = {'series_a': 'Inter', 'series_b': 'Inter', 'series_c': 'Manrope'}
MAX_CUE_WORDS = 10
MAX_CUE_CHARACTERS = 76
PANEL_PATH = ('m 24 0 l 2076 0 b 2090 0 2100 10 2100 24 l 2100 276 '
              'b 2100 290 2090 300 2076 300 l 24 300 b 10 300 0 290 0 276 '
              'l 0 24 b 0 10 10 0 24 0')


def _ass_timestamp(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, rest = divmod(centiseconds, 360000)
    minutes, rest = divmod(rest, 6000)
    secs, centis = divmod(rest, 100)
    return f'{hours}:{minutes:02d}:{secs:02d}.{centis:02d}'


def _safe(value: str) -> str:
    return value.replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ').strip()


def _phrases(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        text = _safe(str(word['word']))
        length = sum(len(str(row['word'])) + 1 for row in current) + len(text)
        gap = current and float(word['start']) - float(current[-1]['end']) > .65
        if current and (len(current) >= MAX_CUE_WORDS or length > MAX_CUE_CHARACTERS or gap):
            groups.append(current)
            current = []
        current.append(word)
        if len(current) >= 4 and text.endswith(('.', '?', '!', ';', ':')):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _split_index(words: list[dict[str, Any]]) -> int:
    texts = [_safe(str(word['word'])) for word in words]
    if len(' '.join(texts)) <= 38:
        return len(words)
    return min(range(1, len(words)), key=lambda i: max(len(' '.join(texts[:i])), len(' '.join(texts[i:]))))


def _text(words: list[dict[str, Any]], active: int | None) -> str:
    split = _split_index(words)
    parts: list[str] = []
    for index, word in enumerate(words):
        if index:
            parts.append('\\N' if index == split else ' ')
        text = _safe(str(word['word']))
        parts.append('{\\c&H008AD5FF&}' + text + '{\\c&H00FFFFFF&}' if index == active else text)
    return '{\\an5\\pos(1280,1010)\\q2}' + ''.join(parts)


def _header(tokens: ThumbnailTokens) -> list[str]:
    font = SERIES_FONT_NAME.get(tokens.show_id, 'Inter')
    return ['[Script Info]', 'Title: ELR Phrase Cards v1', 'ScriptType: v4.00+',
            'WrapStyle: 2', 'ScaledBorderAndShadow: yes', f'PlayResX: {WIDTH}', f'PlayResY: {HEIGHT}', '',
            '[V4+ Styles]',
            'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
            f'Style: Default,{font},{ASS_FONT_SIZE},&H00FFFFFF,&H008AD5FF,&H00101C18,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,5,200,200,0,1', '',
            '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']


def _event(layer: int, start: float, end: float, text: str) -> str:
    return f'Dialogue: {layer},{_ass_timestamp(start)},{_ass_timestamp(end)},Default,,0,0,0,,{text}'


def _events_for_turn_words(words: list[dict[str, Any]], speaker: str = '') -> list[str]:
    events: list[str] = []
    for phrase in _phrases(words):
        start, end = float(phrase[0]['start']), float(phrase[-1]['end'])
        events.append(_event(0, start, end,
            '{\\an7\\pos(230,860)\\bord0\\shad0\\1c&H18251C&\\1a&H55&\\p1}' + PANEL_PATH))
        name = speaker or str(phrase[0].get('speaker') or '')
        if name:
            events.append(_event(1, start, end, '{\\an5\\pos(1280,822)\\fs26\\c&H008AD5FF&\\bord2}' + _safe(name).upper()))
        cursor = start
        for index, word in enumerate(phrase):
            word_start = max(cursor, float(word['start']))
            word_end = max(word_start, float(word['end']))
            if word_start > cursor:
                events.append(_event(2, cursor, word_start, _text(phrase, None)))
            if word_end > word_start:
                events.append(_event(2, word_start, word_end, _text(phrase, index)))
            cursor = word_end
    return events


def generate_karaoke_ass(words: list[dict[str, Any]], tokens: ThumbnailTokens, *,
                         turns: list[dict[str, Any]] | None = None) -> str:
    if not words and not turns:
        raise ValueError('Cannot generate ASS without aligned words')
    events: list[str] = []
    if turns:
        for turn in turns:
            events.extend(_events_for_turn_words(turn.get('words') or [], str(turn.get('speaker') or '')))
    else:
        group: list[dict[str, Any]] = []
        identity = None
        for word in words:
            next_identity = (word.get('turnId'), word.get('speaker'))
            if group and next_identity != identity:
                events.extend(_events_for_turn_words(group))
                group = []
            group.append(word)
            identity = next_identity
        if group:
            events.extend(_events_for_turn_words(group))
    return '\n'.join(_header(tokens) + events) + '\n'


def write_karaoke_ass(path: Path, words: list[dict[str, Any]], tokens: ThumbnailTokens, *,
                      turns: list[dict[str, Any]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_karaoke_ass(words, tokens, turns=turns), encoding='utf-8', newline='\n')


def generate_phrase_cue_ass(cues: list[dict[str, Any]], tokens: ThumbnailTokens) -> str:
    """Same visual cards for source cues, without pretending to have word alignment."""
    events: list[str] = []
    for cue in cues:
        texts = str(cue['text']).split()
        if not texts:
            continue
        start, end = float(cue['start']), float(cue['end'])
        words = [{'word': text, 'start': start+(end-start)*i/len(texts),
                  'end': start+(end-start)*(i+1)/len(texts)} for i, text in enumerate(texts)]
        for phrase in _phrases(words):
            begin, finish = float(phrase[0]['start']), float(phrase[-1]['end'])
            events.append(_event(0, begin, finish,
                '{\\an7\\pos(230,860)\\bord0\\shad0\\1c&H18251C&\\1a&H55&\\p1}' + PANEL_PATH))
            events.append(_event(2, begin, finish, _text(phrase, None)))
    return '\n'.join(_header(tokens) + events) + '\n'
