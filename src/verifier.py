"""Deterministic, review-oriented checks of OCR text against application fields.

This tool is decision support only; it never issues a regulatory approval.
"""
from __future__ import annotations
import re
import math
import unicodedata
from dataclasses import dataclass, asdict
from typing import Optional

WARNING = ("GOVERNMENT WARNING: (1) According to the Surgeon General, women should not "
           "drink alcoholic beverages during pregnancy because of the risk of birth defects. "
           "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
           "operate machinery, and may cause health problems.")

@dataclass
class Check:
    field: str
    expected: str
    observed: str
    status: str
    note: str

    def to_dict(self):
        return asdict(self)


def normalize(s: str) -> str:
    s = unicodedata.normalize('NFKC', s or '').casefold()
    s = s.replace('’', "'").replace('‘', "'")
    return re.sub(r'[^\w]+', ' ', s).strip()


def compact(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def text_field(field: str, expected: str, ocr: str) -> Check:
    if not expected.strip():
        return Check(field, expected, '', 'NOT_CHECKED', 'No application value supplied')
    target = normalize(expected)
    haystack = normalize(ocr)
    # Word boundaries avoid a false match of "ABC" in "ABCD".
    found = bool(re.search(r'(?<!\w)' + re.escape(target) + r'(?!\w)', haystack)) if target else False
    return Check(field, expected, expected if found else '', 'MATCH' if found else 'REVIEW',
                 'Text found after case/punctuation normalization' if found else
                 'Expected text not confidently found; inspect original label')


def alcohol_field(expected: str, ocr: str) -> Check:
    if not expected.strip():
        return Check('Alcohol content (ABV)', '', '', 'NOT_CHECKED', 'No application ABV supplied')
    try:
        number = float(expected.replace('%', '').strip())
    except ValueError:
        return Check('Alcohol content (ABV)', expected, '', 'REVIEW', 'Application ABV must be numeric')
    if not math.isfinite(number) or not 0 <= number <= 100:
        return Check('Alcohol content (ABV)', expected, '', 'REVIEW', 'Application ABV must be between 0 and 100')
    # Accept common ABV/Alc. Vol. variants, not arbitrary numbers in the image.
    candidates = re.findall(r'(?<!\d)(\d{1,2}(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?\.?\s*(?:/\s*)?vol\.?|abv)?', ocr, re.I)
    # Also accept e.g. "Alc. 45% by Vol." and "90 Proof".
    candidates += re.findall(r'alc(?:ohol)?\.?\s*(\d{1,2}(?:\.\d+)?)\s*%', ocr, re.I)
    proof = re.findall(r'(?<!\d)(\d{1,3}(?:\.\d+)?)\s*proof\b', ocr, re.I)
    values = [float(v) for v in candidates] + [float(p)/2 for p in proof]
    matched = any(abs(v - number) < .011 for v in values)
    observed = ', '.join(f'{v:g}%' for v in sorted(set(values)))
    return Check('Alcohol content (ABV)', expected, observed, 'MATCH' if matched else 'REVIEW',
                 'Numeric ABV/proof evidence detected' if matched else 'No matching ABV/proof detected')


def volume_field(expected: str, ocr: str) -> Check:
    if not expected.strip():
        return Check('Net contents', '', '', 'NOT_CHECKED', 'No application volume supplied')
    def volume(s):
        match = re.search(r'(?<!\d)(\d+(?:\.\d+)?)\s*(ml|millilit(?:er|re)s?|l|lit(?:er|re)s?)\b', s, re.I)
        if not match:
            return None
        qty = float(match.group(1))
        unit = match.group(2).lower()
        return qty * 1000 if unit in ('l', 'liter', 'litre', 'liters', 'litres') else qty
    target = volume(expected)
    observed = re.findall(r'(?<!\d)\d+(?:\.\d+)?\s*(?:ml|millilit(?:er|re)s?|l|lit(?:er|re)s?)\b', ocr, re.I)
    matched = target is not None and any(abs(volume(v)-target)<.01 for v in observed)
    return Check('Net contents', expected, ', '.join(observed), 'MATCH' if matched else 'REVIEW',
                 'Equivalent volume detected' if matched else 'Volume missing or different')


def warning_check(ocr: str) -> Check:
    # OCR text cannot establish typography (bold), font size, or physical placement.
    # Preserve exact wording requirement: ignore line breaks only; never ignore case/punctuation.
    actual = compact(ocr)
    expected = compact(WARNING)
    found = expected in actual
    heading = 'GOVERNMENT WARNING:' in actual
    return Check('Government health warning', WARNING, 'Full text detected' if found else
                 ('Heading detected; full text not detected' if heading else 'Not detected'),
                 'TEXT_FOUND_REVIEW_FORMAT' if found else 'REVIEW',
                 'Verify bold uppercase heading, readability, placement and formatting visually' if found else
                 'Exact warning text not detected; inspect the original image and typography')


def verify(ocr_text: str, application: dict) -> dict:
    fields = [
        text_field('Brand name', str(application.get('brand', '')), ocr_text),
        text_field('Class/type', str(application.get('class_type', '')), ocr_text),
        alcohol_field(str(application.get('abv', '')), ocr_text),
        volume_field(str(application.get('net_contents', '')), ocr_text),
        text_field('Producer/bottler', str(application.get('producer', '')), ocr_text),
        text_field('Producer address', str(application.get('address', '')), ocr_text),
        text_field('Country of origin', str(application.get('country', '')), ocr_text),
        warning_check(ocr_text),
    ]
    return {'checks': [c.to_dict() for c in fields],
            'summary': {'matches': sum(c.status == 'MATCH' for c in fields),
                        'review': sum(c.status in ('REVIEW', 'TEXT_FOUND_REVIEW_FORMAT') for c in fields),
                        'not_checked': sum(c.status == 'NOT_CHECKED' for c in fields)},
            'decision': 'HUMAN_REVIEW_REQUIRED'}
