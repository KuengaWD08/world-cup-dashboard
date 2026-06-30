import os
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Team, Match


class Command(BaseCommand):
    help = 'Syncs live World Cup scores from football-data.org'

    def handle(self, *args, **options):
        api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
        if not api_key:
            return

        headers = {'X-Auth-Token': api_key}
        
        wc_id = 'WC'
        try:
            comp_resp = requests.get('https://api.football-data.org/v4/competitions', 
                                    headers=headers, timeout=10)
            if comp_resp.status_code == 200:
                for comp in comp_resp.json().get('competitions', []):
                    comp_name = comp.get('name', '').lower()
                    if 'world cup' in comp_name and 'world' in comp_name:
                        wc_id = comp.get('id')
                        break
        except Exception:
            pass

        try:
            resp = requests.get(
                f'https://api.football-data.org/v4/competitions/{wc_id}/matches',
                headers=headers, timeout=10
            )
            if resp.status_code != 200:
                return
            data = resp.json()
        except Exception:
            return

        for m in data.get('matches', []):
            try:
                home = m.get('homeTeam', {})
                away = m.get('awayTeam', {})
                t1_name = home.get('name') or home.get('shortName') or home.get('tla')
                t2_name = away.get('name') or away.get('shortName') or away.get('tla')

                if not t1_name or not t2_name:
                    continue

                t1, _ = Team.objects.get_or_create(name=t1_name)
                t2, _ = Team.objects.get_or_create(name=t2_name)

                match, created = Match.objects.get_or_create(
                    team_1=t1, team_2=t2,
                    defaults={'date': m['utcDate'], 'is_finished': False}
                )

                if not created:
                    match.date = m['utcDate']

                status = m['status']
                score = m.get('score', {})
                full_time = score.get('fullTime', {})
                stage = m.get('stage', '')

                if status == 'FINISHED':
                    match.score_1 = full_time.get('home')
                    match.score_2 = full_time.get('away')
                    match.is_finished = True

                    # Mark losing team as eliminated for knockout stages
                    if stage not in ('GROUP_STAGE', ''):
                        if match.score_1 is not None and match.score_2 is not None:
                            if match.score_1 > match.score_2:
                                t2.is_eliminated = True
                                t2.save()
                            elif match.score_2 > match.score_1:
                                t1.is_eliminated = True
                                t1.save()

                elif status in ('IN_PLAY', 'PAUSED'):
                    live = score.get('fullTime') or score.get('halfTime') or {}
                    match.score_1 = live.get('home')
                    match.score_2 = live.get('away')

                match.save()

            except Exception:
                continue