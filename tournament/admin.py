from django.contrib import admin
from .models import Team, Player, Match, BattingPerformance, BowlingPerformance

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 1

class TeamAdmin(admin.ModelAdmin):
    inlines = [PlayerInline]
    list_display = ('name', 'home_ground', 'coach', 'founded')
    search_fields = ('name', 'home_ground')

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'age', 'role', 'jersey_number')
    list_filter = ('team', 'role', 'batting_style', 'bowling_style')
    search_fields = ('name', 'team__name')

class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_number', 'home_team', 'away_team', 'date', 'venue', 'result')
    list_filter = ('result', 'date')
    search_fields = ('home_team__name', 'away_team__name', 'venue')

admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(BattingPerformance)
admin.site.register(BowlingPerformance)