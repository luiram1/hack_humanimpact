import json
import os
from urllib.parse import urlparse
import pandas as pd
from models import ROOT
from scripts.prepare_data import prepare

PROFILE_TABLE = 'thebuilders_luis.oct26_humanedgestudio.lc_occupation_ai_profile'
SKILLS_TABLE = 'thebuilders_luis.oct26_humanedgestudio.lc_occupation_skills'
OCCUPATION_CODE = '15-1232.00'

LIMITATIONS = '''Postings measure advertised demand, not hires or employment. GenAI demand is the share of postings explicitly requesting listed GenAI skills. AI exposure is not a probability of job loss, and exposure scores are fixed across years in this dataset. Broad AI-skill indicators include Python and are not direct measures of GenAI use. Top-ranked skills are not exhaustive occupational requirements. Posting-volume confidence flags are not statistical confidence intervals. Occupation demand cannot establish individual employability. Massachusetts aggregates do not establish Worcester-specific demand. These data do not establish experience requirements, wages, demographic effects, an apprenticeship shortage, or causal effects of AI. Demand for a skill does not validate this exact simulation.'''

def load_data(directory=None):
    warehouse_id = os.getenv('DATABRICKS_WAREHOUSE_ID')
    if warehouse_id:
        return load_live_data(warehouse_id)

    directory = directory or ROOT / 'data' / 'prepared'
    actual = directory / 'evidence.json'
    path = actual if actual.exists() else directory / 'illustrative.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('source', 'illustrative', 'profile', 'skills', 'skill_year', 'version'):
        if key not in data:
            raise ValueError(f'{path.name} is missing {key}; rerun data preparation.')
    if not data['profile'] or not data['skills']:
        raise ValueError('Prepared evidence is empty. Rerun data preparation.')
    return data

def load_live_data(warehouse_id):
    host = os.getenv('DATABRICKS_HOST')
    if not host:
        raise ValueError('DATABRICKS_HOST is not available in the app environment.')

    from databricks import sql
    from databricks.sdk.core import Config
    server_hostname = urlparse(host if '://' in host else f'https://{host}').hostname

    def query(table):
        statement = f'SELECT * FROM {table} WHERE onet = ?'
        if table == SKILLS_TABLE:
            statement += ' AND geography = ?'
            parameters = (OCCUPATION_CODE, 'MA')
        else:
            parameters = (OCCUPATION_CODE,)
        with sql.connect(
            server_hostname=server_hostname,
            http_path=f'/sql/1.0/warehouses/{warehouse_id}',
            credentials_provider=Config().authenticate,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, parameters)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    profile = query(PROFILE_TABLE)
    skills = query(SKILLS_TABLE)
    if not profile or not skills:
        raise ValueError('Databricks returned no profile or skill rows for occupation 15-1232.00 in MA.')
    data = prepare(
        pd.DataFrame(profile),
        pd.DataFrame(skills),
        skill_id_column='skill_id',
        geography='MA',
        percent_scale='percent',
        version='Live Databricks data',
    )
    data['source'] = 'Live Databricks tables: ' + PROFILE_TABLE + ' and ' + SKILLS_TABLE
    data['live'] = True
    return data

def skill_shares(data, skills):
    # Only exact labels; do not claim a related source skill is an identical construct.
    return {s['id']: max((float(row['pct_postings']) for row in data['skills']
                         if row['skill_name'].casefold() == s['name'].casefold()), default=0)
            for s in skills}
