from assessment import differences
from simulation import shift_records

def work_sample(journey, career, mission, resources, source):
    lines = ['# LearningCurve work sample',
             '**Simulated practice exercise, not employment experience or a professional certification.**',
             f'Target occupation: {career["title"]}',
             'Skills practiced: ' + ', '.join(s['name'] for s in career['skills'])]
    records = shift_records(journey, mission) or [{'scenario': mission, 'attempts': []}]
    for number, record in enumerate(records, 1):
        scenario = record['scenario']
        lines += [f'\n## Shift {number}: {scenario["title"]}', f'Scenario: {scenario["title"]}',
                  scenario['scenario'], scenario['provenance']]
        lines += attempt_sections(record['attempts'])
    lines += ['\n## Recommended next activities']
    for r in resources:
        lines += [f'- {r["title"]}: {r["activity"]} Estimated {r["minutes"]} minutes. {r["cost"]}', r['url'] or 'Original in-app activity.']
    lines += ['\n## Data attribution', source,
              'Occupation-level demand does not establish individual employability. Progress is session-only.']
    return '\n\n'.join(lines)


def attempt_sections(attempts):
    lines = []
    for i, attempt in enumerate(attempts, 1):
        lines += [f'\n## Attempt {i}', '\n### Decisions']
        lines += [f'- {h["action"]}: {h["result"]}' for h in attempt['history']]
        lines += ['\n### Customer explanation', attempt['explanation'], '\n### Observed actions']
        lines += [f'- {k}: {"Observed" if v else "Not yet demonstrated"}' for k, v in attempt['criteria'].items()]
        lines += ['\n### Automated writing content checks (not competence ratings)']
        lines += [f'- {k}: {v}' for k, v in attempt['writing'].items()]
        lines += ['Improvement: ' + attempt['improvement'], 'Next step: ' + attempt['next_step']]
        if attempt.get('dialogue'):
            lines += ['\n### Customer conversation']
            for turn in attempt['dialogue']:
                lines += ['Question: ' + turn['question'], 'Customer: ' + turn['reply'],
                          'Recorded observation: ' + turn['observation']]
    if len(attempts) == 2:
        lines += ['\n## Revision differences'] + differences(*attempts)
    return lines
