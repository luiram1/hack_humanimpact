def recommend(resources, minutes, free_only, skill_ids, budgets=None):
    if minutes not in (15, 30, 60):
        raise ValueError('Choose 15, 30, or 60 minutes.')
    allowed = budgets if budgets is not None else (['Free'] if free_only else ['Free', 'Paid'])
    return [r for r in resources if r['minutes'] <= minutes
            and ('Paid' if r['paid'] else 'Free') in allowed and set(r['skills']).intersection(skill_ids)]
