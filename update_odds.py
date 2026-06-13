import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Team

def update_odds():
    odds_data = {
        "Spain": 462,
        "France": 485,
        "England": 826,
        "Portugal": 834,
        "Argentina": 1011,
        "Brazil": 1090,
        "Germany": 1686,
        "Netherlands": 1686,
        "Norway": 3900,
        "Mexico": 3900,
        "Belgium": 4248,
        "Colombia": 4900,
        "Japan": 5782,
        "Morocco": 6150,
        "USA": 6150,
        "Turkey": 8223,
        "Switzerland": 9900
    }
    
    for name, odds in odds_data.items():
        team, created = Team.objects.get_or_create(name=name)
        team.american_odds = odds
        team.save()
        if created:
            print(f"Created team {name} with odds +{odds}")
        else:
            print(f"Updated {name} with odds +{odds}")

if __name__ == '__main__':
    update_odds()
