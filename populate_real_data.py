import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Participant, Team, TeamPick

def populate_picks():
    data = """
    Chenzo Zangmo: Portugal,Morocco,Argentina
    Kuenga Wangchen Dorji:Spain,Norway
    Karma Sonam Lhamo:France,Spain,Argentina
    Lhaden Wangda:Spain
    Pema Dregzel Wangda: France 
    Bajay:Portugal,Argentina, France 
    Kinley Digzel Dorji:France,England
    Wangmo: Spain
    Tshering Yangden:Argentina
    Ongmo:Brazil,Argentina,Portugal,Spain
    Sonam Yuden:France,Spain,Brazil
    Sonam Yugyel Gyeltshen:Netherlands,England
    Gyeltshen JOW:Norway,France,Germany,Belgium
    Ap HAti:Brazil
    Aum Bau:Spain
    Kinley Pem: France,Argentina
    Pasang Dorji:France,Argentina
    Tshering:Spain
    Chimi Pem:Spain
    Karma Choeying Dolma:Spain,France
    Sonam Tshering:England,Argentina,Germany,Netherlands
    Kinley Bida:Netherlands,England
    """

    # Ensure all teams are in the database
    all_teams = set()
    for line in data.strip().split('\n'):
        if ':' in line:
            _, teams_str = line.split(':')
            for t_name in teams_str.split(','):
                all_teams.add(t_name.strip())
    
    for t_name in all_teams:
        Team.objects.get_or_create(name=t_name)

    # Clear old data if needed or just add
    # Participant.objects.all().delete() # Optional: keep it clean

    for line in data.strip().split('\n'):
        if ':' in line:
            p_name, teams_str = line.split(':')
            p_name = p_name.strip()
            participant, _ = Participant.objects.get_or_create(name=p_name)
            
            # Clear old picks for this participant to avoid duplicates
            TeamPick.objects.filter(participant=participant).delete()
            
            for t_name in teams_str.split(','):
                t_name = t_name.strip()
                team = Team.objects.get(name=t_name)
                TeamPick.objects.create(participant=participant, team=team)

    print("Family picks populated successfully!")

if __name__ == '__main__':
    populate_picks()
