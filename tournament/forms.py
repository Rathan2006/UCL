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