from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match

@receiver(post_save, sender=Match)
def update_team_stats(sender, instance, **kwargs):
    if instance.status == 'COMPLETED':
        home_team = instance.home_team
        away_team = instance.away_team

        # Update matches played count
        home_team.matches_played = Match.objects.filter(
            models.Q(home_team=home_team) | models.Q(away_team=home_team),
            status='COMPLETED'
        ).count()
        away_team.matches_played = Match.objects.filter(
            models.Q(home_team=away_team) | models.Q(away_team=away_team),
            status='COMPLETED'
        ).count()

        # Update wins/losses/draws based on result
        if instance.result == 'Home Win':
            home_team.wins += 1
            away_team.losses += 1
        elif instance.result == 'Away Win':
            away_team.wins += 1
            home_team.losses += 1
        elif instance.result == 'Draw':
            home_team.draws += 1
            away_team.draws += 1

        home_team.save()
        away_team.save()