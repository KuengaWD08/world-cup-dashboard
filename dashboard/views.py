import json
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from .utils import calculate_probabilities
from .models import Match, Team, Participant
import pytz

def dashboard(request):
    probs = calculate_probabilities()
    
    bhutan_tz = pytz.timezone('Asia/Thimphu')

    # Get all teams that have been picked by anyone
    picked_team_ids = set()
    for p in probs:
        for pick in p['picks']:
            picked_team_ids.add(pick['team'])

    # Fetch upcoming matches involving picked teams only
    picked_teams = Team.objects.filter(name__in=picked_team_ids)
    
    upcoming_matches_raw = Match.objects.filter(
        is_finished=False,
        team_1__in=picked_teams
    ).union(
        Match.objects.filter(
            is_finished=False,
            team_2__in=picked_teams
        )
    ).order_by('date')[:20]

    # Build upcoming matches with player names and Bhutan time
    upcoming_matches = []
    for match in upcoming_matches_raw:
        # Find players who picked either team
        team1_pickers = [
            p['name'].split()[0]  # first name only
            for p in probs
            if any(pick['team'] == match.team_1.name for pick in p['picks'])
        ]
        team2_pickers = [
            p['name'].split()[0]
            for p in probs
            if any(pick['team'] == match.team_2.name for pick in p['picks'])
        ]

        # Convert to Bhutan time
        match_time_bht = match.date.astimezone(bhutan_tz)

        upcoming_matches.append({
            'team1': match.team_1.name,
            'team2': match.team_2.name,
            'team1_pickers': team1_pickers,
            'team2_pickers': team2_pickers,
            'date': match_time_bht.strftime('%b %d'),
            'time': match_time_bht.strftime('%I:%M %p'),
            'timezone': 'BHT',
        })

    # Limit to next 2 matches per picked team
    seen_teams = set()
    filtered_matches = []
    for m in upcoming_matches:
        t1, t2 = m['team1'], m['team2']
        if picked_team_ids & {t1, t2}:
            key = f"{t1}_{t2}"
            if key not in seen_teams:
                seen_teams.add(key)
                filtered_matches.append(m)
        if len(filtered_matches) >= 10:
            break

    chart_data = json.dumps([
        {'name': p['name'], 'probability': p['probability']}
        for p in probs
    ])

    context = {
        'probabilities': probs,
        'chart_data': chart_data,
        'upcoming_matches': filtered_matches,
        'last_updated': timezone.now().strftime('%b %d, %Y %H:%M UTC'),
    }
    return render(request, 'dashboard/index.html', context)