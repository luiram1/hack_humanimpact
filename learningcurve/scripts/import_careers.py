"""Validate the user's two-file Databricks ZIP and build a reproducible snapshot."""
import argparse
import csv
import io
import json
import math
from pathlib import Path
import zipfile

def prepare_zip(path):
    with zipfile.ZipFile(path) as archive:
        occupations = list(csv.DictReader(io.TextIOWrapper(archive.open('occupations.csv'), encoding='utf-8-sig')))
        packed = list(csv.DictReader(io.TextIOWrapper(archive.open('occupation_skills.csv'), encoding='utf-8-sig')))
    result = {}
    for item in occupations:
        if not item['onet'] or not item['onet_name'] or item['onet'] in result:
            raise ValueError('Invalid or duplicate occupation code.')
        result[item['onet']] = {'name': item['onet_name'], 'skills': []}
    packed_ids = set()
    for item in packed:
        code = item['onet']
        if code not in result or code in packed_ids or item['onet_name'] != result[code]['name']:
            raise ValueError('Unknown, duplicate, or mismatched occupation in skills export.')
        packed_ids.add(code)
        rows = json.loads(item['skills_json'])
        keys, counts = set(), set()
        for row in rows:
            for field in ('skill_id', 'skill_name', 'skill_type', 'confidence_flag', 'period'):
                if not isinstance(row.get(field), str) or not row[field]:
                    raise ValueError(f'Missing {field} for {code}')
            if row['year'] != 2025 or row['months_covered'] != 12:
                raise ValueError('Expected 2025 full-year data.')
            for field in ('pct_postings', 'job_postings', 'skill_rank'):
                row[field] = float(row[field])
                if not math.isfinite(row[field]) or row[field] < 0:
                    raise ValueError('Invalid numeric source value.')
            if row['pct_postings'] > 100:
                raise ValueError('Percentage exceeds 100.')
            key = (row['skill_type'], row['skill_id'])
            if key in keys:
                raise ValueError('Duplicate source skill key.')
            keys.add(key)
            counts.add(row['job_postings'])
        if len(counts) > 1:
            raise ValueError('Inconsistent posting denominator for one occupation.')
        result[code]['skills'] = sorted(rows, key=lambda r: (r['skill_type'], r['skill_rank'], r['skill_id']))
    return {'source': 'Data Source: Lightcast, 2026', 'geography': 'Massachusetts',
            'year': 2025, 'months_covered': 12, 'version': 'user-export-2026-10-24',
            'occupations': result}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zip_path', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/prepared/careers.json')
    args = parser.parse_args()
    data = prepare_zip(args.zip_path)
    args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    print(f"{len(data['occupations'])} occupations; {sum(bool(c['skills']) for c in data['occupations'].values())} with skill rows")
