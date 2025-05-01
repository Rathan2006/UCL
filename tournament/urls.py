from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('index', views.index, name='index'),
    path('teams/', views.team_list, name='teams'),
    path('login/', views.login_view,name='login'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('players/', views.player_list, name='players'),
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),
    path('matches/', views.match_list, name='matches'),
    path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('standings/', views.standings, name='standings'),
    path('accounts/register/', views.register, name='register'),
    path('teams/add/', views.add_team, name='add_team'),
    path('players/add/', views.add_player, name='add_player'),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('player_stats/', views.player_stats, name='player_stats'),
    path('match/<int:match_id>/set_live/', views.set_match_live, name='set_match_live'),
    path('match/<int:match_id>/update_score/', views.update_score, name='update_score'),
    path('match/<int:match_id>/update/', views.update_score, name='update_score'),

    path('match/<int:match_id>/start_second_innings/', views.start_second_innings, name='start_second_innings'),
    path('match/<int:match_id>/initialize/', views.initialize_match_players, name='initialize_match_players'),
    path('match/<int:match_id>/live_data/', views.live_match_data, name='live_match_data'),
    path('match/<int:match_id>/performances/', views.match_performances, name='match_performances'),
    path('match/<int:match_id>/update/', views.update_score, name='update_score'),
    path('match/<int:match_id>/initialize/', views.initialize_match_players, name='initialize_match_players'),


    path('match/<int:match_id>/live_data/', views.live_match_data, name='live_match_data'),
    path('match/<int:match_id>/performances/', views.match_performances, name='match_performances'),
    
]
    