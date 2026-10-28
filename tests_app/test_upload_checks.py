"""Local checks over operator-supplied files. They diagnose; they never predict.

An uploaded file is analysed in memory and never leaves the machine. These checks
make no scientific claim: they answer "is this the protein this tool is registered
for" and "does your numbering actually join to your coordinates", which is the class
of silent error that a sequence-index viewer would otherwise present as evidence.
"""
from pathlib import Path

import pytest

from app.upload_checks import (MAX_SEQUENCE_BYTES, MAX_STRUCTURE_BYTES, check_sequence,
                               check_structure)

ROOT = Path(__file__).resolve().parents[1]
FULL = (ROOT / 'reference/lipase_full_212.fasta').read_text(encoding='utf-8')
DEPOSITED = (ROOT / 'reference/1ISP_A_deposited_181.fasta').read_text(encoding='utf-8')
CIF = (ROOT / 'reference/1ISP.cif').read_text(encoding='utf-8')


def test_the_registered_reference_is_recognised():
    result = check_sequence(FULL)
    assert result['verdict'] == 'registered_reference'
    assert result['length'] == 212
    assert result['reviewable'] is True


def test_the_deposited_mature_sequence_is_named_rather_than_silently_accepted():
    """Mature 181 is a real part of the contract, but it is not the review frame."""
    result = check_sequence(DEPOSITED)
    assert result['verdict'] == 'registered_mature_sequence'
    assert result['length'] == 181
    assert result['reviewable'] is False
    assert 'full' in result['detail'].lower()


def test_an_unrelated_protein_is_refused_with_the_reason():
    result = check_sequence('>other\n' + 'ACDEFGHIKLMNPQRSTVWY' * 5)
    assert result['verdict'] == 'not_the_registered_target'
    assert result['reviewable'] is False
    assert 'registered' in result['detail'].lower()


@pytest.mark.parametrize('text', ['', '>only a header\n', '>x\nACDEFG!!!\n', '>x\nZZZZ'])
def test_unreadable_sequence_input_is_refused(text):
    result = check_sequence(text)
    assert result['verdict'] == 'unreadable'
    assert result['reviewable'] is False


def test_oversized_sequence_input_is_refused_without_parsing():
    result = check_sequence('A' * (MAX_SEQUENCE_BYTES + 1))
    assert result['verdict'] == 'too_large'


def test_the_real_structure_join_is_reported_in_full():
    result = check_structure(CIF, DEPOSITED, chain='A')
    assert result['verdict'] == 'join_verified'
    assert result['deposited_residue_count'] == 181
    assert result['modelled_residue_count'] == 179
    assert result['unmodelled_positions'] == [1, 181]
    assert result['auth_minus_label_offsets'] == [0]
    assert result['insertion_codes'] == []
    assert result['identity_mismatches'] == []


def test_a_sequence_that_does_not_match_the_structure_is_diagnosed_not_crashed():
    """The importer fails closed; the diagnostic tool must explain instead."""
    broken = DEPOSITED.split('\n', 1)[1].replace('\n', '')
    broken = '>mismatch\n' + 'W' + broken[1:]
    result = check_structure(CIF, broken, chain='A')
    assert result['verdict'] == 'identity_disagreement'
    assert 'identity' in result['detail'].lower()


def test_a_length_disagreement_is_diagnosed():
    short = '>short\n' + DEPOSITED.split('\n', 1)[1].replace('\n', '')[:100]
    result = check_structure(CIF, short, chain='A')
    assert result['verdict'] == 'length_disagreement'


def test_an_absent_chain_is_reported_rather_than_guessed():
    result = check_structure(CIF, DEPOSITED, chain='Z')
    assert result['verdict'] == 'chain_not_found'


def test_oversized_structure_input_is_refused_without_parsing():
    result = check_structure('x' * (MAX_STRUCTURE_BYTES + 1), DEPOSITED)
    assert result['verdict'] == 'too_large'


def test_a_file_that_is_not_mmcif_is_refused_clearly():
    result = check_structure('just some text, not a structure', DEPOSITED)
    assert result['verdict'] in ('not_mmcif', 'chain_not_found')
    assert result['detail']


def test_no_check_ever_reports_a_biological_claim():
    for result in (check_sequence(FULL), check_structure(CIF, DEPOSITED)):
        blob = ' '.join(str(v) for v in result.values()).lower()
        for forbidden in ('t50', 'thermostab', 'activity improve', 'better variant'):
            assert forbidden not in blob
