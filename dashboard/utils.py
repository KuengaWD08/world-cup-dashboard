from dashboard.models import Participant, Match, Team, TeamPick

def get_implied_probability(american_odds):
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100) * 100

def get_form_points(team, matches):
    pts = 0
    max_pts = 0
    for m in matches:
        if m.team_1 == team or m.team_2 == team:
            max_pts += 3
            if m.score_1 is not None and m.score_2 is not None:
                if m.team_1 == team:
                    if m.score_1 > m.score_2: pts += 3
                    elif m.score_1 == m.score_2: pts += 1
                else:
                    if m.score_2 > m.score_1: pts += 3
                    elif m.score_2 == m.score_1: pts += 1
    return pts, max_pts

def get_blend_weights(matches_played_count):
    if matches_played_count == 0:
        return 1.0, 0.0
    elif matches_played_count <= 48:
        return 0.6, 0.4
    elif matches_played_count <= 56:
        return 0.4, 0.6
    elif matches_played_count <= 60:
        return 0.3, 0.7
    elif matches_played_count <= 62:
        return 0.2, 0.8
    else:
        return 0.1, 0.9

def calculate_probabilities():
    participants = list(Participant.objects.all())
    finished_matches = list(Match.objects.filter(is_finished=True))
    
    # Get only teams that have been picked by participants (17 teams only)
    picked_team_names = set()
    for p in participants:
        for pick in p.team_picks.all():
            picked_team_names.add(pick.team.name)
    
    # Only work with picked teams (ignore the other 31 teams)
    all_teams = list(Team.objects.filter(name__in=picked_team_names))
    active_teams = [t for t in all_teams if not t.is_eliminated]

    if not active_teams:
        return []

    # 1. Normalized Implied Odds Probability (active picked teams only)
    implied_probs = {}
    total_implied = 0
    for t in active_teams:
        p = get_implied_probability(t.american_odds)
        implied_probs[t.id] = p
        total_implied += p

    normalized_odds_probs = {tid: (p / total_implied) * 100 for tid, p in implied_probs.items()} if total_implied > 0 else {t.id: 0 for t in active_teams}

    # 2. Form Probability
    form_scores = {}
    total_form_pct = 0
    for t in active_teams:
        pts, max_pts = get_form_points(t, finished_matches)
        form_pct = (pts / max_pts * 100) if max_pts > 0 else 0
        form_scores[t.id] = form_pct
        total_form_pct += form_pct

    if total_form_pct > 0:
        normalized_form_probs = {tid: (p / total_form_pct) * 100 for tid, p in form_scores.items()}
    else:
        normalized_form_probs = {tid: 0 for tid in form_scores}

    # 3. Blend
    odds_w, form_w = get_blend_weights(len(finished_matches))

    final_team_probs = {}
    for t in active_teams:
        p = (odds_w * normalized_odds_probs[t.id]) + (form_w * normalized_form_probs.get(t.id, 0))
        final_team_probs[t.id] = p

    total_final = sum(final_team_probs.values())
    if total_final > 0:
        final_team_probs = {tid: (p / total_final) * 100 for tid, p in final_team_probs.items()}

    # 4. Build team lookup for at_risk (bottom of group — form % below threshold)
    # A team is "at risk" if it has played matches but has 0 form points
    at_risk_ids = set()
    for t in active_teams:
        pts, max_pts = get_form_points(t, finished_matches)
        if max_pts > 0 and pts == 0:
            at_risk_ids.add(t.id)

    # 5. Participant results — now includes picks list
    participant_results = []
    for participant in participants:
        member_prob = 0
        picks_data = []
        picks = participant.team_picks.all()

        for pick in picks:
            team = pick.team
            member_prob += final_team_probs.get(team.id, 0)
            picks_data.append({
                'team': team.name,
                'is_eliminated': team.is_eliminated,
                'at_risk': team.id in at_risk_ids and not team.is_eliminated,
            })

        participant_results.append({
            'name': participant.name,
            'probability': round(member_prob, 2),
            'current_points': sum(
                get_form_points(pick.team, finished_matches)[0]
                for pick in picks
            ),
            'teams': ', '.join([p['team'] for p in picks_data]),
            'picks': picks_data,  # ← this is what the template now uses
        })

    return sorted(participant_results, key=lambda x: x['probability'], reverse=True)