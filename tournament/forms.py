from django import forms
from .models import Match,Team, Player

class MatchResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['result', 'man_of_the_match', 'home_score', 'away_score', 'current_batsman', 'current_bowler', 'balls_remaining', 'innings']
        widgets = {
            'result': forms.Select(attrs={'class': 'form-control'}),
            'man_of_the_match': forms.Select(attrs={'class': 'form-control'}),
            'home_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'away_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_batsman': forms.Select(attrs={'class': 'form-control'}),
            'current_bowler': forms.Select(attrs={'class': 'form-control'}),
            'balls_remaining': forms.NumberInput(attrs={'class': 'form-control'}),
            'innings': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Only show players from the teams in this match
            self.fields['man_of_the_match'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            ).order_by('name')
            self.fields['current_batsman'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            ).order_by('name')
            self.fields['current_bowler'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            ).order_by('name')
class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo', 'home_ground', 'coach', 'founded']
        widgets = {
            'founded': forms.NumberInput(attrs={'min': 1800, 'max': 2023}),
        }

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = '__all__'
        widgets = {
            'age': forms.NumberInput(attrs={'min': 16, 'max': 50}),
            'jersey_number': forms.NumberInput(attrs={'min': 1, 'max': 99}),
        }

class LiveScoreForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_score', 'away_score', 'current_batsman', 'current_bowler', 'balls_remaining', 'innings']
        widgets = {
            'home_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'away_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_batsman': forms.Select(attrs={'class': 'form-control'}),
            'current_bowler': forms.Select(attrs={'class': 'form-control'}),
            'balls_remaining': forms.NumberInput(attrs={'class': 'form-control'}),
            'innings': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['current_batsman'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            )
            self.fields['current_bowler'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            )

class TossForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['toss_winner', 'toss_decision']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['toss_winner'].queryset = Team.objects.filter(
            id__in=[self.instance.home_team_id, self.instance.away_team_id]
        )

class LiveScoreForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['striker', 'non_striker', 'bowler']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['striker'].queryset = Player.objects.filter(team=self.instance.batting_team)
            self.fields['non_striker'].queryset = Player.objects.filter(team=self.instance.batting_team)
            self.fields['bowler'].queryset = Player.objects.filter(team=self.instance.bowling_team)

class NextBatsmanForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['next_batsman']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['next_batsman'].queryset = Player.objects.filter(
                team=self.instance.batting_team
            ).exclude(
                id__in=[self.instance.striker_id, self.instance.non_striker_id]
            )

class NextBowlerForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['next_bowler']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['next_bowler'].queryset = Player.objects.filter(
                team=self.instance.bowling_team
            ).exclude(id=self.instance.bowler_id)
class AddRunsForm(forms.Form):
    runs = forms.IntegerField(
        min_value=0,
        max_value=6,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class NextBatsmanForm(forms.Form):
    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match')
        super().__init__(*args, **kwargs)
        self.fields['batsman'] = forms.ModelChoiceField(
            queryset=match.get_available_batsmen(),
            widget=forms.Select(attrs={'class': 'form-select'}),
            label="Select next batsman"
        )

class NextBowlerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        match = kwargs.pop('match')
        super().__init__(*args, **kwargs)
        self.fields['bowler'] = forms.ModelChoiceField(
            queryset=match.get_available_bowlers(),
            widget=forms.Select(attrs={'class': 'form-select'}),
            label="Select next bowler"
        )

class PlayerSelectionForm(forms.Form):
    striker = forms.ModelChoiceField(queryset=None, label="Striker")
    non_striker = forms.ModelChoiceField(queryset=None, label="Non-Striker")
    bowler = forms.ModelChoiceField(queryset=None, label="Bowler")

    def __init__(self, *args, **kwargs):
        first_team_players = kwargs.pop('first_team_players')
        second_team_players = kwargs.pop('second_team_players')
        super().__init__(*args, **kwargs)
        self.fields['striker'].queryset = first_team_players
        self.fields['non_striker'].queryset = first_team_players
        self.fields['bowler'].queryset = second_team_players

class ScoreUpdateForm(forms.Form):
    runs = forms.IntegerField(required=False)
    extras = forms.ChoiceField(
        choices=[('', 'None'), ('wide', 'Wide'), ('no_ball', 'No Ball')],
        required=False
    )
    wicket_type = forms.ChoiceField(
        choices=[
            ('', 'None'),
            ('bowled', 'Bowled'),
            ('caught', 'Caught'),
            ('lbw', 'LBW'),
            ('stumped', 'Stumped'),
            ('run_out', 'Run Out'),
            ('hit_wicket', 'Hit Wicket')
        ],
        required=False
    )
    out_batsman = forms.ChoiceField(
        choices=[('', 'None'), ('striker', 'Striker'), ('non_striker', 'Non-Striker')],
        required=False
    )
    next_batsman = forms.ModelChoiceField(queryset=None, required=False)
    fielder = forms.ModelChoiceField(queryset=None, required=False)
    complete_over = forms.BooleanField(required=False)
    complete_match = forms.BooleanField(required=False)
    start_second_innings = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        first_team_players = kwargs.pop('first_team_players')
        second_team_players = kwargs.pop('second_team_players')
        super().__init__(*args, **kwargs)
        self.fields['next_batsman'].queryset = first_team_players
        self.fields['fielder'].queryset = second_team_players