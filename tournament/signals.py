from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, Team
from django.db.models import Q

@receiver(post_save, sender=Match)
def update_team_stats(sender, instance, **kwargs):
    """
    Update team statistics when a match is saved
    """
    if instance.status == 'COMPLETED':
        # Update home team stats
        home_team = instance.home_team
        home_team.matches_played = Match.objects.filter(
            Q(home_team=home_team) | Q(away_team=home_team),
            status='COMPLETED'
        ).count()
        home_team.save()
        
        # Update away team stats
        away_team = instance.away_team
        away_team.matches_played = Match.objects.filter(
            Q(home_team=away_team) | Q(away_team=away_team),
            status='COMPLETED'
        ).count()
        away_team.save()