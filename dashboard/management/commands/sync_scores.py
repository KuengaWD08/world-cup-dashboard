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
            self.stderr.write(self.style.ERROR(
                'No API key set. Get a free key at https://www.football-data.org/ '
                'then run: set FOOTBALL_DATA_API_KEY=your_key_here'
            ))
            return

        headers = {'X-Auth-Token': api_key}
        
        # First, try to list available competitions to find World Cup 2026
        wc_id = None
        try:
            comp_resp = requests.get('https://api.football-data.org/v4/competitions', 
                                    headers=headers, timeout=10)
            if comp_resp.status_code == 200:
                competitions = comp_resp.json().get('competitions', [])
                
                # Find World Cup 2026
                for comp in competitions:
                    comp_name = comp.get('name', '').lower()
                    if ('2026' in comp.get('name', '') or 'world cup' in comp_name) and 'world' in comp_name:
                        wc_id = comp.get('id')
                        self.stdout.write(self.style.SUCCESS(
                            f"Found World Cup 2026: {comp.get('name')} (Code: {wc_id})"
                        ))
                        break
        except Exception as e:
            self.stdout.write(f"[DEBUG] Could not fetch competitions: {e}")

        # Fallback to WC if not found
        if not wc_id:
            wc_id = 'WC'
            self.stdout.write("[DEBUG] Using fallback competition code: WC")

        # Fetch matches
        url = f'https://api.football-data.org/v4/competitions/{wc_id}/matches'
        self.stdout.write(f"[DEBUG] Fetching matches from: {url}")

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            self.stdout.write(f"[DEBUG] Response status: {resp.status_code}")
            
            if resp.status_code == 429:
                self.stderr.write(self.style.WARNING('Rate limited. Try again in a minute.'))
                return
            
            if resp.status_code != 200:
                self.stderr.write(self.style.ERROR(f'API returned {resp.status_code}'))
                self.stderr.write(self.style.ERROR(f'Response: {resp.text[:500]}'))
                return
                
            data = resp.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Request error: {e}'))
            return

        # Process matches
        created_count = 0
        updated_count = 0

        matches_list = data.get('matches', [])
        if not matches_list:
            self.stderr.write(self.style.WARNING('No matches in API response'))
            self.stdout.write(f"[DEBUG] Response keys: {data.keys()}")
            return

        for m in matches_list:
            try:
                t1_name = m['homeTeam']['name']
                t2_name = m['awayTeam']['name']
                
                # Skip matches with missing team names
                if not t1_name or not t2_name:
                    self.stdout.write(f"[DEBUG] Skipping match with missing team names: {t1_name} vs {t2_name}")
                    continue
                
                match_date = m['utcDate']  # ISO string

                t1, _ = Team.objects.get_or_create(name=t1_name)
                t2, _ = Team.objects.get_or_create(name=t2_name)

                match, created = Match.objects.get_or_create(
                    team_1=t1, team_2=t2,
                    defaults={'date': match_date, 'is_finished': False}
                )

                status = m['status']
                score = m.get('score', {})
                full_time = score.get('fullTime', {})

                if status == 'FINISHED':
                    match.score_1 = full_time.get('home')
                    match.score_2 = full_time.get('away')
                    match.is_finished = True
                    match.save()
                    updated_count += 1
                elif status in ('IN_PLAY', 'PAUSED'):
                    # Live score
                    live = score.get('fullTime') or score.get('halfTime') or {}
                    match.score_1 = live.get('home')
                    match.score_2 = live.get('away')
                    match.save()
                    updated_count += 1

                if created:
                    created_count += 1
            except KeyError as e:
                self.stderr.write(f"[DEBUG] Error parsing match: {e}")
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Sync complete: {created_count} new matches, {updated_count} updated.'
        ))