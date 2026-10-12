from src.verifier import verify, warning_check, WARNING, alcohol_field, volume_field, text_field


def test_matches_sample_fields():
    ocr = 'OLD TOM DISTILLERY\nKentucky Straight Bourbon Whiskey\n45% Alc./Vol. (90 Proof)\n750 mL\n' + WARNING
    result = verify(ocr, dict(brand='Old Tom Distillery', class_type='Kentucky Straight Bourbon Whiskey', abv='45', net_contents='750 mL'))
    assert result['summary']['matches'] == 4
    assert result['decision'] == 'HUMAN_REVIEW_REQUIRED'
    assert result['checks'][-1]['status'] == 'TEXT_FOUND_REVIEW_FORMAT'


def test_warning_case_matters():
    assert warning_check(WARNING.replace('GOVERNMENT WARNING:', 'Government Warning:')).status == 'REVIEW'


def test_missing_warning():
    assert warning_check('45% Alc/Vol').status == 'REVIEW'


def test_proof_equivalence():
    assert alcohol_field('45', '90 Proof').status == 'MATCH'


def test_volume_equivalence():
    assert volume_field('750 mL', '0.75 L').status == 'MATCH'


def test_no_substring_false_positive():
    assert text_field('Brand', 'OLD TOM', 'OLD TOMMY').status == 'REVIEW'


def test_bad_abv():
    assert alcohol_field('forty-five', '45%').status == 'REVIEW'


def test_empty_optional_field():
    assert text_field('Producer', '', 'Any text').status == 'NOT_CHECKED'
