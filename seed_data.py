import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Participant, Team, Match, Bet

def seed():
    # Participants
    family = ['John', 'Jane', 'Alice', 'Bob']
    participants = []
    for name in family:
        p, _ = Participant.objects.get_or_create(name=name)
        participants.append(p)

    # Teams
    teams_data = [
        ('Argentina', 0.95), ('France', 0.94), ('Brazil', 0.92), 
        ('England', 0.90), ('Spain', 0.88), ('Germany', 0.85),
        ('Netherlands', 0.84), ('Portugal', 0.83), ('Morocco', 0.75),
        ('Croatia', 0.78), ('Japan', 0.70), ('USA', 0.65)
    ]
    teams = []
    for name, strength in teams_data:
        t, _ = Team.objects.get_or_create(name=name, defaults={'strength': strength})
        teams.append(t)

    # Some Finished Matches
    m1, _ = Match.objects.get_or_create(
        team_1=teams[0], team_2=teams[1], 
        defaults={'score_1': 3, 'score_2': 3, 'date': datetime.now() - timedelta(days=5), 'is_finished': True}
    )
    
    m2, _ = Match.objects.get_or_create(
        team_1=teams[2], team_2=teams[4], 
        defaults={'score_1': 1, 'score_2': 2, 'date': datetime.now() - timedelta(days=4), 'is_finished': True}
    )

    # Upcoming Matches
    m3, _ = Match.objects.get_or_create(
        team_1=teams[3], team_2=teams[5], 
        defaults={'date': datetime.now() + timedelta(days=1), 'is_finished': False}
    )
    
    m4, _ = Match.objects.get_or_create(
        team_1=teams[6], team_2=teams[7], 
        defaults={'date': datetime.now() + timedelta(days=2), 'is_finished': False}
    )

    # Bets for finished matches
    for p in participants:
        # Randomish bets
        Bet.objects.get_or_create(participant=p, match=m1, defaults={'predicted_result': 'X', 'points_won': 10 if p.name == 'John' else 0})
        Bet.objects.get_or_create(participant=p, match=m2, defaults={'predicted_result': '2', 'points_won': 10 if p.name in ['Jane', 'Alice'] else 0})
        
        # Bets for upcoming matches
        Bet.objects.get_or_create(participant=p, match=m3, defaults={'predicted_result': '1' if p.name in ['John', 'Jane'] else '2'})
        Bet.objects.get_or_create(participant=p, match=m4, defaults={'predicted_result': 'X' if p.name == 'Bob' else '1'})

    print("Seeding complete!")

if __name__ == '__main__':
    seed()
