import pandas as pd
import pytest
from models import ROOT
from data_access import load_data
from scripts.prepare_data import prepare

def frames():
    d = load_data()
    p = pd.DataFrame(d['profile']).assign(onet='15-1232.00', onet_name='Computer User Support Specialists')
    s = pd.DataFrame(d['skills']).assign(onet='15-1232.00', year=2025, geography='Massachusetts')
    return p, s

def run(p, s):
    return prepare(p, s, skill_id_column='skill_id', geography='Massachusetts', percent_scale='percent', version='test')

def test_counts_and_partial_year():
    p, s = frames()
    result = run(p, s)
    assert sum(r['ma_job_postings'] for r in result['profile']) == p.ma_job_postings.sum()
    assert result['skill_year'] == 2025
    assert 'partial year' in result['profile'][-1]['period']

def test_duplicate_keys_and_invalid_schema_fail():
    p, s = frames()
    with pytest.raises(ValueError, match='one row'):
        run(pd.concat([p, p.iloc[[0]]]), s)
    with pytest.raises(ValueError, match='Duplicate'):
        run(p, pd.concat([s, s.iloc[[0]]]))
    with pytest.raises(ValueError, match='missing columns'):
        run(p.drop(columns='ma_job_postings'), s)

def test_invalid_prepared_data_never_silently_falls_back(tmp_path):
    (tmp_path / 'evidence.json').write_text('{}')
    with pytest.raises(ValueError):
        load_data(tmp_path)
