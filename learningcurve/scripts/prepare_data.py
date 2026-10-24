"""Reproducible CSV/table preparation with explicit source semantics."""
import argparse
import json
from pathlib import Path
import pandas as pd

OCCUPATION = 'Computer User Support Specialists'
CODE = '15-1232.00'
PROFILE_COLUMNS = ['onet', 'onet_name', 'year', 'period', 'months_covered',
                   'ma_job_postings', 'ma_pct_postings_genai_skills', 'ma_confidence_flag']
SKILL_COLUMNS = ['onet', 'year', 'geography', 'skill_name', 'skill_type',
                 'pct_postings', 'confidence_flag']

def require(frame, columns, label):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f'{label}: missing columns {sorted(missing)}. Available: {list(frame.columns)}')
    if frame[columns].isna().any().any():
        raise ValueError(f'{label}: required columns contain nulls.')

def numeric(frame, columns):
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors='raise')
        if not frame[column].map(lambda x: float('-inf') < x < float('inf')).all():
            raise ValueError(f'{column} contains non-finite values.')

def prepare(profile, skills, *, skill_id_column, geography, percent_scale, version):
    profile, skills = profile.copy(), skills.copy()
    require(profile, PROFILE_COLUMNS, 'Occupation profile')
    require(skills, SKILL_COLUMNS + [skill_id_column], 'Skills')
    numeric(profile, ['year', 'months_covered', 'ma_job_postings', 'ma_pct_postings_genai_skills'])
    numeric(skills, ['year', 'pct_postings'])
    if profile.duplicated(['onet', 'year']).any():
        raise ValueError('Profile must have one row per occupation/year. Do not sum duplicate counts.')
    if skills.duplicated(['onet', 'year', 'geography', 'skill_type', skill_id_column]).any():
        raise ValueError('Duplicate occupation/year/geography/skill-type/skill-ID keys.')
    if not profile['months_covered'].between(1, 12).all() or (profile['ma_job_postings'] < 0).any():
        raise ValueError('Invalid month coverage or posting counts.')
    for frame, cols in [(profile, ['year', 'months_covered', 'ma_job_postings']), (skills, ['year'])]:
        if any((frame[c] % 1 != 0).any() for c in cols):
            raise ValueError('Years, month coverage, and posting counts must be integers.')
    selected = profile[profile['onet_name'].str.casefold() == OCCUPATION.casefold()].copy()
    if selected.empty or set(selected['onet'].astype(str)) != {CODE}:
        raise ValueError(f'Expected {OCCUPATION} with source code {CODE}; inspect source mapping.')
    if ((selected['year'] == 2026) & (selected['months_covered'] != 9)).any():
        raise ValueError('Expected January–September coverage (9 months) for 2026; inspect the source version.')
    complete = selected[selected['months_covered'] == 12]
    if complete.empty:
        raise ValueError('No complete year is available for skill selection.')
    year = int(complete['year'].max())
    chosen = skills[(skills['onet'].astype(str) == CODE) & (skills['year'] == year)
                    & (skills['geography'] == geography)].copy()
    if chosen.empty:
        raise ValueError(f'No skill rows for {CODE}, {year}, {geography!r}. Check geography labels.')
    if percent_scale not in ('percent', 'fraction'):
        raise ValueError('Explicitly choose percent or fraction from the data dictionary.')
    for frame, col in [(selected, 'ma_pct_postings_genai_skills'), (chosen, 'pct_postings')]:
        maximum = 1 if percent_scale == 'fraction' else 100
        if not frame[col].between(0, maximum).all():
            raise ValueError(f'{col} is outside the selected {percent_scale} range.')
        if percent_scale == 'fraction':
            frame[col] *= 100
    selected.loc[selected['year'] == 2026, 'period'] = 'January–September — partial year'
    if skill_id_column != 'skill_id':
        chosen = chosen.rename(columns={skill_id_column: 'skill_id'})
    return {'version': version, 'illustrative': False, 'source': 'Data Source: Lightcast, 2026',
            'occupation': OCCUPATION, 'onet': CODE, 'geography': 'Massachusetts',
            'source_geography_label': geography, 'skill_year': year,
            'profile': json.loads(selected.sort_values('year').to_json(orient='records')),
            'skills': json.loads(chosen.sort_values('pct_postings', ascending=False).to_json(orient='records'))}

def write_prepared(data, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/prepared/evidence.json')
    parser.add_argument('--skill-id-column', required=True)
    parser.add_argument('--geography', required=True, help='Exact Massachusetts label from source')
    parser.add_argument('--percent-scale', choices=['percent', 'fraction'], required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    files = [args.input_dir / name for name in ['lc_occupation_ai_profile.csv', 'lc_occupation_skills.csv']]
    if not all(p.is_file() for p in files):
        parser.error('Both source CSV files are required. App remains runnable with the separately labeled illustrative fixture.')
    profile, skills = [pd.read_csv(p, dtype={'onet': str}) for p in files]
    result = prepare(profile, skills, skill_id_column=args.skill_id_column,
                     geography=args.geography, percent_scale=args.percent_scale, version=args.version)
    write_prepared(result, args.output)
    print(f'Prepared {args.output}. No joins or posting-count aggregation performed.')

if __name__ == '__main__':
    main()
