from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required,permission_required
from django.utils import timezone
from .models import Team, Player, Match, BattingPerformance, BowlingPerformance
from .forms import MatchResultForm,TeamForm, PlayerForm, LiveScoreForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,logout
from django.http import JsonResponse
from django import forms
from django import template
from django.db.models import Q,F
from django.db.models import Count, Case, When, IntegerField

def index(request):
    upcoming_matches = Match.objects.filter(date__gte=timezone.now()).order_by('date')[:5]
    recent_matches = Match.objects.filter(date__lt=timezone.now()).order_by('-date')[:5]
    context = {
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
    }
    return render(request, 'tournament/index.html', context)

def team_list(request):
    teams = Team.objects.all().order_by('name')
    return render(request, 'tournament/teams.html', {'teams': teams})

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

def player_list(request):
    players = Player.objects.all().order_by('team', 'name')
    return render(request, 'tournament/players.html', {'players': players})

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
    upcoming_matches = Match.objects.filter(date__gte=timezone.now()).order_by('date')
    past_matches = Match.objects.filter(date__lt=timezone.now()).order_by('-date')
    return render(request, 'tournament/matches.html', {
        'upcoming_matches': upcoming_matches,
        'past_matches': past_matches,
    })

def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    batting_performances = BattingPerformance.objects.filter(match=match).select_related('player')
    bowling_performances = BowlingPerformance.objects.filter(match=match).select_related('player')
    
    context = {
        'match': match,
        'batting_performances': batting_performances,
        'bowling_performances': bowling_performances,
    }
    return render(request, 'tournament/match_detail.html', context)

# views.py
from django.db.models import Count, Case, When, IntegerField, Sum

def standings(request):
    # First update all team stats
    for team in Team.objects.all():
        team.update_stats()
    
    # Get teams ordered by points and wins
    teams = Team.objects.all().order_by('-points', '-wins')
    return render(request, 'tournament/standings.html', {'standings': teams})

@login_required
def add_result(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    
    if request.method == 'POST':
        form = MatchResultForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect('match_detail', match_id=match.id)
    else:
        form = MatchResultForm(instance=match)
    
    return render(request, 'tournament/add_result.html', {
        'form': form,
        'match': match,
    })
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
class LiveScoreForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_score', 'away_score', 'current_batsman', 'current_bowler', 'balls_remaining']
def get_live_score(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    data = {
        'home_score': match.home_score,
        'away_score': match.away_score,
        'current_batsman': match.current_batsman.name if match.current_batsman else '',
        'current_bowler': match.current_bowler.name if match.current_bowler else '',
        'balls_remaining': match.balls_remaining,
        'innings': match.innings,
    }
    return JsonResponse(data)

@login_required
def update_score_api(request, match_id):
    if request.method == 'POST' and request.is_ajax():
        match = get_object_or_404(Match, pk=match_id)
        # Process update from POST data
        match.home_score = request.POST.get('home_score', match.home_score)
        match.away_score = request.POST.get('away_score', match.away_score)
        match.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
@login_required
def update_live_score(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.method == 'POST':
        # Process score update
        runs = int(request.POST.get('runs', 0))
        is_wicket = request.POST.get('is_wicket') == 'on'
        
        # Update match score
        if match.batting_team == match.home_team:
            match.home_score += runs
        else:
            match.away_score += runs
        
        # Update player stats if needed
        if is_wicket:
            bowler = match.current_bowler
            if bowler:
                bowler.wickets += 1
                bowler.save()
        
        # Update ball count
        match.current_ball += 1
        if match.current_ball > 5:
            match.current_ball = 0
            match.current_over += 1
        
        match.save()
        return redirect('match_detail', match_id=match.id)
    
    return render(request, 'tournament/update_live.html', {'match': match})


def custom_logout(request):
    logout(request)
    return redirect('index')  # Redirect to your homepage


@login_required
def dashboard(request):
    user_teams = Team.objects.filter(manager=request.user)
    context = {
        'user_teams': user_teams,
    }
    return render(request, 'tournament/dashboard.html', context)

def team_list(request):
    if request.user.is_authenticated:
        teams = Team.objects.all()
    else:
        teams = Team.objects.filter(manager__isnull=True)
    
    return render(request, 'tournament/teams.html', {'teams': teams})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'tournament/profile.html', {'form': form})


@login_required
def player_stats(request):
    return render(request, 'tournament/player_stats.html', {
        'batting_performances': BattingPerformance.objects.all(),
        'bowling_performances': BowlingPerformance.objects.all(),
    })