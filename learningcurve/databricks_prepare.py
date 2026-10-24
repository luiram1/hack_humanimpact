# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
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

base = "thebuilders_luis.oct26_humanedgestudio"

profile = spark.table(f"{base}.lc_occupation_ai_profile")
skills = spark.table(f"{base}.lc_occupation_skills")

print("PROFILE COLUMNS:", profile.columns)
print("SKILL COLUMNS:", skills.columns)

display(skills.select("geography").distinct())

# COMMAND ----------

base = "thebuilders_luis.oct26_humanedgestudio"

rows = [
    (name, field.name, field.dataType.simpleString())
    for name in ["lc_occupation_ai_profile", "lc_occupation_skills"]
    for field in spark.table(f"{base}.{name}").schema.fields
]

display(spark.createDataFrame(
    rows, ["table_name", "column_name", "data_type"]
))

# COMMAND ----------

display(spark.sql("""
    SELECT
        skill_name,
        job_postings,
        job_postings_with_skill,
        pct_postings AS stored_value,
        ROUND(
            100.0 * job_postings_with_skill / job_postings, 2
        ) AS calculated_percentage
    FROM thebuilders_luis.oct26_humanedgestudio.lc_occupation_skills
    WHERE geography = 'MA'
      AND onet = '15-1232.00'
      AND year = 2025
      AND job_postings > 0
      AND job_postings_with_skill > 0
    ORDER BY skill_rank
    LIMIT 5
"""))

# COMMAND ----------

display(spark.sql("""
    SELECT column_name, comment
    FROM thebuilders_luis.information_schema.columns
    WHERE table_schema = 'oct26_humanedgestudio'
      AND table_name = 'lc_occupation_ai_profile'
      AND column_name IN (
          'ma_pct_postings_genai_skills',
          'ma_pct_postings_ai_skills',
          'ma_job_postings'
      )
"""))

# COMMAND ----------

import sys
from pathlib import Path

folder = Path(
    "/Workspace/Users/lramirez@g.holycross.edu/"
    "hack_humanimpact/learningcurve"
)

if not (folder / "scripts" / "prepare_data.py").is_file():
    raise ValueError(f"Preparation script not found inside {folder}")

sys.path.insert(0, str(folder))
from scripts.prepare_data import prepare, write_prepared

base = "thebuilders_luis.oct26_humanedgestudio"

profile_source = spark.table(f"{base}.lc_occupation_ai_profile")
skill_source = spark.table(f"{base}.lc_occupation_skills")

print("Profile columns:", profile_source.columns)
print("Skill columns:", skill_source.columns)

display(skill_source.select("geography").distinct())

# COMMAND ----------

from pyspark.sql import functions as F

occupation = "15-1232.00"

# Read the selected occupation and Massachusetts skills.
profile = profile_source.where(
    F.col("onet") == occupation
).toPandas()

skills = skill_source.where(
    (F.col("onet") == occupation) &
    (F.col("geography") == "MA")
).toPandas()

# Skills percentages are verified.
# GenAI profile percentage units are still an explicit assumption.
result = prepare(
    profile,
    skills,
    skill_id_column="skill_id",
    geography="MA",
    percent_scale="percent",
    version="shared-table-snapshot; source version unverified"
)

result["source"] += (
    " | Caution: skills percentage units verified from counts; "
    "GenAI profile units assumed to be percentages (0–100), "
    "not yet verified. Do not interpret the GenAI chart as "
    "validated findings."
)

destination = folder / "data" / "prepared" / "evidence.json"
write_prepared(result, destination)

print(f"Prepared: {destination}")
print("Caution: GenAI percentage units remain unverified.")
print("Redeploy the Databricks App to load this snapshot.")