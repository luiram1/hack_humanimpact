# Databricks notebook source
# Import this as a Python notebook, or paste each COMMAND section into a cell.
# This notebook runs on notebook compute; the Streamlit app does not use Spark.
display(spark.sql('SHOW TABLES IN thebuilders_luis.oct26_humanedgestudio'))

# COMMAND ----------
dbutils.widgets.text('app_folder', '', 'Absolute /Workspace/.../learningcurve folder')
dbutils.widgets.text('profile_table', '', 'Actual occupation profile table name')
dbutils.widgets.text('skills_table', '', 'Actual occupation skills table name')
dbutils.widgets.text('skill_id_column', '', 'Actual skill ID column from source')
dbutils.widgets.text('geography', '', 'Exact Massachusetts geography label')
dbutils.widgets.dropdown('percent_scale', 'UNSET', ['UNSET', 'percent', 'fraction'])
dbutils.widgets.text('dataset_version', '2026-10-12', 'Dataset version (verify with source)')

# COMMAND ----------
# Set the widgets before running this cell. Do not guess table or column names.
import re
import sys
from pathlib import Path

folder = Path(dbutils.widgets.get('app_folder'))
if not folder.is_absolute() or not (folder / 'scripts' / 'prepare_data.py').is_file():
    raise ValueError('Set app_folder to the absolute Workspace path containing the supplied app files.')
sys.path.insert(0, str(folder))
from scripts.prepare_data import prepare, write_prepared

def source_table(widget):
    table = dbutils.widgets.get(widget)
    if not re.fullmatch(r'[A-Za-z0-9_]+', table):
        raise ValueError(f'Set {widget} to a table name from the first cell; letters, digits and underscores only.')
    return spark.table(f'thebuilders_luis.oct26_humanedgestudio.{table}')

profile_source = source_table('profile_table')
skill_source = source_table('skills_table')
print('Profile columns:', profile_source.columns)
print('Skill columns:', skill_source.columns)
display(skill_source.select('geography').distinct())

# COMMAND ----------
# Inspect source columns and the supplied data dictionary before setting units.
from pyspark.sql import functions as F
occupation = '15-1232.00'
profile = profile_source.where(F.col('onet') == occupation).toPandas()
skills = skill_source.where((F.col('onet') == occupation) &
                           (F.col('geography') == dbutils.widgets.get('geography'))).toPandas()
result = prepare(profile, skills,
                 skill_id_column=dbutils.widgets.get('skill_id_column'),
                 geography=dbutils.widgets.get('geography'),
                 percent_scale=dbutils.widgets.get('percent_scale'),
                 version=dbutils.widgets.get('dataset_version'))
destination = folder / 'data' / 'prepared' / 'evidence.json'
write_prepared(result, destination)
print(f'Prepared {destination}. Redeploy the app to include this snapshot.')
