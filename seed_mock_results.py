import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Match, Team

def seed_results():
    # Let's assume Argentina and France won some matches
    arg = Team.objects.get(name='Argentina')
    fra = Team.objects.get(name='France')
    bra = Team.objects.get(name='Brazil')
    esp = Team.objects.get(name='Spain')
    
    # Finished match
    Match.objects.get_or_create(
        team_1=arg, team_2=esp,
        defaults={'score_1': 2, 'score_2': 1, 'is_finished': True, 'date': datetime.now() - timedelta(days=1)}
    )
    
    Match.objects.get_or_create(
        team_1=fra, team_2=bra,
        defaults={'score_1': 1, 'score_2': 0, 'is_finished': True, 'date': datetime.now() - timedelta(days=2)}
    )

    print("Mock results seeded!")

if __name__ == '__main__':
    seed_results()
