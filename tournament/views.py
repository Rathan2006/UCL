from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.utils import timezone
from .models import Team, Player, Match, BattingPerformance, BowlingPerformance, Ball
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.db.models import Q, F, Sum, Count
from .forms import TossForm, TeamForm, PlayerForm
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate
from django.db.models import Sum, Count,IntegerField
from django.db.models.functions import NullIf
from django.db.models import Value
from django.db.models import Case, When, F, Value, FloatField
from django.db.models.functions import Cast
from django.shortcuts import render
from django.db.models.functions import Coalesce
import math


from django.utils import timezone

def index(request):
    live_matches = Match.objects.filter(is_live=True)
    upcoming_matches = Match.objects.filter(date__gte=timezone.now(), is_live=False).order_by('date')[:5]
    recent_matches = Match.objects.filter(date__lt=timezone.now(), is_live=False).order_by('-date')[:5]
    
    # Get top teams (first calculate standings)
    for team in Team.objects.all():
        # Get completed matches involving the team
        matches = Match.objects.filter(
            Q(home_team=team) | Q(away_team=team),
            is_live=False,
            date__lt=timezone.now()
        )

        total_matches = matches.count()
        wins = 0
        draws = 0

        for match in matches:
            # Determine scores
            home = match.home_team
            away = match.away_team
            home_score = match.home_score
            away_score = match.away_score

            # Skip if scores are missing
            if home_score is None or away_score is None:
                continue

            # Determine result
            if home_score == away_score:
                draws += 1
            elif home_score > away_score and team == home:
                wins += 1
            elif away_score > home_score and team == away:
                wins += 1

        losses = total_matches - wins - draws
        points = wins * 3 + draws

        # Update team stats
        team.total_matches = total_matches
        team.wins = wins
        team.losses = losses
        team.draws = draws
        team.points = points
        team.save()

    # Get top 2 teams
    top_teams = Team.objects.all().order_by('-points', '-wins')[:2]
    
    # Get top 2 batsmen
    top_batsmen = Player.objects.annotate(
        total_runs_calc=Sum('batting_performances__runs'),
        total_matches_bat=Count('batting_performances__match', distinct=True),
        total_balls_faced_calc=Sum('batting_performances__balls_faced'),
    ).annotate(
        strike_rate_calc=Case(
            When(total_balls_faced_calc=0, then=Value(0.0)),
            default=Cast(F('total_runs_calc') * 100, FloatField()) / Cast(F('total_balls_faced_calc'), FloatField()),
            output_field=FloatField()
        )
    ).filter(total_runs_calc__gt=0).order_by('-total_runs_calc')[:2]
    
    # Get top 2 bowlers
    top_bowlers = Player.objects.annotate(
        total_wickets_calc=Sum('bowling_performances__wickets'),
        total_matches_bowl=Count('bowling_performances__match', distinct=True),
        total_runs_conceded_calc=Sum('bowling_performances__runs_conceded'),
        total_overs_bowled_calc=Sum('bowling_performances__overs'),
    ).annotate(
        bowling_avg=Case(
            When(total_wickets_calc=0, then=Value(0.0)),
            default=Cast(F('total_runs_conceded_calc'), FloatField()) / Cast(F('total_wickets_calc'), FloatField()),
            output_field=FloatField()
        )
    ).filter(total_wickets_calc__gt=0).order_by('-total_wickets_calc')[:2]
    
    context = {
        'live_matches': live_matches,
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
        'top_teams': top_teams,
        'top_batsmen': top_batsmen,
        'top_bowlers': top_bowlers,
    }
    return render(request, 'tournament/index.html', context)

@login_required
def team_list(request):
    teams = Team.objects.all().order_by('name')
    return render(request, 'tournament/teams.html', {'teams': teams})

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    players = team.players.all().order_by('-role', 'name')
    upcoming_matches = team.home_matches.filter(date__gte=timezone.now()) | team.away_matches.filter(date__gte=timezone.now())
    past_matches = team.home_matches.filter(date__lt=timezone.now()) | team.away_matches.filter(date__lt=timezone.now())
    
    context = {
        'team': team,
        'players': players,
        'upcoming_matches': upcoming_matches.order_by('date'),
        'past_matches': past_matches.order_by('-date'),
    }
    return render(request, 'tournament/team_detail.html', context)

@login_required
def player_list(request):
    players = Player.objects.all().order_by('team', 'name')
    return render(request, 'tournament/players.html', {'players': players})

@login_required
def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    batting_performances = player.batting_performances.all().order_by('-match__date')
    bowling_performances = player.bowling_performances.all().order_by('-match__date')
    
    context = {
        'player': player,
        'batting_performances': batting_performances,
        'bowling_performances': bowling_performances,
    }
    return render(request, 'tournament/player_detail.html', context)

def match_list(request):
    past = request.GET.get('past', '0') == '1'
    
    if past:
        # Show only completed matches (date in past AND is_live=False)
        matches = Match.objects.filter(
            date__lt=timezone.now(),
            is_live=False
        ).order_by('-date')
    else:
        # Show upcoming matches (date in future OR is_live=True)
        matches = Match.objects.filter(
            Q(date__gte=timezone.now()) | Q(is_live=True)
        ).order_by('date')
    
    return render(request, 'tournament/matches.html', {
        'upcoming_matches': matches if not past else None,
        'past_matches': matches if past else None,
        'past': past
    })

def standings(request):
    for team in Team.objects.all():
        # Get completed matches involving the team
        matches = Match.objects.filter(
            Q(home_team=team) | Q(away_team=team),
            is_live=False,
            date__lt=timezone.now()
        )

        total_matches = matches.count()
        wins = 0
        draws = 0

        for match in matches:
            # Determine scores
            home = match.home_team
            away = match.away_team
            home_score = match.home_score
            away_score = match.away_score

            # Skip if scores are missing
            if home_score is None or away_score is None:
                continue

            # Determine result
            if home_score == away_score:
                draws += 1
            elif home_score > away_score and team == home:
                wins += 1
            elif away_score > home_score and team == away:
                wins += 1

        losses = total_matches - wins - draws
        points = wins * 3 + draws

        # Update team stats
        team.total_matches = total_matches
        team.wins = wins
        team.losses = losses
        team.draws = draws
        team.points = points
        team.save()

    # Order standings
    teams = Team.objects.all().order_by('-points', '-wins')
    return render(request, 'tournament/standings.html', {'standings': teams})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'tournament/register.html', {'form': form})

@login_required
@permission_required('tournament.add_team')
def add_team(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('teams')
    else:
        form = TeamForm()
    return render(request, 'tournament/add_team.html', {'form': form})

@login_required
@permission_required('tournament.add_player')
def add_player(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('players')
    else:
        form = PlayerForm()
    return render(request, 'tournament/add_player.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('landing')

@login_required
def player_stats(request):
    # Batting stats - Cricbuzz-style: most runs on top
    batting_stats = Player.objects.annotate(
        total_runs_calc=Sum('batting_performances__runs'),
        total_matches_bat=Count('batting_performances__match', distinct=True),
        total_fours_calc=Sum('batting_performances__fours'),
        total_sixes_calc=Sum('batting_performances__sixes'),
        total_balls_faced_calc=Sum('batting_performances__balls_faced'),
        fifties_count=Count(
            Case(
                When(batting_performances__runs__gte=50, batting_performances__runs__lt=100, then=1),
                output_field=IntegerField()
            )
        ),
        centuries_count=Count(
            Case(
                When(batting_performances__runs__gte=100, then=1),
                output_field=IntegerField()
            )
        ),
        dismissals_count=Count(
            Case(
                When(batting_performances__not_out=False, then=1),
                output_field=IntegerField()
            )
        )
    ).annotate(
        batting_avg=Case(
            When(dismissals_count=0, then=Value(0.0)),
            default=Cast(F('total_runs_calc'), FloatField()) / Cast(F('dismissals_count'), FloatField()),
            output_field=FloatField()
        ),
        strike_rate_calc=Case(
            When(total_balls_faced_calc=0, then=Value(0.0)),
            default=Cast(F('total_runs_calc') * 100, FloatField()) / Cast(F('total_balls_faced_calc'), FloatField()),
            output_field=FloatField()
        )
    ).filter(total_runs_calc__gt=0).order_by('-total_runs_calc')

    # Bowling stats - Cricbuzz-style: most wickets on top
    bowling_stats = Player.objects.annotate(
        total_wickets_calc=Sum('bowling_performances__wickets'),
        total_matches_bowl=Count('bowling_performances__match', distinct=True),
        total_runs_conceded_calc=Sum('bowling_performances__runs_conceded'),
        total_overs_bowled_calc=Sum('bowling_performances__overs'),
        five_wickets_count=Count(
            Case(
                When(bowling_performances__wickets__gte=5, then=1),
                output_field=IntegerField()
            )
        )
    ).annotate(
        bowling_avg=Case(
            When(total_wickets_calc=0, then=Value(0.0)),
            default=Cast(F('total_runs_conceded_calc'), FloatField()) / Cast(F('total_wickets_calc'), FloatField()),
            output_field=FloatField()
        ),
        economy_rate_calc=Case(
            When(total_overs_bowled_calc=0, then=Value(0.0)),
            default=Cast(F('total_runs_conceded_calc'), FloatField()) / Cast(F('total_overs_bowled_calc'), FloatField()),
            output_field=FloatField()
        )
    ).filter(total_wickets_calc__gt=0).order_by('-total_wickets_calc')

    return render(request, 'tournament/player_stats.html', {
        'batting_stats': batting_stats,
        'bowling_stats': bowling_stats,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def set_match_live(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        form = TossForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save()
            if match.toss_decision == 'bat':
                match.batting_team = match.toss_winner
                match.bowling_team = match.home_team if match.toss_winner == match.away_team else match.away_team
            else:
                match.bowling_team = match.toss_winner
                match.batting_team = match.home_team if match.toss_winner == match.away_team else match.away_team
            match.is_live = True
            match.save()
            return redirect('initialize_match_players', match_id=match.id)
    else:
        form = TossForm(instance=match)
    
    return render(request, 'tournament/set_live.html', {'form': form, 'match': match})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def initialize_match_players(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    if not match.batting_team or not match.bowling_team:
        if match.toss_decision == 'bat':
            match.batting_team = match.toss_winner
            match.bowling_team = match.away_team if match.toss_winner == match.home_team else match.home_team
        else:
            match.bowling_team = match.toss_winner
            match.batting_team = match.away_team if match.toss_winner == match.home_team else match.home_team
        match.save()
    
    batting_players = Player.objects.filter(team=match.batting_team)
    bowling_players = Player.objects.filter(team=match.bowling_team)
    
    if request.method == 'POST':
        try:
            if 'striker' in request.POST:
                match.striker = Player.objects.get(id=request.POST['striker'])
                BattingPerformance.objects.create(
                        player=match.striker,
                        match=match,
                        innings=match.innings,
                        runs=0,
                        balls_faced=0,
                        fours=0,
                        sixes=0,
                        not_out=True
                    )
                match.striker_runs = 0
                match.striker_balls = 0
                match.striker_fours = 0
                match.striker_sixes = 0
            if 'non_striker' in request.POST:
                match.non_striker = Player.objects.get(id=request.POST['non_striker'])
                BattingPerformance.objects.create(
                        player=match.non_striker,
                        match=match,
                        innings=match.innings,
                        runs=0,
                        balls_faced=0,
                        fours=0,
                        sixes=0,
                        not_out=True
                    )
                match.non_striker_runs = 0
                match.non_striker_balls = 0
                match.non_striker_fours = 0
                match.non_striker_sixes = 0
            if 'bowler' in request.POST:
                match.bowler = Player.objects.get(id=request.POST['bowler'])
                bowling_performance = BowlingPerformance.objects.create(
                        player=match.bowler,
                        match=match,
                        runs_conceded=0,
                        wickets=0,
                        innings=match.innings,
                        overs=0,
                        maidens=0,
                        economy=0,
                    ) 

                match.bowler_runs = 0
                match.bowler_wickets = 0
                match.bowler_balls = 0
                match.bowler_wides = 0
                match.bowler_no_balls = 0
            match.save()
            return redirect('update_score', match_id=match.id)
        except Exception as e:
            messages.error(request, f"Error setting players: {str(e)}")

    return render(request, 'tournament/initialize_players.html', {
        'match': match,
        'batting_players': batting_players,
        'bowling_players': bowling_players,
    })

def live_match_data(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    return JsonResponse({
        'total_runs': match.total_runs,
        'total_wickets': match.total_wickets,
        'current_over': f"{match.current_over}.{match.current_ball}",
        'striker': match.striker.name if match.striker else '',
        'striker_runs': match.striker_runs,
        'striker_balls': match.striker_balls,
        'non_striker': match.non_striker.name if match.non_striker else '',
        'non_striker_runs': match.non_striker_runs,
        'non_striker_balls': match.non_striker_balls,
        'bowler': match.bowler.name if match.bowler else '',
        'bowler_runs': match.bowler_runs,
        'bowler_wickets': match.bowler_wickets,
        'bowler_overs': (match.bowler_balls // 6),
    })

def match_performances(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    batting_performances = BattingPerformance.objects.filter(match=match).select_related('player', 'bowler')
    bowling_performances = BowlingPerformance.objects.filter(match=match).select_related('player')
    
    batting_html = render_to_string('tournament/_batting_table.html', {
        'batting_performances': batting_performances
    })
    
    bowling_html = render_to_string('tournament/_bowling_table.html', {
        'bowling_performances': bowling_performances
    })
    
    return JsonResponse({
        'batting_html': batting_html,
        'bowling_html': bowling_html
    })

@never_cache
def landing(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    upcoming_matches = Match.objects.filter(date__gte=timezone.now()).order_by('date')[:3]
    
    context = {
        'upcoming_matches': upcoming_matches,
    }
    
    return render(request, 'tournament/landing.html', context)

def login_view(request): 
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'tournament/login.html', {'error': 'Invalid credentials'})
    return render(request, 'tournament/login.html')

@login_required

def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    
    
    # First innings data
    first_innings_batting = BattingPerformance.objects.filter(
        match=match, innings=1
    ).select_related('player', 'bowler').order_by('-runs')
    
    first_innings_bowling = BowlingPerformance.objects.filter(
        match=match, innings=1
    ).select_related('player').order_by('-wickets')
    
    first_innings_total = first_innings_batting.aggregate(
        Sum('runs'), Sum('balls_faced'), Sum('fours'), Sum('sixes'))
    first_innings_wickets = first_innings_batting.filter(not_out=False).count()
    
    first_innings_team = match.batting_team if match.innings == 2 else match.home_team
    first_innings_bowling_team = match.bowling_team if match.innings == 2 else match.away_team
    
    # Second innings data
    second_innings_batting = None
    second_innings_bowling = None
    second_innings_total = None
    second_innings_wickets = None
    second_innings_team = None
    second_innings_bowling_team = None
    
    if match.innings > 1 or match.status == 'COMPLETED':
        second_innings_batting = BattingPerformance.objects.filter(
            match=match, innings=2
        ).select_related('player', 'bowler').order_by('-runs')
        
        second_innings_bowling = BowlingPerformance.objects.filter(
            match=match, innings=2
        ).select_related('player').order_by('-wickets')
        
        second_innings_total = second_innings_batting.aggregate(
            Sum('runs'), Sum('balls_faced'), Sum('fours'), Sum('sixes'))
        second_innings_wickets = second_innings_batting.filter(not_out=False).count()
        
        second_innings_team = match.batting_team if match.innings == 1 else match.away_team
        second_innings_bowling_team = match.bowling_team if match.innings == 1 else match.home_team
    
    is_upcoming = match.date > timezone.now()
    is_past = match.date <= timezone.now() and not match.is_live and match.status != 'COMPLETED'

    # Calculate target for second innings
    target = None
    if match.innings == 2 and first_innings_total['runs__sum'] is not None:
        target = first_innings_total['runs__sum'] + 1
    
    context = {
        'can_set_live': is_upcoming and not match.is_live and request.user.is_superuser,
        'can_start_match': match.is_live and match.innings == 1 and not match.striker and request.user.is_superuser,
        'match': match,
        'first_innings_batting': first_innings_batting,
        'first_innings_bowling': first_innings_bowling,
        'first_innings_total': first_innings_total,
        'first_innings_wickets': first_innings_wickets,
        'first_innings_team': first_innings_team,
        'first_innings_bowling_team': first_innings_bowling_team,
        'second_innings_batting': second_innings_batting,
        'second_innings_bowling': second_innings_bowling,
        'second_innings_total': second_innings_total,
        'second_innings_wickets': second_innings_wickets,
        'second_innings_team': second_innings_team,
        'second_innings_bowling_team': second_innings_bowling_team,
        'target': target,
    }
    
    return render(request, 'tournament/match_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def start_second_innings(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Check if we can start second innings
    first_innings_completed = (
        match.is_live and 
        match.innings == 1 and 
        (match.total_wickets >= 10 or match.current_over >= 10)
    )

    if first_innings_completed:  
        # Switch innings
        match.innings = 2
        match.batting_team, match.bowling_team = match.bowling_team, match.batting_team
        
        # Reset all counters
        match.current_over = 0
        match.current_ball = 0
        match.total_runs = 0
        match.total_wickets = 0
        match.striker = None
        match.non_striker = None
        match.striker_runs = 0
        match.striker_balls = 0
        match.striker_fours = 0
        match.striker_sixes = 0
        match.non_striker_runs = 0
        match.non_striker_balls = 0
        match.non_striker_fours = 0
        match.non_striker_sixes = 0
        match.bowler = None
        match.bowler_runs = 0
        match.bowler_wickets = 0
        match.bowler_balls = 0
        match.bowler_wides = 0
        match.bowler_no_balls = 0
        
        match.save()
        
        messages.success(request, "Second innings started successfully!")
        return redirect('initialize_match_players', match_id=match.id)
    else:
        messages.error(request, "Cannot start second innings at this time. First innings must be completed.")
        return redirect('match_detail', match_id=match_id)
    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_score(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            # Add Runs
            if action == 'add_runs':
                runs = int(request.POST.get('runs', 0))
                match.total_runs += runs
                match.striker_runs += runs
                match.striker_balls += 1
                striker_performance = BattingPerformance.objects.get(
                    player=match.striker,
                    match=match,
                    )
                bowler_performance = BowlingPerformance.objects.get(
                    player=match.bowler,
                    match=match,
                    )
                bowler_performance.runs_conceded += runs
                bowler_performance.overs += 0.1
                econ_overs=bowler_performance.overs//1
                econ_temp=math.floor(bowler_performance.overs)
                econ_balls=bowler_performance.overs-econ_temp
                t_balls=((econ_overs*6)+econ_balls*10)
                if t_balls!=0: 
                    bowler_performance.economy = round((bowler_performance.runs_conceded / t_balls) * 6, 2)
                bowler_performance.save()
                striker_performance.runs += runs
                striker_performance.balls_faced += 1
                # Update boundaries
                if runs == 4:
                    match.striker_fours += 1
                    striker_performance.fours += 1
                elif runs == 6:
                    match.striker_sixes += 1
                    striker_performance.sixes += 1
                
                match.bowler_runs += runs
                match.bowler_balls += 1
                striker_performance.save()
                
                # Rotate strike for odd runs
                if runs % 2 != 0:
                    match.striker, match.non_striker = match.non_striker, match.striker
                    match.striker_runs, match.non_striker_runs = match.non_striker_runs, match.striker_runs
                    match.striker_balls, match.non_striker_balls = match.non_striker_balls, match.striker_balls
                    match.striker_fours, match.non_striker_fours = match.non_striker_fours, match.striker_fours
                    match.striker_sixes, match.non_striker_sixes = match.non_striker_sixes, match.striker_sixes
                
                match.current_ball += 1
                crr_balls=match.current_over*6+match.current_ball
                match.current_run_rate=round((match.total_runs/crr_balls)*6,2)
                match.save()
                
                return JsonResponse({
                    'status': 'success',
                    'total_runs': match.total_runs,
                    'total_wickets': match.total_wickets,
                    'current_over': f"{match.current_over}.{match.current_ball}",
                    'striker': {
                        'name': match.striker.name,
                        'runs': match.striker_runs,
                        'balls': match.striker_balls,
                        'fours': match.striker_fours,
                        'sixes': match.striker_sixes,
                    },
                    'bowler': {
                        'name': match.bowler.name,
                        'runs': match.bowler_runs,
                        'wickets': match.bowler_wickets,
                        'overs': f"{match.bowler_balls//6}.{match.bowler_balls%10}",
                    }
                })
            
            # Add Wide
            elif action == 'add_wide':
                match.total_runs += 1
                match.bowler_runs += 1
                match.bowler_wides += 1
                crr_balls=match.current_over*6+match.current_ball
                match.current_run_rate=round((match.total_runs/crr_balls)*6,2)
                match.save()
                bowler_performance = BowlingPerformance.objects.get(
                    player=match.bowler,
                    match=match,
                    )
                bowler_performance.runs_conceded += 1
                econ_overs=bowler_performance.overs//1
                econ_temp=math.floor(bowler_performance.overs)
                econ_balls=bowler_performance.overs-econ_temp
                t_balls=((econ_overs*6)+econ_balls*10)
                if t_balls!=0: 
                    bowler_performance.economy = round((bowler_performance.runs_conceded / t_balls) * 6, 2)
                bowler_performance.save()
                
                return JsonResponse({
                    'status': 'success',
                    'total_runs': match.total_runs,
                    'bowler_runs': match.bowler_runs,
                })
            
            # Add No Ball
            elif action == 'add_noball':
                match.total_runs += 1
                match.bowler_runs += 1
                match.bowler_no_balls += 1
                crr_balls=match.current_over*6+match.current_ball
                match.current_run_rate=round((match.total_runs/crr_balls)*6,2)
                match.save()
                bowler_performance = BowlingPerformance.objects.get(
                    player=match.bowler,
                    match=match,
                    )
                bowler_performance.runs_conceded += 1
                econ_overs=bowler_performance.overs//1
                econ_temp=math.floor(bowler_performance.overs)
                econ_balls=bowler_performance.overs-econ_temp
                t_balls=((econ_overs*6)+econ_balls*10)
                if t_balls!=0: 
                    bowler_performance.economy = round((bowler_performance.runs_conceded / t_balls) * 6, 2)
                bowler_performance.save()
                return JsonResponse({
                    'status': 'success',
                    'total_runs': match.total_runs,
                    'bowler_runs': match.bowler_runs,
                })
            
            # Add Wicket
            elif action == 'add_wicket':
                wicket_type = request.POST.get('wicket_type', 'bowled')
                out_player = request.POST.get('out_player', 'striker')
                
                # Update match stats
                match.total_wickets += 1
                match.bowler_wickets += 1
                match.current_ball += 1
                crr_balls=match.current_over*6+match.current_ball
                match.current_run_rate=round((match.total_runs/crr_balls)*6,2)
                striker_performance = BattingPerformance.objects.get(
                    player=match.striker,
                    match=match,
                    )
                striker_performance.balls_faced += 1
                striker_performance.not_out = False
                bowler_performance = BowlingPerformance.objects.get(
                    player=match.bowler,
                    match=match,
                    )
                striker_performance.not_out = False
                bowler_performance.wickets += 1
                bowler_performance.overs += 0.1
                econ_overs=bowler_performance.overs//1
                econ_temp=math.floor(bowler_performance.overs)
                econ_balls=bowler_performance.overs-econ_temp
                t_balls=((econ_overs*6)+econ_balls*10)
                if t_balls!=0: 
                    bowler_performance.economy = round((bowler_performance.runs_conceded / t_balls) * 6, 2)
                bowler_performance.save()
                match.save()
                
                
                # Clear batsman position
                if out_player == 'striker':
                    match.striker = None
                    match.striker_runs = 0
                    match.striker_balls = 0
                    match.striker_fours = 0
                    match.striker_sixes = 0
                else:
                    match.non_striker = None
                    match.non_striker_runs = 0
                    match.non_striker_balls = 0
                    match.non_striker_fours = 0
                    match.non_striker_sixes = 0
                
                match.save()
                
                # Get available batsmen
                batting_team = match.batting_team
                out_batsmen = BattingPerformance.objects.filter(
                    match=match,
                    innings=match.innings,
                    not_out=False
                ).values_list('player_id', flat=True)
                
                available_batsmen = batting_team.players.exclude(
                    id__in=out_batsmen
                ).exclude(
                    id__in=[match.striker.id if match.striker else 0, 
                           match.non_striker.id if match.non_striker else 0]
                )
                
                return JsonResponse({
                    'status': 'success',
                    'total_wickets': match.total_wickets,
                    'available_batsmen': [{'id': p.id, 'name': p.name} for p in available_batsmen],
                    'needs_new_batsman': True
                })
            
            # Complete Over
            elif action == 'complete_over':


                bowler_performance = BowlingPerformance.objects.get(
                    player=match.bowler,
                    match=match,
                    )
                if(match.bowler_runs==0):
                    bowler_performance.maidens += 1
                bowler_performance.overs = math.ceil(bowler_performance.overs)
                bowler_performance.save()
                
                # Reset bowler stats
                match.bowler_runs = 0
                match.bowler_wickets = 0
                match.bowler_balls = 0
                match.bowler_wides = 0
                match.bowler_no_balls = 0
                
                # Rotate strike
                if match.striker and match.non_striker:
                    match.striker, match.non_striker = match.non_striker, match.striker
                    match.striker_runs, match.non_striker_runs = match.non_striker_runs, match.striker_runs
                    match.striker_balls, match.non_striker_balls = match.non_striker_balls, match.striker_balls
                    match.striker_fours, match.non_striker_fours = match.non_striker_fours, match.striker_fours
                    match.striker_sixes, match.non_striker_sixes = match.non_striker_sixes, match.striker_sixes
                
                # Update over count
                match.current_ball = 0
                match.current_over += 1
                match.save()
                
                # Get available bowlers
                available_bowlers = match.bowling_team.players.exclude(id=match.bowler.id if match.bowler else 0)
                
                return JsonResponse({
                    'status': 'success',
                    'current_over': match.current_over,
                    'available_bowlers': [{'id': p.id, 'name': p.name} for p in available_bowlers],
                    'needs_new_bowler': True
                })
            
            # Complete Innings
            elif action == 'complete_innings':                
                # Switch innings if first innings
                if match.innings == 1:
                    match.innings = 2
                    match.batting_team, match.bowling_team = match.bowling_team, match.batting_team
                    
                    
                    # Reset all counters
                    match.current_over = 0
                    match.current_ball = 0
                    match.total_runs = 0
                    match.total_wickets = 0
                    match.striker = None
                    match.non_striker = None
                    match.striker_runs = 0
                    match.striker_balls = 0
                    match.striker_fours = 0
                    match.striker_sixes = 0
                    match.non_striker_runs = 0
                    match.non_striker_balls = 0
                    match.non_striker_fours = 0
                    match.non_striker_sixes = 0
                    match.bowler = None
                    match.bowler_runs = 0
                    match.bowler_wickets = 0
                    match.bowler_balls = 0
                    match.bowler_wides = 0
                    match.bowler_no_balls = 0
                    
                    match.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Second innings started',
                        'new_innings': True,
                        'batting_team': match.batting_team.name,
                        'bowling_team': match.bowling_team.name
                    })
                
                # Complete match if second innings
                else:
                    match.is_live = False
                    match.status = 'COMPLETED'
                    
                    # Determine winner
                    first_innings_runs = BattingPerformance.objects.filter(
                        match=match, innings=1
                    ).aggregate(total=Sum('runs'))['total'] or 0
                    
                    second_innings_runs = BattingPerformance.objects.filter(
                        match=match, innings=2
                    ).aggregate(total=Sum('runs'))['total'] or 0
                    
                    if first_innings_runs > second_innings_runs:
                        match.winner = match.bowling_team
                        match.result = f"{match.winner.name} won by {first_innings_runs - second_innings_runs} runs"
                    elif second_innings_runs > first_innings_runs:
                        match.winner = match.batting_team
                        wickets_left = 10 - match.total_wickets
                        match.result = f"{match.winner.name} won by {wickets_left} wickets"
                    else:
                        match.result = "Match tied"
                    
                    match.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Match completed',
                        'result': match.result,
                        'winner': match.winner.name if match.winner else None
                    })
            
            # Complete Match
            elif action == 'complete_match':
                match.is_live = False
                match.status = 'COMPLETED'
                
                
                # Determine result
                if match.innings == 1:
                    match.result = "Match abandoned after first innings"
                else:
                    first_innings_runs = BattingPerformance.objects.filter(
                        match=match, innings=1
                    ).aggregate(total=Sum('runs'))['total'] or 0
                    
                    second_innings_runs = BattingPerformance.objects.filter(
                        match=match, innings=2
                    ).aggregate(total=Sum('runs'))['total'] or 0
                    
                    if first_innings_runs > second_innings_runs:
                        match.winner = match.bowling_team
                        match.result = f"{match.winner.name} won by {first_innings_runs - second_innings_runs} runs"
                    elif second_innings_runs > first_innings_runs:
                        match.winner = match.batting_team
                        wickets_left = 10 - match.total_wickets
                        match.result = f"{match.winner.name} won by {wickets_left} wickets"
                    else:
                        match.result = "Match tied"
                
                match.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Match completed',
                    'result': match.result,
                    'winner': match.winner.name if match.winner else None
                })
            
            # Set Next Batsman
            elif action == 'set_next_batsman':
                batsman_id = request.POST.get('batsman_id')
                position = request.POST.get('position', 'striker')
                
                new_batsman = Player.objects.get(id=batsman_id)
                BattingPerformance.objects.create(
                        player=new_batsman,
                        match=match,
                        innings=match.innings,
                        runs=0,
                        balls_faced=0,
                        fours=0,
                        sixes=0,
                        not_out=True
                    )
                
                if position == 'striker':
                    match.striker = new_batsman
                    match.striker_runs = 0
                    match.striker_balls = 0
                    match.striker_fours = 0
                    match.striker_sixes = 0
                else:
                    match.non_striker = new_batsman
                    match.non_striker_runs = 0
                    match.non_striker_balls = 0
                    match.non_striker_fours = 0
                    match.non_striker_sixes = 0
                
                match.save()
                
                return JsonResponse({
                    'status': 'success',
                    'striker': {
                        'name': match.striker.name,
                        'runs': match.striker_runs,
                        'balls': match.striker_balls,
                    },
                    'non_striker': {
                        'name': match.non_striker.name if match.non_striker else '',
                        'runs': match.non_striker_runs,
                        'balls': match.non_striker_balls,
                    }
                })
            
            # Set Next Bowler
            elif action == 'set_next_bowler':
                bowler_id = request.POST.get('bowler_id')
                new_bowler = Player.objects.get(id=bowler_id)
                match.bowler = new_bowler

                try:
                    bowling_performance = BowlingPerformance.objects.get(
                        player=new_bowler,
                        match=match
                    )
                    created = False
                except BowlingPerformance.DoesNotExist:
                    # Create new bowling performance if not found
                    bowling_performance = BowlingPerformance.objects.create(
                        player=new_bowler,
                        match=match,
                        runs_conceded=0,
                        wickets=0,
                        innings=match.innings,
                        overs=0,
                        maidens=0,
                        economy=0,
                    )
                    created = True
                match.bowler_runs = 0
                match.bowler_wickets = 0
                match.bowler_balls = 0
                match.bowler_wides = 0
                match.bowler_no_balls = 0
                match.save()
                
                return JsonResponse({
                    'status': 'success',
                    'bowler': {
                        'name': match.bowler.name,
                        'runs': match.bowler_runs,
                        'wickets': match.bowler_wickets,
                    }
                })
            
            # Set Man of the Match
            elif action == 'set_motm':
                motm_id = request.POST.get('motm_id')
                match.man_of_the_match = Player.objects.get(id=motm_id)
                match.save()
                
                return JsonResponse({
                    'status': 'success',
                    'motm': match.man_of_the_match.name
                })
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # GET request - render template
    batting_players = match.batting_team.players.all()
    bowling_players = match.bowling_team.players.all()
    
    out_batsmen = BattingPerformance.objects.filter(
        match=match,
        innings=match.innings,
        not_out=False
    ).values_list('player_id', flat=True)
    
    available_batsmen = batting_players.exclude(
        id__in=out_batsmen
    ).exclude(
        id__in=[match.striker.id if match.striker else 0, 
               match.non_striker.id if match.non_striker else 0]
    )
    
    available_bowlers = bowling_players.exclude(
        id=match.bowler.id if match.bowler else 0
    )
    
    context = {
        'match': match,
        'batting_players': batting_players,
        'bowling_players': bowling_players,
        'available_batsmen': available_batsmen,
        'available_bowlers': available_bowlers,
        'all_players': Player.objects.filter(
            Q(team=match.home_team) | Q(team=match.away_team)
        ),
    }
    
    return render(request, 'tournament/update_score.html', context)