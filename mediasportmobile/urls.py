from django.conf.urls import url
from mediasportmobile import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

urlpatterns = [
    url(r'^$', views.home_page, name='home_page'),
    url(r'^matches/$', views.match_list),
    url(r'data/$', views.data_list),
    url(r'^matches/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$', views.match_detail),
    url(r'events/$', views.event_list),
    url(r'leagues/$', views.league_page, name='leagues'),
    url(r'leagues/(?P<pk>\w+-\w+-\w+-\w+-\w+)$', views.league_teams, name='league_teams'),
    url(r'edit_delete_league/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$',
        views.edit_delete_league,
        name='edit_delete_league'),
    url(r'leagues/(?P<lk>\w+-\w+-\w+-\w+-\w+)/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$',
        views.edit_delete_team,
        name='edit_delete_team'),
    url(r'team_players/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$',
        views.team_players,
        name='team_players'),
    url(r'team_players/(?P<tk>\w+-\w+-\w+-\w+-\w+)/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$',
        views.edit_delete_player,
        name='edit_delete_player'),
    url(r'goalkeeper_stat_test/$', views.goalkeeper_stat_test, name='goalkeeper_stat_test'),
    url(r'player_stat_test/$', views.player_stat_test, name='player_stat_test'),
    url(r'stat_players/$', views.stat_players, name='stat_players'),
    url(r'match_test/$', views.match_test, name='match_test'),
    url(r'stat_match/$', views.stat_match, name='stat_match'),
    url(r'stat_general/$', views.general_stat, name='general_stat'),
    url(r'match_event/$', views.match_event, name='match_event'),
    url(r'efficiency_stat/$', views.efficiency_stat, name='efficiency_stat'),
    url(r'add_user/$', views.user_add, name='user_add'),
    url(r'login/$', views.login_view, name='login'),
    url(r'logout/', views.logout_view, name='logout'),
    url(r'users/$', views.user_list, name='user_list'),
    url(r'^users/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$', views.edit_user, name='edit_user'),
    url(r'^user_delete/(?P<pk>\w+-\w+-\w+-\w+-\w+)/$', views.delete_user, name='delete_user'),
    url(r'^user_profile/$', views.user_profile, name='user_profile'),
    url(r'^user_edit_profile/$', views.user_edit_profile, name='user_edit_profile'),
    url(r'played_matches/$', views.all_matches, name='all_matches'),
]

urlpatterns = format_suffix_patterns(urlpatterns)

if settings.DEBUG:
    if settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT)
# Эта строка опциональна и будет добавлять url'ы только при DEBUG = True

urlpatterns += staticfiles_urlpatterns()