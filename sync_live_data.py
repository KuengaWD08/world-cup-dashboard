import os
import django
import requests
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Team, Match

# You can get a free API key at https://www.football-data.org/
API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')

def sync_data():
    if not API_KEY:
        print("No API key found. Please set FOOTBALL_DATA_API_KEY environment variable.")
        print("Falling back to simulation or existing data...")
        return

    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {'X-Auth-Token': API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        for match_data in data.get('matches', []):
            t1_name = match_data['homeTeam']['name']
            t2_name = match_data['awayTeam']['name']
            
            t1, _ = Team.objects.get_or_create(name=t1_name)
            t2, _ = Team.objects.get_or_create(name=t2_name)
            
            match, _ = Match.objects.get_or_create(
                team_1=t1, team_2=t2,
                date=datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00'))
            )
            
            if match_data['status'] == 'FINISHED':
                match.score_1 = match_data['score']['fullTime']['home']
                match.score_2 = match_data['score']['fullTime']['away']
                match.is_finished = True
                match.save()
            elif match_data['status'] == 'IN_PLAY':
                # Update live scores
                match.score_1 = match_data['score']['fullTime']['home']
                match.score_2 = match_data['score']['fullTime']['away']
                match.save()

        print("Sync complete!")
    except Exception as e:
        print(f"Error syncing data: {e}")

if __name__ == '__main__':
    sync_data()
