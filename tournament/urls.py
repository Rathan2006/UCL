from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('teams/', views.team_list, name='teams'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('players/', views.player_list, name='players'),
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),
    path('matches/', views.match_list, name='matches'),
    path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('standings/', views.standings, name='standings'),
    path('matches/<int:match_id>/add-result/', views.add_result, name='add_result'),
    path('accounts/register/', views.register, name='register'),
    path('teams/add/', views.add_team, name='add_team'),
    path('players/add/', views.add_player, name='add_player'),
    path('matches/<int:match_id>/live/', views.update_live_score, name='update_live_score'),
    path('api/matches/<int:match_id>/live/', views.get_live_score, name='get_live_score'),
    path('api/matches/<int:match_id>/update/', views.update_score_api, name='update_score_api'),
    path('matches/<int:match_id>/live/update/', views.update_live_score, name='update_live_score'),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('player_stats/', views.player_stats, name='player_stats'),
    ]