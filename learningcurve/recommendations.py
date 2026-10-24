def recommend(resources, minutes, free_only, skill_ids):
    if minutes not in (15, 30, 60):
        raise ValueError('Choose 15, 30, or 60 minutes.')
    return [r for r in resources if r['minutes'] <= minutes
            and (not free_only or not r['paid']) and set(r['skills']).intersection(skill_ids)]
