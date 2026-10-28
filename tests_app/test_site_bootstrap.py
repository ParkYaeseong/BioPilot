"""Site-level bootstrap interval for the complete-case Spearman.

Variants at one position are correlated, so the resampling unit is the site, not
the variant. Everything here is evaluator-only and offline.
"""
import math

import pytest

from evaluation.public_assay import site_bootstrap_spearman


def cohort(sites, per_site=19, *, slope=1.0):
    """Deterministic predicted/observed pairs grouped by site."""
    predicted, observed, ids = {}, {}, []
    letters='CDEFGHIKLMNPQRSTVWY'
    for site in sites:
        for index in range(per_site):
            cid=f'A{site}{letters[index % len(letters)]}'
            if cid in predicted:
                continue
            predicted[cid]=float(index)
            observed[cid]=slope*float(index)
            ids.append(cid)
    return predicted, observed, ids


def test_interval_is_deterministic_for_a_fixed_seed():
    predicted, observed, ids = cohort([32,50,70,90,110,130,150,170,190,205])
    first=site_bootstrap_spearman(predicted, observed, ids, resamples=200, seed=20261027)
    second=site_bootstrap_spearman(predicted, observed, ids, resamples=200, seed=20261027)
    assert first==second
    assert first['seed']==20261027
    assert first['resamples']==200
    assert first['resampling_unit']=='site'


def test_perfect_agreement_interval_is_tight_and_positive():
    predicted, observed, ids = cohort([32,50,70,90,110,130,150,170,190,205])
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=300, seed=7)
    assert result['point_estimate']==pytest.approx(1.0)
    assert result['ci_low']>0.9
    assert result['ci_high']==pytest.approx(1.0)
    assert result['site_count']==10
    assert result['excludes_zero'] is True


def test_inverted_outcome_gives_a_negative_interval():
    predicted, observed, ids = cohort([32,50,70,90,110], slope=-1.0)
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=300, seed=7)
    assert result['point_estimate']==pytest.approx(-1.0)
    assert result['ci_high']<0
    assert result['excludes_zero'] is True


def test_too_few_sites_returns_a_null_interval_with_a_reason():
    predicted, observed, ids = cohort([32])
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=100, seed=1)
    assert result['ci_low'] is None
    assert result['ci_high'] is None
    assert result['site_count']==1
    assert 'site' in result['status']
    assert result['excludes_zero'] is None


def test_interval_brackets_the_point_estimate_on_noisy_data():
    predicted, observed, ids = cohort([32,50,70,90,110,130,150,170,190,205])
    # Break the monotone relation at two sites so the correlation is imperfect.
    for cid in [c for c in ids if c.startswith('A50') or c.startswith('A90')]:
        observed[cid]=-observed[cid]
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=400, seed=99)
    assert result['ci_low']<=result['point_estimate']<=result['ci_high']
    assert -1.0<=result['ci_low']<=1.0
    assert -1.0<=result['ci_high']<=1.0


def test_confidence_level_is_recorded_and_configurable():
    predicted, observed, ids = cohort([32,50,70,90,110,130,150,170,190,205])
    wide=site_bootstrap_spearman(predicted, observed, ids, resamples=400, seed=5, confidence=0.80)
    narrow=site_bootstrap_spearman(predicted, observed, ids, resamples=400, seed=5, confidence=0.95)
    assert wide['confidence']==0.80
    assert narrow['confidence']==0.95
    assert narrow['ci_low']<=wide['ci_low']


def test_unusable_resamples_are_counted_not_silently_dropped():
    predicted, observed, ids = cohort([32,50])
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=200, seed=3)
    assert result['usable_resamples']<=200
    assert result['degenerate_resamples']==200-result['usable_resamples']
    assert result['usable_resamples']>0


def test_interval_never_claims_calibrated_or_biological_meaning():
    predicted, observed, ids = cohort([32,50,70,90,110,130,150,170,190,205])
    result=site_bootstrap_spearman(predicted, observed, ids, resamples=100, seed=1)
    assert result['calibrated_T50'] is False
    assert result['establishes_general_performance'] is False
