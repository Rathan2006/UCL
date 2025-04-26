from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=3, blank=True) 
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    home_ground = models.CharField(max_length=100)
    captain = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='captain_of')
    coach = models.CharField(max_length=100)
    founded = models.PositiveIntegerField()
    public = models.BooleanField(default=True) 
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_teams', null=True, blank=True)
    
    # Stats fields
    matches_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)  # Added concrete points field
    
    def __str__(self):
        return self.name
    @property
    def total_matches(self):
        """Count all completed matches for this team"""
        return Match.objects.filter(
            (Q(home_team=self) | Q(away_team=self)),
            status='COMPLETED'
        ).count()
    
    def update_stats(self):
        """Update all statistics including matches played"""
        completed_matches = Match.objects.filter(
            Q(home_team=self) | Q(away_team=self),
            status='COMPLETED'
        )
        
        self.matches_played = completed_matches.count()  # This will now work
        self.wins = completed_matches.filter(
            Q(home_team=self, result='Home Win') | 
            Q(away_team=self, result='Away Win')
        ).count()
        self.losses = completed_matches.filter(
            Q(home_team=self, result='Away Win') | 
            Q(away_team=self, result='Home Win')
        ).count()
        self.draws = completed_matches.filter(result='Draw').count()
        self.points = (self.wins * 3) + (self.draws * 1)
        self.save()

class Player(models.Model):
    BATTING_STYLE = [
        ('Right', 'Right-handed'),
        ('Left', 'Left-handed'),
    ]
    
    BOWLING_STYLE = [
        ('Fast', 'Fast bowler'),
        ('Medium', 'Medium pace'),
        ('Spin', 'Spin bowler'),
        ('NA', 'Not a bowler'),
    ]
    
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    age = models.PositiveIntegerField()
    nationality = models.CharField(max_length=100)
    batting_style = models.CharField(max_length=10, choices=BATTING_STYLE)
    bowling_style = models.CharField(max_length=10, choices=BOWLING_STYLE)
    role = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='player_photos/', null=True, blank=True)
    jersey_number = models.PositiveIntegerField()
    # Batting Stats
    total_runs = models.PositiveIntegerField(default=0)
    total_balls_faced = models.PositiveIntegerField(default=0)
    total_fours = models.PositiveIntegerField(default=0)
    total_sixes = models.PositiveIntegerField(default=0)
    highest_score = models.PositiveIntegerField(default=0)
    fifties = models.PositiveIntegerField(default=0)
    centuries = models.PositiveIntegerField(default=0)
    
    # Bowling Stats
    total_wickets = models.PositiveIntegerField(default=0)
    total_overs_bowled = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    total_runs_conceded = models.PositiveIntegerField(default=0)
    best_bowling_wickets = models.PositiveIntegerField(default=0)
    best_bowling_runs = models.PositiveIntegerField(default=0)
    
    # Fielding Stats
    total_catches = models.PositiveIntegerField(default=0)
    total_stumpings = models.PositiveIntegerField(default=0)
    total_run_outs = models.PositiveIntegerField(default=0)
    
    # Calculated properties
    @property
    def batting_average(self):
        if self.total_matches > 0 and self.total_runs > 0:
            return round(self.total_runs / self.total_matches, 2)
        return 0.0
    
    @property
    def strike_rate(self):
        if self.total_balls_faced > 0:
            return round((self.total_runs / self.total_balls_faced) * 100, 2)
        return 0.0
    
    @property
    def bowling_average(self):
        if self.total_wickets > 0:
            return round(self.total_runs_conceded / self.total_wickets, 2)
        return 0.0
    
    @property
    def economy_rate(self):
        if self.total_overs_bowled > 0:
            return round(self.total_runs_conceded / float(self.total_overs_bowled), 2)
        return 0.0
    
    def __str__(self):
        return f"{self.name} ({self.team})"
    
    @property
    def total_runs(self):
        return sum(performance.runs for performance in self.batting_performances.all())
    
    @property
    def total_wickets(self):
        return sum(performance.wickets for performance in self.bowling_performances.all())


class Match(models.Model):
    RESULT_CHOICES = [
        ('Home Win', 'Home Win'),
        ('Away Win', 'Away Win'),
        ('Draw', 'Draw'),
        ('No Result', 'No Result'),
        ('TBD', 'To Be Determined'),
    ]
    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UPCOMING')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateTimeField()
    venue = models.CharField(max_length=100)
    toss_winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='toss_wins')
    toss_decision = models.CharField(max_length=10, choices=[('Bat', 'Bat'), ('Field', 'Field')], null=True, blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='TBD')
    man_of_the_match = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    umpires = models.CharField(max_length=200)
    match_number = models.PositiveIntegerField(unique=True)
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    current_batsman = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_batsman_matches')
    current_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_bowler_matches')
    balls_remaining = models.PositiveIntegerField(default=120)
    innings = models.PositiveIntegerField(default=1)
    is_live = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Match {self.match_number}: {self.home_team} vs {self.away_team}"
    
    @property
    def is_completed(self):
        return self.result != 'TBD'
    
    @property
    def winner(self):
        if self.result == 'Home Win':
            return self.home_team
        elif self.result == 'Away Win':
            return self.away_team
        return None

    def get_opponent_team(self, team):
        if self.home_team == team:
            return self.away_team
        return self.home_team

    def get_win_margin(self):
        if not self.is_completed or self.result == 'Draw':
            return ""
        return "X runs" if self.result == 'Home Win' else "Y wickets"


class BattingPerformance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batting_performances')
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    runs = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    not_out = models.BooleanField(default=False)
    
    @property
    def strike_rate(self):
        if self.balls_faced > 0:
            return round((self.runs / self.balls_faced) * 100, 2)
        return 0.0


class BowlingPerformance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bowling_performances')
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    overs = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    maidens = models.PositiveIntegerField(default=0)
    runs_conceded = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    
    @property
    def economy(self):
        if self.overs > 0:
            return round(self.runs_conceded / float(self.overs), 2)
        return 0.0

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=100)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)