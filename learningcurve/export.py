from assessment import differences

def work_sample(journey, career, mission, resources, source):
    lines = ['# LearningCurve work sample',
             '**Simulated practice exercise, not employment experience or a professional certification.**',
             f'Target occupation: {career["title"]}', f'Scenario: {mission["title"]}',
             mission['scenario'], mission['provenance'],
             'Skills practiced: ' + ', '.join(s['name'] for s in career['skills'])]
    for i, attempt in enumerate(journey['attempts'], 1):
        lines += [f'\n## Attempt {i}', '\n### Decisions']
        lines += [f'- {h["action"]}: {h["result"]}' for h in attempt['history']]
        lines += ['\n### Customer explanation', attempt['explanation'], '\n### Observed actions']
        lines += [f'- {k}: {"Observed" if v else "Not yet demonstrated"}' for k, v in attempt['criteria'].items()]
        lines += ['\n### Automated writing content checks (not competence ratings)']
        lines += [f'- {k}: {v}' for k, v in attempt['writing'].items()]
        lines += ['Improvement: ' + attempt['improvement'], 'Next step: ' + attempt['next_step']]
    if len(journey['attempts']) == 2:
        lines += ['\n## Revision differences'] + differences(*journey['attempts'])
    lines += ['\n## Recommended next activities']
    for r in resources:
        lines += [f'- {r["title"]}: {r["activity"]} Estimated {r["minutes"]} minutes. {r["cost"]}', r['url'] or 'Original in-app activity.']
    lines += ['\n## Data attribution', source,
              'Occupation-level demand does not establish individual employability. Progress is session-only.']
    return '\n\n'.join(lines)
