from django.db import models

class Participant(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100)
    flag_url = models.URLField(blank=True, null=True)
    american_odds = models.IntegerField(default=100) # e.g. +460
    is_eliminated = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Match(models.Model):
    team_1 = models.ForeignKey(Team, related_name='matches_as_t1', on_delete=models.CASCADE)
    team_2 = models.ForeignKey(Team, related_name='matches_as_t2', on_delete=models.CASCADE)
    score_1 = models.IntegerField(null=True, blank=True)
    score_2 = models.IntegerField(null=True, blank=True)
    date = models.DateTimeField()
    is_finished = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.team_1} vs {self.team_2}"

class Bet(models.Model):
    # This was for match-specific bets, keeping it for now
    RESULT_CHOICES = [
        ('1', 'Team 1 Wins'),
        ('X', 'Draw'),
        ('2', 'Team 2 Wins'),
    ]
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='match_bets')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_bets')
    predicted_result = models.CharField(max_length=1, choices=RESULT_CHOICES)
    points_won = models.IntegerField(default=0)

class TeamPick(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='team_picks')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.participant.name} picked {self.team.name}"
