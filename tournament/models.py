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
    
    total_matches = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    
    def update_stats(self):
        # Same calculation logic as in the view
        self.total_matches = Match.objects.filter(
            Q(home_team=self) | Q(away_team=self),
            is_live=False,
            date__lt=timezone.now()
        ).count()
        
        self.wins = Match.objects.filter(
            Q(winner=self),
            is_live=False,
            date__lt=timezone.now()
        ).count()
        
        self.draws = Match.objects.filter(
            Q(home_team=self) | Q(away_team=self),
            is_live=False,
            date__lt=timezone.now(),
            result='Draw'
        ).count()
        
        self.losses = self.total_matches - self.wins - self.draws
        self.points = self.wins * 3 + self.draws * 1
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
    out = models.BooleanField(default=False)
    wicket_type = models.CharField(max_length=20, blank=True, null=True)
    
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
        ('LIVE', 'Live'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='UPCOMING')    

    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='TBD')
    man_of_the_match = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    umpires = models.CharField(max_length=200)
    match_number = models.PositiveIntegerField(unique=True)
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    current_batsman = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_batsman_matches')
    current_non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_non_striker_matches')
    current_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_bowler_matches')
    striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='striker_matches')
    non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='non_striker_matches')
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='bowler_matches')
    balls_remaining = models.PositiveIntegerField(default=120)
    innings = models.PositiveIntegerField(default=1)
    is_live = models.BooleanField(default=False)
    current_run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    required_run_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    win_margin = models.CharField(max_length=100, blank=True)
    next_batsman = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='next_batsman_matches')
    next_bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='next_bowler_matches')
    current_ball = models.PositiveIntegerField(default=0)
    current_over = models.PositiveIntegerField(default=0)
    batting_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='batting_matches')
    striker_runs = models.PositiveIntegerField(default=0)
    striker_balls = models.PositiveIntegerField(default=0)
    non_striker_runs = models.PositiveIntegerField(default=0)
    non_striker_balls = models.PositiveIntegerField(default=0)
    bowler_runs = models.PositiveIntegerField(default=0)
    bowler_wickets = models.PositiveIntegerField(default=0)
    bowler_balls = models.PositiveIntegerField(default=0)
    total_runs = models.PositiveIntegerField(default=0)
    total_wickets = models.PositiveIntegerField(default=0)
    extras = models.PositiveIntegerField(default=0)
    batting_team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='batting_matches', null=True)
    bowling_team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='bowling_matches', null=True)
    powerplay_overs = models.IntegerField(default=6)  # Typically 6 for T20
    powerplay_runs = models.IntegerField(default=0)
    powerplay_wickets = models.IntegerField(default=0)
    is_powerplay = models.BooleanField(default=True)


    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateTimeField()
    venue = models.CharField(max_length=100)
    toss_winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='toss_wins', null=True)
    toss_decision = models.CharField(max_length=10, choices=[('bat', 'Bat'), ('field', 'Field')], null=True)
    
    # Innings tracking
    innings = models.IntegerField(default=1)
    first_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='first_innings', null=True)
    second_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='second_innings', null=True)
    
    # First innings score
    first_score = models.IntegerField(default=0)
    first_wickets = models.IntegerField(default=0)
    first_current_over = models.IntegerField(default=0)
    first_current_ball = models.IntegerField(default=0)
    
    # Second innings score
    second_score = models.IntegerField(default=0)
    second_wickets = models.IntegerField(default=0)
    second_current_over = models.IntegerField(default=0)
    second_current_ball = models.IntegerField(default=0)
    
    # Current players
    striker = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='striker_matches', null=True)
    non_striker = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='non_striker_matches', null=True)
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='bowler_matches', null=True)
    
    # Batsman stats
    striker_runs = models.IntegerField(default=0)
    striker_balls = models.IntegerField(default=0)
    striker_fours = models.IntegerField(default=0)
    striker_sixes = models.IntegerField(default=0)
    
    non_striker_runs = models.IntegerField(default=0)
    non_striker_balls = models.IntegerField(default=0)
    non_striker_fours = models.IntegerField(default=0)
    non_striker_sixes = models.IntegerField(default=0)
    
    # Bowler stats
    bowler_runs = models.IntegerField(default=0)
    bowler_wickets = models.IntegerField(default=0)
    bowler_wides = models.IntegerField(default=0)
    bowler_no_balls = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.date}"
    
    def save(self, *args, **kwargs):
        # Set first_team and second_team based on toss decision
        if self.toss_winner and not self.first_team:
            if self.toss_decision == 'bat':
                self.first_team = self.toss_winner
                self.second_team = self.away_team if self.toss_winner == self.home_team else self.home_team
            else:
                self.second_team = self.toss_winner
                self.first_team = self.away_team if self.toss_winner == self.home_team else self.home_team
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Match {self.match_number}: {self.home_team} vs {self.away_team}"
    
    def get_bowling_team(self):
        if self.batting_team == self.home_team:
            return self.away_team
        return self.home_team
    
    def update_score(self, runs):
        if self.batting_team == self.home_team:
            self.home_score += runs
        else:
            self.away_score += runs
        
        if hasattr(self, 'current_batsman_runs'):
            self.current_batsman_runs += runs
            self.current_batsman_balls += 1
        else:
            self.current_batsman_runs = runs
            self.current_batsman_balls = 1
        
        # Update bowler stats
        if hasattr(self, 'current_bowler_runs'):
            self.current_bowler_runs += runs
        else:
            self.current_bowler_runs = runs
        
        # Update ball count
        self.current_ball += 1
        if self.current_ball > 5:
            self.current_ball = 0
            self.current_over += 1
        
        self.save()

    @property
    def first_current_ball(self):
        return self.ball_set.order_by('over', 'ball_number').first()
        
        # Update batsman stats
        
    
    def add_wicket(self):
        if self.batting_team == self.home_team:
            self.home_wickets += 1
        else:
            self.away_wickets += 1
        
        # Update bowler stats
        if hasattr(self, 'current_bowler_wickets'):
            self.current_bowler_wickets += 1
        else:
            self.current_bowler_wickets = 1
        
        self.save()
    
    def complete_match(self):
        self.status = 'COMPLETED'
        self.save()
        self.update_player_stats()
    
    def update_player_stats(self):
        # Update all batting performances
        for performance in self.batting_performances.all():
            player = performance.player
            player.total_runs += performance.runs
            player.total_balls_faced += performance.balls_faced
            player.total_fours += performance.fours
            player.total_sixes += performance.sixes
            if performance.runs >= 50:
                player.fifties += 1
            if performance.runs >= 100:
                player.centuries += 1
            if performance.runs > player.highest_score:
                player.highest_score = performance.runs
            player.save()
        
        # Update all bowling performances
        for performance in self.bowling_performances.all():
            player = performance.player
            player.total_wickets += performance.wickets
            player.total_overs_bowled += performance.overs
            player.total_runs_conceded += performance.runs_conceded
            if performance.wickets > player.best_bowling_wickets or (
                performance.wickets == player.best_bowling_wickets and 
                performance.runs_conceded < player.best_bowling_runs
            ):
                player.best_bowling_wickets = performance.wickets
                player.best_bowling_runs = performance.runs_conceded
            player.save()
    

    def update_stats(self):
        # Calculate CRR
        if self.current_over > 0 or self.current_ball > 0:
            total_balls = self.current_over * 6 + self.current_ball
            self.current_run_rate = (self.total_runs / total_balls) * 6
            
        # Calculate RRR if second innings
        if self.innings == 2:
            remaining_runs = self.first_innings_total + 1 - self.total_runs
            remaining_balls = 120 - (self.current_over * 6 + self.current_ball)
            if remaining_balls > 0 and remaining_runs > 0:
                self.required_run_rate = (remaining_runs / remaining_balls) * 6
        self.save()
    
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
    @property
    def status(self):
        if self.is_live:
            return "LIVE"
        elif self.date > timezone.now():
            return "UPCOMING"
        else:
            return "COMPLETED"
    def status(self):
        if self.is_live:
            return "LIVE"
        elif self.date > timezone.now():
            return "UPCOMING"
        else:
            return "COMPLETED"
    
    def update_batting_stats(self, player, runs, balls=1):
        performance, created = BattingPerformance.objects.get_or_create(
            player=player,
            match=self,
            defaults={'runs': runs, 'balls_faced': balls}
        )
        if not created:
            performance.runs += runs
            performance.balls_faced += balls
            performance.save()
        return performance

    def update_bowling_stats(self, player, runs=0, wickets=0, extras=0):
        performance, created = BowlingPerformance.objects.get_or_create(
            player=player,
            match=self,
            defaults={
                'runs_conceded': runs + extras,
                'wickets': wickets,
                'overs': 0
            }
        )
        if not created:
            performance.runs_conceded += runs + extras
            performance.wickets += wickets
            performance.save()
        return performance
    def save(self, *args, **kwargs):
        # Auto-set batting/bowling teams if not set
        if self.toss_winner and not self.batting_team:
            if self.toss_decision == 'bat':
                self.batting_team = self.toss_winner
                self.bowling_team = self.get_opponent_team(self.toss_winner)
            else:
                self.bowling_team = self.toss_winner
                self.batting_team = self.get_opponent_team(self.toss_winner)
        super().save(*args, **kwargs)

    def reset_match(self):
        """Reset all match statistics and performances"""
        # Reset match stats
        self.total_runs = 0
        self.total_wickets = 0
        self.current_ball = 0
        self.current_over = 0
        self.extras = 0
        self.striker_runs = 0
        self.striker_balls = 0
        self.non_striker_runs = 0
        self.non_striker_balls = 0
        self.bowler_runs = 0
        self.bowler_wickets = 0
        self.bowler_balls = 0
        
        # Reset team scores
        self.home_score = 0
        self.home_wickets = 0
        self.away_score = 0
        self.away_wickets = 0
        
        
        self.is_live = False
        self.save()
        
        # Delete all performances
        self.batting_performances.all().delete()
        self.bowling_performances.all().delete()
    
    def get_batting_team_players(self):
        return Player.objects.filter(team=self.batting_team)
    
    def get_bowling_team_players(self):
        return Player.objects.filter(team=self.bowling_team)
    
    def get_available_batsmen(self):
        return Player.objects.filter(team=self.batting_team).exclude(
            id__in=[self.striker_id, self.non_striker_id] if self.striker_id and self.non_striker_id else []
        )

    def get_available_bowlers(self):
        return Player.objects.filter(team=self.bowling_team).exclude(id=self.bowler_id)

    # Add to Match model
    def set_openers(self):
        """Set initial opening batsmen and bowlers"""
        if not self.batting_team or not self.bowling_team:
            return
            
        # Set first two batsmen from batting team as openers
        batting_players = Player.objects.filter(team=self.batting_team).order_by('?')[:2]
        if len(batting_players) >= 2:
            self.striker = batting_players[0]
            self.non_striker = batting_players[1]
            
        # Set first bowler from bowling team
        bowling_players = Player.objects.filter(team=self.bowling_team).order_by('?')[:1]
        if bowling_players:
            self.bowler = bowling_players[0]
            
        self.save()

    def update_team_scores(self):
        """Update team scores based on total runs"""
        if self.batting_team == self.home_team:
            self.home_score = self.total_runs
            self.home_wickets = self.total_wickets
        else:
            self.away_score = self.total_runs
            self.away_wickets = self.total_wickets
        self.save()
    def add_runs(self, runs):
        if self.innings == 1:
            self.first_score += runs
            self.striker_runs += runs
            self.striker_balls += 1
            if runs == 4:
                self.striker_fours += 1
            elif runs == 6:
                self.striker_sixes += 1
        else:
            self.second_score += runs
            self.striker_runs += runs
            self.striker_balls += 1
            if runs == 4:
                self.striker_fours += 1
            elif runs == 6:
                self.striker_sixes += 1
        self.save()

    def add_extras(self, extra_type):
        if extra_type == 'wide':
            if self.innings == 1:
                self.first_score += 1
                self.bowler_wides += 1
            else:
                self.second_score += 1
                self.bowler_wides += 1
        elif extra_type == 'no_ball':
            if self.innings == 1:
                self.first_score += 1
                self.bowler_no_balls += 1
            else:
                self.second_score += 1
                self.bowler_no_balls += 1
        self.save()

    def add_wicket(self, wicket_type, out_batsman, next_batsman, fielder=None):
        if self.innings == 1:
            self.first_wickets += 1
        else:
            self.second_wickets += 1
        
        if out_batsman == 'striker':
            batsman = self.striker
            batsman.out = True
            batsman.wicket_type = wicket_type
            batsman.bowler = self.bowler
            if fielder:
                batsman.fielder = fielder
            batsman.save()
            self.striker = next_batsman
        else:
            batsman = self.non_striker
            batsman.out = True
            batsman.wicket_type = wicket_type
            batsman.bowler = self.bowler
            if fielder:
                batsman.fielder = fielder
            batsman.save()
            self.non_striker = next_batsman
        
        self.save()

    def complete_over(self):
        if self.innings == 1:
            if self.first_current_ball == 5:
                self.first_current_over += 1
                self.first_current_ball = 0
            else:
                self.first_current_ball += 1
        else:
            if self.second_current_ball == 5:
                self.second_current_over += 1
                self.second_current_ball = 0
            else:
                self.second_current_ball += 1
        self.save()

    def start_second_innings(self):
        self.innings = 2
        # Swap batting and bowling teams
        self.first_team, self.second_team = self.second_team, self.first_team
        self.save()
class BattingPerformance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batting_performances')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='batting_performances')    
    runs = models.PositiveIntegerField(default=0)
    balls_faced = models.PositiveIntegerField(default=0)
    fours = models.PositiveIntegerField(default=0)
    sixes = models.PositiveIntegerField(default=0)
    not_out = models.BooleanField(default=False)
    innings = models.PositiveIntegerField(default=1)  
    bowler = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='bowling_dismissals')
    
    @property
    def strike_rate(self):
        if self.balls_faced > 0:
            return (self.runs / self.balls_faced) * 100
        return 0
    

class BowlingPerformance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bowling_performances')
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='bowling_performances')
    innings = models.PositiveIntegerField(default=1)  # <-- Add this
    overs = models.FloatField(default=0)
    maidens = models.IntegerField(default=0)
    runs_conceded = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    economy = models.FloatField(default=0)

    def update_economy(self):
        if self.overs > 0:
            self.economy = self.runs_conceded / self.overs
        self.save()

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


class Ball(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    batsman = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batted_balls')
    bowler = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bowled_balls')
    runs = models.IntegerField(default=0)
    is_wicket = models.BooleanField(default=False)
    over = models.IntegerField(default=1)         # e.g., 0 to 19 for a 20-over match
    ball_number = models.IntegerField(default=1)
    wicket_type = models.CharField(max_length=20, blank=True, choices=[
        ('bowled', 'Bowled'),
        ('caught', 'Caught'),
        ('lbw', 'LBW'),
        ('run_out', 'Run Out'),
        ('stumped', 'Stumped'),
        ('hit_wicket', 'Hit Wicket'),
    ])
    extras = models.CharField(max_length=20, blank=True, choices=[
        ('wide', 'Wide'),
        ('no_ball', 'No Ball'),
        ('bye', 'Bye'),
        ('leg_bye', 'Leg Bye'),
        ('penalty', 'Penalty'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)


class DRS(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    requesting_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    reviewing_player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)
    decision = models.CharField(max_length=20, choices=[
        ('lbw', 'LBW'),
        ('caught', 'Caught'),
        ('stumped', 'Stumped'),
        ('run_out', 'Run Out')
    ])
    original_decision = models.CharField(max_length=10, choices=[
        ('out', 'Out'),
        ('not_out', 'Not Out')
    ])
    DECISION_CHOICES = [
    ('Out', 'Out'),
    ('Not Out', 'Not Out'),
    ('Umpire\'s Call', 'Umpire\'s Call'),  # 13 characters including apostrophe
    ]
    reviewed_decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    is_successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class Partnership(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    batter1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batter1_partnerships')
    batter2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='batter2_partnerships')
    runs = models.IntegerField()
    balls = models.IntegerField()
    wicket = models.ForeignKey(BattingPerformance, on_delete=models.SET_NULL, null=True, blank=True)
    innings = models.IntegerField()

def calculate_partnerships(match):
    """Calculate all partnerships in the match"""
    partnerships = []
    current_partners = []
    current_runs = 0
    current_balls = 0
    
    for ball in Ball.objects.filter(match=match).order_by('timestamp'):
        if not current_partners:
            # New partnership starting
            current_partners = [match.striker, match.non_striker]
        
        current_runs += ball.runs
        current_balls += 1
        
        if ball.is_wicket and ball.batsman in current_partners:
            # Partnership broken
            other_partner = [p for p in current_partners if p != ball.batsman][0]
            partnerships.append({
                'batter1': ball.batsman,
                'batter2': other_partner,
                'runs': current_runs,
                'balls': current_balls,
                'wicket': ball
            })
            current_partners = []
            current_runs = 0
            current_balls = 0
    
    return partnerships