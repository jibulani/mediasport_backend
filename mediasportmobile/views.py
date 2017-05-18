from . import models
from . import serializers
from . import forms
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect, render_to_response # HttpResponse
# from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse , HttpResponse
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
import datetime
import json
from django.contrib.auth.decorators import (
    login_required, permission_required
)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.messages import error
from django.contrib.auth.models import Permission
from django.template import RequestContext
from django.http import QueryDict

# MATCH_DURATION = 90

@csrf_exempt
def match_list(request):
    if request.method == 'GET':
        matches = models.Match.objects.all()
        serializer = serializers.MatchSerializer(matches, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = serializers.MatchSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def data_list(request):
    if request.method == 'GET':
        leagues = models.League.objects.all()
        league_list = []
        for league in leagues:
            teams = models.Team.objects.filter(league_id=league)
            team_list = []
            for team in teams:
                players = models.Player.objects.filter(team=team)
                player_list = []
                for player in players:
                    curr_player = {}
                    curr_player['id'] = str(player.id)
                    curr_player['name'] = player.__str__()
                    curr_player['number'] = player.number
                    if player.position == 'Вратарь':
                        curr_player['type'] = 'goalkeeper'
                    elif player.position == 'Защитник':
                        curr_player['type'] = 'defender'
                    elif player.position == 'Универсал':
                        curr_player['type'] = 'midfielder'
                    else:
                        curr_player['type'] = 'forward'
                    player_list.append(curr_player)
                curr_team = {}
                curr_team['id'] = str(team.id)
                curr_team['name'] = team.name
                curr_team['players'] = player_list
                team_list.append(curr_team)
            curr_league = {}
            curr_league['id'] = str(league.id)
            curr_league['name'] = league.name
            curr_league['teams'] = team_list
            league_list.append(curr_league)
        data = {'leagues': league_list}
        data = json.dumps(data, ensure_ascii=False)
        return HttpResponse(data)


@csrf_exempt
def match_detail(request, pk, format=None):
    try:
        match = models.Match.objects.get(pk=pk)
    except models.Match.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = serializers.MatchSerializer(match)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'PUT':
        serializer = serializers.MatchSerializer(match, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        match.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@csrf_exempt
def event_list(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        # match_info = JSONParser().parse(data.match_info)
        match_info = data['match_info']
        match_date = datetime.datetime.fromtimestamp(timestamp=float(match_info['date']/1000)).date()
        home_team = models.Team.objects.get(id=match_info['team_home_id'])
        guest_team = models.Team.objects.get(id=match_info['team_guest_id'])
        try:
            match = models.Match.objects.get(home_team=home_team,
                                             guest_team=guest_team,
                                             date=match_date)
            match.home_team_goals = match_info['home_goals']
            match.guest_team_goals = match_info['guest_goals']
        except ObjectDoesNotExist:
            match = models.Match.objects.create(home_team=home_team,
                                                guest_team=guest_team,
                                                date=match_date,
                                                home_team_goals=match_info['home_goals'],
                                                guest_team_goals=match_info['guest_goals'])
        match.save()

        for event in data['stats']:
            player = models.Player.objects.get(id=event['player'])
            match_event = models.MatchEvent.objects.create(match=match, player=player,
                                                           event_type=event['event'],
                                                           event_value=event['sub_event'],
                                                           event_time=int(event['time']/60000))
            match_event.save()
            if player.position == 'Вратарь':
                try:
                    goalkeeper_stat = models.GoalkeeperStat.objects.get(goalkeeper_id=player,
                                                                        match_id=match)
                except ObjectDoesNotExist:
                    goalkeeper_stat = models.GoalkeeperStat.objects.create(goalkeeper_id=player,
                                                                           match_id=match,
                                                                           goals=0, passes=0,
                                                                           missed_goals=0,
                                                                           yellow_cards=0,
                                                                           red_cards=0, mins=0,
                                                                           shots_on_target=0,
                                                                           beat_off_shots=0,
                                                                           dr_plus=0, dr_minus=0,
                                                                           errors=0, saves=0,
                                                                           min_in=0, min_out=0)
                goalkeeper_stat.save()
                if match_event.event_type == 'result':
                    if match_event.event_value == 'goal':
                        goalkeeper_stat.goals += 1
                    elif match_event.event_value == 'pass':
                        goalkeeper_stat.passes += 1
                elif match_event.event_type == 'dribble_successful':
                    goalkeeper_stat.dr_plus += 1
                elif match_event.event_type == 'dribble_unsuccessful':
                    goalkeeper_stat.dr_minus += 1
                elif match_event.event_type == 'parried':
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.beat_off_shots += 1
                elif match_event.event_type == 'goal':
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.missed_goals += 1
                elif match_event.event_type == 'mistake':
                    goalkeeper_stat.errors += 1
                    if match_event.event_value == 'goal':
                        goalkeeper_stat.missed_goals += 1
                        goalkeeper_stat.shots_on_target += 1
                    elif match_event.event_value == 'yellow_card':
                        goalkeeper_stat.yellow_cards += 1
                    elif match_event.event_value == 'red_card':
                        goalkeeper_stat.red_cards += 1
                elif match_event.event_type == 'save':
                    goalkeeper_stat.saves += 1
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.beat_off_shots += 1
                elif match_event.event_type == 'replaced_to_match':
                    goalkeeper_stat.min_in = match_event.event_time
                elif match_event.event_type == 'replaced_from_match':
                    goalkeeper_stat.min_out = match_event.event_time
                    goalkeeper_stat.mins += goalkeeper_stat.min_out - goalkeeper_stat.min_in
                goalkeeper_stat.save()


            else:
                try:
                    player_stat = models.PlayerStat.objects.get(player_id=player,
                                                                match_id=match)
                except:
                    player_stat = models.PlayerStat.objects.create(player_id=player, match_id=match,
                                                                   goals=0, passes=0, yellow_cards=0,
                                                                   red_cards=0, mins=0, foul_plus=0,
                                                                   foul_minus=0, dr_plus=0, dr_minus=0,
                                                                   lost_ball=0, interceptions=0,
                                                                   in_target=0, out_target=0,
                                                                   min_in=0, min_out=0)
                player_stat.save()
                if match_event.event_type == 'hit':
                    if match_event.event_value == 'goal':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'pass':
                        player_stat.passes += 1
                    elif match_event.event_value == 'goal_from_10':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'goal_from_6':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'no_goal_from_play':
                        player_stat.out_target += 1
                    elif match_event.event_value == 'no_goal_from_target':
                        player_stat.in_target += 1
                elif match_event.event_type == 'dribble_successful':
                    player_stat.dr_plus += 1
                elif match_event.event_type == 'dribble_unsuccessful':
                    player_stat.dr_minus += 1
                elif match_event.event_type == 'intercept':
                    player_stat.interceptions += 1
                elif match_event.event_type == 'lost':
                    player_stat.lost_ball += 1
                elif match_event.event_type == 'foul_on':
                    player_stat.foul_plus += 1
                elif match_event.event_type == 'foul_from':
                    player_stat.foul_minus += 1
                    if match_event.event_value == 'yellow_card':
                        player_stat.yellow_cards += 1
                    elif match_event.event_value == 'red_card':
                        player_stat.red_cards += 1
                elif match_event.event_type == 'replaced_to_match':
                    player_stat.min_in = match_event.event_time
                elif match_event.event_type == 'replaced_from_match':
                    player_stat.min_out = match_event.event_time
                    player_stat.mins += player_stat.min_out - player_stat.min_in
                player_stat.save()
        return HttpResponse(status=200)
    return HttpResponse(status=204)


@login_required
@permission_required('mediasportmobile.can_edit_info')
def league_page(request):

    leagues = models.League.objects.all()
    if request.method == 'POST':
        name = request.POST.get('league', '')
        league = models.League(name=name)
        league.save()
        return HttpResponse('ok')

    return render(
        request, 'leagues.html',
        {'leagues': leagues}
    )

@login_required
@permission_required('mediasportmobile.can_edit_info')
def edit_delete_league(request, pk):
    if request.method == 'DELETE':
        try:
            league_to_delete = models.League.objects.get(id=pk)
            league_to_delete.delete()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    if request.method == 'POST':
        try:
            league_to_edit = models.League.objects.get(id=pk)
            league_to_edit.name = request.POST.get('league', '')
            league_to_edit.save()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    if request.method == 'GET':
        try:
            league = models.League.objects.get(id=pk)
            return JsonResponse({'id': league.id,'name': league.name})
        except ObjectDoesNotExist:
            return JsonResponse({'id':'','name':''})
    leagues = models.League.objects.all()
    return render(
        request, 'leagues.html',
        {'leagues': leagues}
    )

@login_required
@permission_required('mediasportmobile.can_edit_info')
def league_teams(request, pk):
    try:
        teams = models.Team.objects.filter(league_id=pk)
    except ObjectDoesNotExist:
        teams = []
    if request.method == 'POST':
        league = models.League.objects.get(id=pk)
        team_name = request.POST.get('team_name', '')
        agent_name = request.POST.get('agent_name', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        team = models.Team(league_id=league, name=team_name,
                           agent_name=agent_name, phone=phone,
                           e_mail=email)
        team.save()
        return HttpResponse('ok')
    return render(
        request, 'teams.html',
        {'teams': teams}
    )

@login_required
@permission_required('mediasportmobile.can_edit_info')
def edit_delete_team(request, lk, pk):
    if request.method == 'DELETE':
        try:
            team_to_delete = models.Team.objects.get(id=pk)
            team_to_delete.delete()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    if request.method == 'POST':
        try:
            team_to_edit = models.Team.objects.get(id=pk)
            team_to_edit.name = request.POST.get('team_name', '')
            team_to_edit.agent_name = request.POST.get('agent_name', '')
            team_to_edit.phone = request.POST.get('phone', '')
            team_to_edit.e_mail = request.POST.get('email', '')
            team_to_edit.save()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    teams = models.Team.objects.filter(league_id=lk)
    return render(
        request, 'teams.html',
        {'teams': teams}
    )

@login_required
@permission_required('mediasportmobile.can_edit_info')
def team_players(request, pk):
    try:
        players = models.Player.objects.filter(team=pk)
    except ObjectDoesNotExist:
        players = []
    if request.method == 'POST':
        team = models.Team.objects.get(id=pk)
        middle_name = request.POST.get('middle_name', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        number = request.POST.get('number', '')
        position = request.POST.get('position', '')
        player = models.Player(team=team, middle_name=middle_name, first_name=first_name,
                             last_name=last_name, number=number, position=position)
        player.save()
        return HttpResponse('ok')
    return render(
        request, 'players.html',
        {'players': players}
    )

@login_required
@permission_required('mediasportmobile.can_edit_info')
def edit_delete_player(request, tk, pk):
    if request.method == 'DELETE':
        try:
            player_to_delete = models.Player.objects.get(id=pk)
            player_to_delete.delete()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    if request.method == 'POST':
        try:
            player_to_edit = models.Player.objects.get(id=pk)
            player_to_edit.middle_name = request.POST.get('middle_name', '')
            player_to_edit.first_name = request.POST.get('first_name', '')
            player_to_edit.last_name = request.POST.get('last_name', '')
            player_to_edit.number = request.POST.get('number', '')
            player_to_edit.position = request.POST.get('position', '')
            player_to_edit.save()
        except ObjectDoesNotExist:
            return HttpResponse('not ok')
    players = models.Player.objects.filter(team=tk)
    return render(
        request, 'players.html',
        {'players': players}
    )

@login_required
def stat_players(request):
    goalkeeper_statistic = ''
    player_statistic = ''
    leagues = models.League.objects.all()
    if request.method == 'POST' and request.is_ajax():
        league_id = request.POST.get('selected_league', '')
        curr_league = models.League.objects.get(id=league_id)
        teams = models.Team.objects.filter(league_id=curr_league)
        league_teams = []
        for team in teams:
            league_teams.append(team.name)
        return HttpResponseAjax(teams=league_teams)
    if request.method == 'POST':
            team = request.POST.get('team', '')
            try:
                team = models.Team.objects.get(name=team)
            except ObjectDoesNotExist:
                info = 'Команда не выбрана'
                return render(
                    request, 'stat-players.html',
                    {'leagues': leagues, 'goalkeepers': goalkeeper_statistic, 'players': player_statistic,
                     'info': info}
                )
            goalkeepers = models.Player.objects.filter(team=team).filter(position='Вратарь')
            goalkeeper_statistic = []
            for goalkeeper in goalkeepers:

                general_stat = {}
                goalkeeper_stat = models.GoalkeeperStat.objects.filter(goalkeeper_id=goalkeeper)
                if goalkeeper_stat:
                    player_g = models.Player.objects.get(id=goalkeeper.id)
                    general_stat['position'] = player_g.position
                    general_stat['name'] = player_g.__str__()
                    goals = goalkeeper_stat.aggregate(stat_goals=Sum('goals'))['stat_goals']
                    general_stat['goals'] = goals
                    passes = goalkeeper_stat.aggregate(stat_passes=Sum('passes'))['stat_passes']
                    general_stat['passes'] = passes
                    general_stat['goal_pass'] = goals + passes
                    missed_goals = goalkeeper_stat.aggregate(stat_missed_goals=Sum('missed_goals'))['stat_missed_goals']
                    general_stat['missed_goals'] = missed_goals
                    yellow_cards = goalkeeper_stat.aggregate(y_cards=Sum('yellow_cards'))['y_cards']
                    general_stat['yellow_cards'] = yellow_cards
                    red_cards = goalkeeper_stat.aggregate(r_cards=Sum('red_cards'))['r_cards']
                    general_stat['red_cards'] = red_cards
                    games = goalkeeper_stat.aggregate(stat_games=Count('match_id'))['stat_games']
                    general_stat['games'] = games
                    mins = goalkeeper_stat.aggregate(stat_mins=Sum('mins'))['stat_mins']
                    general_stat['mins'] = mins
                    if missed_goals != 0:
                        general_stat['min_missed'] = round(mins / missed_goals, 2)
                    else:
                        general_stat['min_missed'] = 'Нет пропущенных'
                    goalkeeper_statistic.append(general_stat)
                else:
                    player_g = models.Player.objects.get(id=goalkeeper.id)
                    general_stat['position'] = player_g.position
                    general_stat['name'] = player_g.__str__()
                    goals = 0
                    general_stat['goals'] = goals
                    passes = 0
                    general_stat['passes'] = passes
                    general_stat['goal_pass'] = goals + passes
                    missed_goals = 0
                    general_stat['missed_goals'] = missed_goals
                    yellow_cards = 0
                    general_stat['yellow_cards'] = yellow_cards
                    red_cards = 0
                    general_stat['red_cards'] = red_cards
                    games = 0
                    general_stat['games'] = games
                    mins = 0
                    general_stat['mins'] = mins
                    general_stat['min_missed'] = 0
                    goalkeeper_statistic.append(general_stat)
            if not goalkeeper_statistic:
                goalkeeper_statistic = ''

            players = models.Player.objects.filter(team=team).exclude(position='Вратарь')
            player_statistic = []
            for player in players:
                general_stat = {}
                player_stat = models.PlayerStat.objects.filter(player_id=player)
                if player_stat:
                    player_not_g = models.Player.objects.get(id=player.id)
                    general_stat['position'] = player_not_g.position
                    general_stat['name'] = player_not_g.__str__()
                    goals = player_stat.aggregate(stat_goals=Sum('goals'))['stat_goals']
                    general_stat['goals'] = goals
                    passes = player_stat.aggregate(stat_passes=Sum('passes'))['stat_passes']
                    general_stat['passes'] = passes
                    general_stat['goal_pass'] = goals + passes
                    yellow_cards = player_stat.aggregate(y_cards=Sum('yellow_cards'))['y_cards']
                    general_stat['yellow_cards'] = yellow_cards
                    red_cards = player_stat.aggregate(r_cards=Sum('red_cards'))['r_cards']
                    general_stat['red_cards'] = red_cards
                    games = player_stat.aggregate(stat_games=Count('match_id'))['stat_games']
                    general_stat['games'] = games
                    mins = player_stat.aggregate(stat_mins=Sum('mins'))['stat_mins']
                    general_stat['mins'] = mins
                    if goals == 0:
                        general_stat['min_goal'] = 'Нет забитых голов'
                    else:
                        general_stat['min_goal'] = round(mins / goals, 2)
                    player_statistic.append(general_stat)
                else:
                    player_not_g = models.Player.objects.get(id=player.id)
                    general_stat['position'] = player_not_g.position
                    general_stat['name'] = player_not_g.__str__()
                    goals = 0
                    general_stat['goals'] = goals
                    passes = 0
                    general_stat['passes'] = passes
                    general_stat['goal_pass'] = goals + passes
                    yellow_cards = 0
                    general_stat['yellow_cards'] = yellow_cards
                    red_cards = 0
                    general_stat['red_cards'] = red_cards
                    games = 0
                    general_stat['games'] = games
                    mins = 0
                    general_stat['mins'] = mins
                    general_stat['min_goal'] = 0
                    player_statistic.append(general_stat)
            if not player_statistic:
                player_statistic = ''

    return render(
            request, 'stat-players.html',
            {'leagues': leagues, 'goalkeepers': goalkeeper_statistic, 'players': player_statistic,}
        )

@login_required
def stat_match(request):
    info = ''
    goalkeepers_stat_home = ''
    goalkeepers_stat_guest = ''
    field_players_stat_home = ''
    field_players_stat_guest = ''
    goalkeepers_stat_home_general = ''
    goalkeepers_stat_guest_general = ''
    field_players_stat_home_general = ''
    field_players_stat_guest_general = ''
    home_team = ''
    guest_team = ''
    leagues = models.League.objects.all()
    if request.method == 'POST' and request.is_ajax():
        league_id = request.POST.get('selected_league', '')
        curr_league = models.League.objects.get(id=league_id)
        teams = models.Team.objects.filter(league_id=curr_league)
        league_teams = []
        for team in teams:
            league_teams.append(team.name)
        return HttpResponseAjax(teams=league_teams)
    if request.method == 'POST':
        home_team = request.POST.get('home_team', '')
        guest_team = request.POST.get('guest_team', '')
        date = request.POST.get('date', '')
        position = request.POST.get('position', '')
        if not home_team:
            info = 'Не выбрана команда хозяев'
            return render(
                request, 'stat-match.html',
                {'info': info,  # 'form': form,
                 # 'teams': teams,
                 'leagues': leagues,
                 'field_players_stat_home': field_players_stat_home,
                 'field_players_stat_guest': field_players_stat_guest,
                 'goalkeepers_stat_home': goalkeepers_stat_home,
                 'goalkeepers_stat_guest': goalkeepers_stat_guest,
                 'guest_team': guest_team,
                 'goalkeepers_stat_home_general': goalkeepers_stat_home_general,
                 'goalkeepers_stat_guest_general': goalkeepers_stat_guest_general,
                 'field_players_stat_home_general': field_players_stat_home_general,
                 'field_players_stat_guest_general': field_players_stat_guest_general,
                 }
            )
        elif not guest_team:
            info = 'Не выбрана команда гостей'
            return render(
                request, 'stat-match.html',
                {'info': info,
                 'leagues': leagues,
                 'field_players_stat_home': field_players_stat_home,
                 'field_players_stat_guest': field_players_stat_guest,
                 'goalkeepers_stat_home': goalkeepers_stat_home,
                 'goalkeepers_stat_guest': goalkeepers_stat_guest,
                 'guest_team': guest_team,
                 'goalkeepers_stat_home_general': goalkeepers_stat_home_general,
                 'goalkeepers_stat_guest_general': goalkeepers_stat_guest_general,
                 'field_players_stat_home_general': field_players_stat_home_general,
                 'field_players_stat_guest_general': field_players_stat_guest_general,
                 }
            )
        elif not date:
            info = 'Не выбрана дата матча'
            return render(
                request, 'stat-match.html',
                {'info': info,
                 'leagues': leagues,
                 'field_players_stat_home': field_players_stat_home,
                 'field_players_stat_guest': field_players_stat_guest,
                 'goalkeepers_stat_home': goalkeepers_stat_home,
                 'goalkeepers_stat_guest': goalkeepers_stat_guest,
                 'guest_team': guest_team,
                 'goalkeepers_stat_home_general': goalkeepers_stat_home_general,
                 'goalkeepers_stat_guest_general': goalkeepers_stat_guest_general,
                 'field_players_stat_home_general': field_players_stat_home_general,
                 'field_players_stat_guest_general': field_players_stat_guest_general,
                 }
            )
        home_team = models.Team.objects.get(name=home_team)
        guest_team = models.Team.objects.get(name=guest_team)
        date = datetime.datetime.strptime(date, "%d/%m/%y").date()
        try:
            match = models.Match.objects.get(home_team=home_team, guest_team=guest_team,
                                             date=date)
        except:
            info = 'Такого матча не существует, или были введены неверные данные'
            return render(
                request, 'stat-match.html',
                {'info': info,
                 'leagues': leagues,
                 'field_players_stat_home': field_players_stat_home,
                 'field_players_stat_guest': field_players_stat_guest,
                 'goalkeepers_stat_home': goalkeepers_stat_home,
                 'goalkeepers_stat_guest': goalkeepers_stat_guest,
                 'home_team': home_team, 'guest_team': guest_team,
                 'goalkeepers_stat_home_general': goalkeepers_stat_home_general,
                 'goalkeepers_stat_guest_general': goalkeepers_stat_guest_general,
                 'field_players_stat_home_general': field_players_stat_home_general,
                 'field_players_stat_guest_general': field_players_stat_guest_general,
                 }
            )
        home_team_players = models.Player.objects.filter(team=home_team)
        home_team_players_ids = []
        for home_team_player in home_team_players:
            home_team_players_ids.append(home_team_player.id)
        if position == 'Вратари':
            goalkeepers_stat_home = []
            goalkeepers_stat_guest = []

            goalkeepers = models.GoalkeeperStat.objects.filter(match_id=match)
            for goalkeeper in goalkeepers:
                if goalkeeper.goalkeeper_id.id in home_team_players_ids:
                    goalkeepers_stat_home.append(goalkeeper)
                else:
                    goalkeepers_stat_guest.append(goalkeeper)
            if not goalkeepers_stat_home:
                info = 'События по вратарям со стороны команды хозяев не фиксировались'
                goalkeepers_stat_home = ''
                if not goalkeepers_stat_guest:
                    info += ' События по вратарям со стороны команды гостей не фиксировались'
                    goalkeepers_stat_guest = ''
            elif not goalkeepers_stat_guest:
                info = 'События по вратарям со стороны команды гостей не фиксировались'
                goalkeepers_stat_guest = ''
            goalkeepers_stat_home_general = {}
            goalkeepers_stat_home_general['dr_plus'] = 0
            goalkeepers_stat_home_general['dr_minus'] = 0
            goalkeepers_stat_home_general['errors'] = 0
            goalkeepers_stat_home_general['saves'] = 0
            goalkeepers_stat_home_general['missed_goals'] = 0
            goalkeepers_stat_home_general['shots_on_target'] = 0
            for goalkeeper_stat in goalkeepers_stat_home:
                goalkeepers_stat_home_general['dr_plus'] += goalkeeper_stat.dr_plus
                goalkeepers_stat_home_general['dr_minus'] += goalkeeper_stat.dr_minus
                goalkeepers_stat_home_general['errors'] += goalkeeper_stat.errors
                goalkeepers_stat_home_general['saves'] += goalkeeper_stat.saves
                goalkeepers_stat_home_general['missed_goals'] += goalkeeper_stat.missed_goals
                goalkeepers_stat_home_general['shots_on_target'] += goalkeeper_stat.shots_on_target
            goalkeepers_stat_guest_general = {}
            goalkeepers_stat_guest_general['dr_plus'] = 0
            goalkeepers_stat_guest_general['dr_minus'] = 0
            goalkeepers_stat_guest_general['errors'] = 0
            goalkeepers_stat_guest_general['saves'] = 0
            goalkeepers_stat_guest_general['missed_goals'] = 0
            goalkeepers_stat_guest_general['shots_on_target'] = 0
            for goalkeeper_stat in goalkeepers_stat_guest:
                goalkeepers_stat_guest_general['dr_plus'] += goalkeeper_stat.dr_plus
                goalkeepers_stat_guest_general['dr_minus'] += goalkeeper_stat.dr_minus
                goalkeepers_stat_guest_general['errors'] += goalkeeper_stat.errors
                goalkeepers_stat_guest_general['saves'] += goalkeeper_stat.saves
                goalkeepers_stat_guest_general['missed_goals'] += goalkeeper_stat.missed_goals
                goalkeepers_stat_guest_general['shots_on_target'] += goalkeeper_stat.shots_on_target
        elif position == 'Полевые':
            field_players_stat_home = []
            field_players_stat_guest = []
            field_players = models.PlayerStat.objects.filter(match_id=match)
            for field_player in field_players:
                if field_player.player_id.id in home_team_players_ids:
                    field_players_stat_home.append(field_player)
                else:
                    field_players_stat_guest.append(field_player)
            if not field_players_stat_home:
                info = 'События по игрокам со стороны команды хозяев не фиксировались'
                field_players_stat_home = ''
                if not field_players_stat_guest:
                    info += ' События по игрокам со стороны команды гостей не фиксировались'
                    field_players_stat_guest = ''
            elif not field_players_stat_guest:
                info = ' События по игрокам со стороны команды гостей не фиксировались'
                field_players_stat_guest = ''
            field_players_stat_home_general = {}
            field_players_stat_home_general['goals'] = 0
            field_players_stat_home_general['passes'] = 0
            field_players_stat_home_general['goal_pass'] = 0
            field_players_stat_home_general['foul_plus'] = 0
            field_players_stat_home_general['foul_minus'] = 0
            field_players_stat_home_general['dr_plus'] = 0
            field_players_stat_home_general['dr_minus'] = 0
            field_players_stat_home_general['lost_ball'] = 0
            field_players_stat_home_general['interceptions'] = 0
            field_players_stat_home_general['in_target'] = 0
            field_players_stat_home_general['out_target'] = 0
            for player_stat in field_players_stat_home:
                field_players_stat_home_general['goals'] += player_stat.goals
                field_players_stat_home_general['passes'] += player_stat.passes
                field_players_stat_home_general['goal_pass'] += player_stat.goals + player_stat.passes
                field_players_stat_home_general['foul_plus'] += player_stat.foul_plus
                field_players_stat_home_general['foul_minus'] += player_stat.foul_minus
                field_players_stat_home_general['dr_plus'] += player_stat.dr_plus
                field_players_stat_home_general['dr_minus'] += player_stat.dr_minus
                field_players_stat_home_general['lost_ball'] += player_stat.lost_ball
                field_players_stat_home_general['interceptions'] += player_stat.interceptions
                field_players_stat_home_general['in_target'] += player_stat.in_target
                field_players_stat_home_general['out_target'] += player_stat.out_target
            field_players_stat_guest_general = {}
            field_players_stat_guest_general['goals'] = 0
            field_players_stat_guest_general['passes'] = 0
            field_players_stat_guest_general['goal_pass'] = 0
            field_players_stat_guest_general['foul_plus'] = 0
            field_players_stat_guest_general['foul_minus'] = 0
            field_players_stat_guest_general['dr_plus'] = 0
            field_players_stat_guest_general['dr_minus'] = 0
            field_players_stat_guest_general['lost_ball'] = 0
            field_players_stat_guest_general['interceptions'] = 0
            field_players_stat_guest_general['in_target'] = 0
            field_players_stat_guest_general['out_target'] = 0
            for player_stat in field_players_stat_guest:
                field_players_stat_guest_general['goals'] += player_stat.goals
                field_players_stat_guest_general['passes'] += player_stat.passes
                field_players_stat_guest_general['goal_pass'] += player_stat.goals + player_stat.passes
                field_players_stat_guest_general['foul_plus'] += player_stat.foul_plus
                field_players_stat_guest_general['foul_minus'] += player_stat.foul_minus
                field_players_stat_guest_general['dr_plus'] += player_stat.dr_plus
                field_players_stat_guest_general['dr_minus'] += player_stat.dr_minus
                field_players_stat_guest_general['lost_ball'] += player_stat.lost_ball
                field_players_stat_guest_general['interceptions'] += player_stat.interceptions
                field_players_stat_guest_general['in_target'] += player_stat.in_target
                field_players_stat_guest_general['out_target'] += player_stat.out_target

    return render(
        request, 'stat-match.html',
        {'info': info,
         'leagues': leagues,
         'field_players_stat_home': field_players_stat_home,
         'field_players_stat_guest': field_players_stat_guest,
         'goalkeepers_stat_home': goalkeepers_stat_home,
         'goalkeepers_stat_guest': goalkeepers_stat_guest,
         'home_team': home_team, 'guest_team': guest_team,
         'goalkeepers_stat_home_general': goalkeepers_stat_home_general,
         'goalkeepers_stat_guest_general': goalkeepers_stat_guest_general,
         'field_players_stat_home_general': field_players_stat_home_general,
         'field_players_stat_guest_general': field_players_stat_guest_general,
         }
    )

@login_required
def general_stat(request):
    teams = models.Team.objects.all()
    field_players_team = []
    field_players_team_sum = []
    goalkeepers_team = []
    goalkeepers_team_sum = []
    for team in teams:
        field_players = models.Player.objects.filter(team=team).exclude(position='Вратарь')
        field_players_stat = models.PlayerStat.objects.all()
        field_players_ids = []
        goals = 0
        passes = 0
        foul_plus = 0
        foul_minus = 0
        dr_plus = 0
        dr_minus = 0
        lost_ball = 0
        interceptions = 0
        in_target = 0
        out_target = 0
        for field_player in field_players:
            field_players_ids.append(field_player.id)
        for field_player_stat in field_players_stat:
            if (field_player_stat.player_id.id in field_players_ids):
                goals += field_player_stat.goals
                passes += field_player_stat.passes
                foul_plus += field_player_stat.foul_plus
                foul_minus += field_player_stat.foul_minus
                dr_plus += field_player_stat.dr_plus
                dr_minus += field_player_stat.dr_minus
                lost_ball += field_player_stat.lost_ball
                interceptions += field_player_stat.interceptions
                in_target += field_player_stat.in_target
                out_target += field_player_stat.out_target
        home_matches = models.Match.objects.filter(home_team=team)
        home_matches_amount = home_matches.aggregate(matches=Count('id'))['matches']
        guest_matches = models.Match.objects.filter(guest_team=team)
        guest_matches_amount = guest_matches.aggregate(matches=Count('id'))['matches']
        team_matches_amount = home_matches_amount + guest_matches_amount
        field_players_team_stat = {}
        field_players_team_stat_sum = {}
        field_players_team_stat['team'] = team.name
        field_players_team_stat_sum['team'] = team.name
        field_players_team_stat_sum['goals'] = goals
        field_players_team_stat_sum['passes'] = passes
        field_players_team_stat_sum['goals_passes'] = goals + passes
        field_players_team_stat_sum['foul_plus'] = foul_plus
        field_players_team_stat_sum['foul_minus'] = foul_minus
        field_players_team_stat_sum['dr_plus'] = dr_plus
        field_players_team_stat_sum['dr_minus'] = dr_minus
        field_players_team_stat_sum['lost_ball'] = lost_ball
        field_players_team_stat_sum['interceptions'] = interceptions
        field_players_team_stat_sum['in_target'] = in_target
        field_players_team_stat_sum['out_target'] = out_target
        if team_matches_amount != 0:
            field_players_team_stat['goals'] = round(goals / team_matches_amount, 2)
            field_players_team_stat['passes'] = round(passes / team_matches_amount, 2)
            field_players_team_stat['goals_passes'] = round((goals + passes) / team_matches_amount, 2)
            field_players_team_stat['foul_plus'] = round(foul_plus / team_matches_amount, 2)
            field_players_team_stat['foul_minus'] = round(foul_minus / team_matches_amount, 2)
            field_players_team_stat['dr_plus'] = round(dr_plus / team_matches_amount, 2)
            field_players_team_stat['dr_minus'] = round(dr_minus / team_matches_amount, 2)
            field_players_team_stat['lost_ball'] = round(lost_ball / team_matches_amount, 2)
            field_players_team_stat['interceptions'] = round(interceptions / team_matches_amount, 2)
            field_players_team_stat['in_target'] = round(in_target / team_matches_amount, 2)
            field_players_team_stat['out_target'] = round(out_target / team_matches_amount, 2)
        else:
            field_players_team_stat['goals'] = round(goals, 2)
            field_players_team_stat['passes'] = round(passes, 2)
            field_players_team_stat['goals_passes'] = round((goals + passes), 2)
            field_players_team_stat['foul_plus'] = round(foul_plus, 2)
            field_players_team_stat['foul_minus'] = round(foul_minus, 2)
            field_players_team_stat['dr_plus'] = round(dr_plus, 2)
            field_players_team_stat['dr_minus'] = round(dr_minus, 2)
            field_players_team_stat['lost_ball'] = round(lost_ball, 2)
            field_players_team_stat['interceptions'] = round(interceptions, 2)
            field_players_team_stat['in_target'] = round(in_target, 2)
            field_players_team_stat['out_target'] = round(out_target, 2)
        field_players_team.append(field_players_team_stat)
        field_players_team_sum.append(field_players_team_stat_sum)

    for team in teams:
        goalkeepers = models.Player.objects.filter(team=team).filter(position='Вратарь')
        goalkeepers_stat = models.GoalkeeperStat.objects.all()
        goalkeepers_ids = []
        goals = 0
        passes = 0
        yellow_cards = 0
        red_cards = 0
        missed_goals = 0
        shots_on_target = 0
        beat_off_shots = 0
        for goalkeeper in goalkeepers:
            goalkeepers_ids.append(goalkeeper.id)
        for goalkeeper_stat in goalkeepers_stat:
            if (goalkeeper_stat.goalkeeper_id.id in goalkeepers_ids):
                goals += goalkeeper_stat.goals
                passes += goalkeeper_stat.passes
                yellow_cards += goalkeeper_stat.yellow_cards
                red_cards += goalkeeper_stat.red_cards
                missed_goals += goalkeeper_stat.missed_goals
                shots_on_target += goalkeeper_stat.shots_on_target
                beat_off_shots += goalkeeper_stat.beat_off_shots
        home_matches = models.Match.objects.filter(home_team=team)
        home_matches_amount = home_matches.aggregate(matches=Count('id'))['matches']
        guest_matches = models.Match.objects.filter(guest_team=team)
        guest_matches_amount = guest_matches.aggregate(matches=Count('id'))['matches']
        team_matches_amount = home_matches_amount + guest_matches_amount
        goalkeepers_team_stat = {}
        goalkeepers_team_stat_sum = {}
        goalkeepers_team_stat['team'] = team.name
        goalkeepers_team_stat_sum['team'] = team.name
        goalkeepers_team_stat_sum['goals'] = goals
        goalkeepers_team_stat_sum['passes'] = passes
        goalkeepers_team_stat_sum['goals_passes'] = (goals + passes)
        goalkeepers_team_stat_sum['yellow_cards'] = yellow_cards
        goalkeepers_team_stat_sum['red_cards'] = red_cards
        goalkeepers_team_stat_sum['missed_goals'] = missed_goals
        goalkeepers_team_stat_sum['shots_on_target'] = shots_on_target
        if (team_matches_amount != 0) and (shots_on_target != 0):
            goalkeepers_team_stat['goals'] = round(goals / team_matches_amount, 2)
            goalkeepers_team_stat['passes'] = round(passes / team_matches_amount, 2)
            goalkeepers_team_stat['goals_passes'] = round((goals + passes) / team_matches_amount, 2)
            goalkeepers_team_stat['yellow_cards'] = round(yellow_cards / team_matches_amount, 2)
            goalkeepers_team_stat['red_cards'] = round(red_cards / team_matches_amount, 2)
            goalkeepers_team_stat['missed_goals'] = round(missed_goals / team_matches_amount, 2)
            goalkeepers_team_stat['shots_on_target'] = round(shots_on_target / team_matches_amount, 2)
            goalkeepers_team_stat['beat_off_shots'] = round((beat_off_shots / shots_on_target) * 100, 2)
            goalkeepers_team_stat_sum['beat_off_shots'] = round((beat_off_shots / shots_on_target) * 100, 2)
        else:
            goalkeepers_team_stat['goals'] = round(goals, 2)
            goalkeepers_team_stat['passes'] = round(passes, 2)
            goalkeepers_team_stat['goals_passes'] = round((goals + passes), 2)
            goalkeepers_team_stat['yellow_cards'] = round(yellow_cards, 2)
            goalkeepers_team_stat['red_cards'] = round(red_cards, 2)
            goalkeepers_team_stat['missed_goals'] = round(missed_goals, 2)
            goalkeepers_team_stat['shots_on_target'] = round(shots_on_target, 2)
            goalkeepers_team_stat['beat_off_shots'] = round((beat_off_shots) * 100, 2)
            goalkeepers_team_stat_sum['beat_off_shots'] = round((beat_off_shots) * 100, 2)
        goalkeepers_team.append(goalkeepers_team_stat)
        goalkeepers_team_sum.append(goalkeepers_team_stat_sum)
    return render(
        request, 'general-stat.html',
        {'field_players_team': field_players_team,
         'goalkeepers_team': goalkeepers_team,
         'field_players_team_sum': field_players_team_sum,
         'goalkeepers_team_sum': goalkeepers_team_sum,
         }
    )

@login_required
def efficiency_stat(request):
    info = ''
    home_team_players = []
    leagues = models.League.objects.all()
    if request.method == 'POST' and request.is_ajax():
        league_id = request.POST.get('selected_league', '')
        curr_league = models.League.objects.get(id=league_id)
        teams = models.Team.objects.filter(league_id=curr_league)
        league_teams = []
        for team in teams:
            league_teams.append(team.name)
        return HttpResponseAjax(teams=league_teams)
    if request.method == 'POST':
        home_team = request.POST.get('home_team', '')
        guest_team = request.POST.get('guest_team', '')
        date = request.POST.get('date', '')
        if not home_team:
            info = 'Не выбрана команда хозяев'
            return render(
                request, 'efficiency-stat.html',
                {
                    'info': info,
                    'leagues': leagues,
                }
            )
        elif not guest_team:
            info = 'Не выбрана команда гостей'
            return render(
                request, 'efficiency-stat.html',
                {
                    'info': info,
                    'leagues': leagues,
                }
            )
        elif not date:
            info = 'Не выбрана дата матча'
            return render(
                request, 'efficiency-stat.html',
                {
                    'info': info,
                    'leagues': leagues,
                }
            )
        home_team = models.Team.objects.get(name=home_team)
        guest_team = models.Team.objects.get(name=guest_team)
        match_date = datetime.datetime.strptime(date, "%d/%m/%y").date()
        try:
            match = models.Match.objects.get(home_team=home_team, guest_team=guest_team,
                                             date=match_date)
        except ObjectDoesNotExist:
            info = 'Такого матча не существует'
            return render(
                request, 'efficiency-stat.html',
                {
                    'info': info,
                    'leagues': leagues,
                }
            )
        players = models.Player.objects.filter(team=home_team).exclude(position='Вратарь')
        time_periods = []

        for player in players:
            player_events_replaced_to = models.MatchEvent.objects.filter(match=match, player=player,
                                                                         event_type='replaced_to_match')
            player_events_replaced_from = models.MatchEvent.objects.filter(match=match, player=player,
                                                                           event_type='replaced_from_match')
            times_replaced_to = set(player_event_replaced_to.event_time
                                    for player_event_replaced_to in player_events_replaced_to)
            times_replaced_from = set(player_event_replaced_from.event_time
                                      for player_event_replaced_from in player_events_replaced_from)
            player_time = {}
            player_time['id'] = str(player.id)
            player_time['name'] = player.__str__()
            player_time['periods'] = []
            while times_replaced_to:
                replaced_to_time = min(times_replaced_to)
                times_replaced_to.remove(replaced_to_time)
                if times_replaced_from:
                    replaced_from_time = min(times_replaced_from)
                    times_replaced_from.remove(replaced_from_time)
                player_time['periods'].append({'replaced_to_time': replaced_to_time,
                                               'replaced_from_time': replaced_from_time})
                time_periods.append({'replaced_to_time': replaced_to_time,
                                     'replaced_from_time': replaced_from_time})
            home_team_players.append(player_time)
        events = models.MatchEvent.objects.filter(match=match)
        match_duration = 0
        for event in events:
            if event.event_time > match_duration:
                match_duration = event.event_time
        min_time = 0
        curr_periods = []
        general_periods = []
        while min_time != match_duration:
            max_time = match_duration

            for period in time_periods:
                if period['replaced_to_time'] <= min_time and period['replaced_from_time'] > min_time:
                    curr_periods.append(period)

            for period in curr_periods:
                if period['replaced_from_time'] < max_time:
                    max_time = period['replaced_from_time']

            if curr_periods:
                general_periods.append({'start': min_time, 'end': max_time})
                min_time = max_time
                curr_periods = []
            else:
                min_time = match_duration

        total_stat = []
        max_num_players = 0
        curr_num_players = 0

        players = []

        for period in general_periods:
            period_stat = {}
            period_stat['period_players'] = []
            period_stat['interval'] = str(period['start']) + '-' + str(period['end'])
            period_stat['goals'] = 0
            period_stat['in_target'] = 0
            period_stat['passes'] = 0
            period_stat['out_target'] = 0
            period_stat['dr_plus'] = 0
            period_stat['dr_minus'] = 0
            period_stat['interceptions'] = 0
            period_stat['lost_balls'] = 0
            period_stat['foul_plus'] = 0
            period_stat['foul_minus'] = 0
            period_stat['goals_and_passes'] = 0
            for home_team_player in home_team_players:
                for play_period in home_team_player['periods']:
                    if play_period['replaced_to_time'] < period['end'] and play_period['replaced_from_time'] > period[
                        'start']:
                        period_stat['period_players'].append(home_team_player['name'])
                        player = models.Player.objects.get(id=home_team_player['id'])
                        curr_num_players += 1

                        if period['start'] == 0:
                            player_events = models.MatchEvent.objects.filter(player=player, match=match,
                                                                             event_time__range=(period['start'],
                                                                                                period['end']))
                        else:
                            player_events = models.MatchEvent.objects.filter(player=player, match=match,
                                                                             event_time__range=(period['start'] + 1,
                                                                                                period['end']))

                        for event in player_events:
                            if event.event_type == 'hit':
                                if event.event_value == 'goal':
                                    period_stat['goals'] += 1
                                    period_stat['in_target'] += 1
                                elif event.event_value == 'pass':
                                    period_stat['passes'] += 1
                                elif event.event_value == 'goal_from_10':
                                    period_stat['goals'] += 1
                                    period_stat['in_target'] += 1
                                elif event.event_value == 'goal_from_6':
                                    period_stat['goals'] += 1
                                    period_stat['in_target'] += 1
                                elif event.event_value == 'no_goal_from_play':
                                    period_stat['out_target'] += 1
                                elif event.event_value == 'no_goal_from_target':
                                    period_stat['in_target'] += 1
                            elif event.event_type == 'dribble_successful':
                                period_stat['dr_plus'] += 1
                            elif event.event_type == 'dribble_unsuccessful':
                                period_stat['dr_minus'] += 1
                            elif event.event_type == 'intercept':
                                period_stat['interceptions'] += 1
                            elif event.event_type == 'lost':
                                period_stat['lost_balls'] += 1
                            elif event.event_type == 'foul_on':
                                period_stat['foul_plus'] += 1
                            elif event.event_type == 'foul_from':
                                period_stat['foul_minus'] += 1
            if max_num_players < curr_num_players:
                max_num_players = curr_num_players
            curr_num_players = 0
                                
            period_stat['goals_and_passes'] = period_stat['goals'] + period_stat['passes']
            stat_to_add = {}

            if total_stat:
                for stat in total_stat:
                    players = []
                    for player in stat['period_players']:
                        players.append(player)
                    players.sort()
                    if period_stat:
                        period_stat['period_players'].sort()
                        if players == period_stat['period_players']:
                            stat['interval'] += '/' + period_stat['interval']
                            stat['goals'] += period_stat['goals']
                            stat['in_target'] += period_stat['in_target']
                            stat['passes'] += period_stat['passes']
                            stat['out_target'] += period_stat['out_target']
                            stat['dr_plus'] += period_stat['dr_plus']
                            stat['dr_minus'] += period_stat['dr_minus']
                            stat['interceptions'] += period_stat['interceptions']
                            stat['lost_balls'] += period_stat['lost_balls']
                            stat['foul_plus'] += period_stat['foul_plus']
                            stat['foul_minus'] += period_stat['foul_minus']
                            stat['goals_and_passes'] += period_stat['goals_and_passes']
                            period_stat = False
                            break

            else:
                period_stat['period_players'].sort()
                total_stat.append(period_stat)
                period_stat = False
            if period_stat:
                period_stat['period_players'].sort()
                total_stat.append(period_stat)


        return render(
            request, 'efficiency-stat.html',
            {'home_team_players': home_team_players,
             'general_periods': general_periods, 'info': info,
             'leagues': leagues,
             'total_stat': total_stat, 'players': players,
             'max_num_players': max_num_players,}
        )

    return render(
        request, 'efficiency-stat.html',
        {
            'leagues': leagues,
            'home_team_players': home_team_players
        }
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def goalkeeper_stat_test(request):
    if request.method == 'POST':
        form = forms.GoalkeeperStatForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = forms.GoalkeeperStatForm()
    return render(
        request, 'goalkeeper_stat_test.html',
        {'form': form,}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def player_stat_test(request):
    if request.method == 'POST':
        form = forms.PlayerStatForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = forms.PlayerStatForm()
    return render(
        request, 'player_stat_test.html',
        {'form': form,}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def match_test(request):
    if request.method == 'POST':
        form = forms.MatchForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = forms.MatchForm()
    return render(
        request, 'match_test.html',
        {'form': form,}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def match_event(request):
    if request.method == 'POST':
        form = forms.EventForm(request.POST)
        if form.is_valid():
            match_date = form.cleaned_data['match_date']
            home_team = form.cleaned_data['home_team']
            guest_team = form.cleaned_data['guest_team']
            player_id = form.cleaned_data['player_id']
            event = form.cleaned_data['event']
            sub_event = form.cleaned_data['sub_event']
            time = form.cleaned_data['time']
            home_goals = form.cleaned_data['home_team_goals']
            guest_goals = form.cleaned_data['guest_team_goals']
            match_date = datetime.datetime.fromtimestamp(timestamp=float(match_date)).date()
            home_team = models.Team.objects.get(id=home_team)
            guest_team = models.Team.objects.get(id=guest_team)
            try:
                match = models.Match.objects.get(home_team=home_team,
                                                 guest_team=guest_team,
                                                 date=match_date)
                match.home_team_goals = home_goals
                match.guest_team_goals = guest_goals
            except ObjectDoesNotExist:
                match = models.Match.objects.create(home_team=home_team,
                                                    guest_team=guest_team,
                                                    date=match_date,
                                                    home_team_goals=home_goals,
                                                    guest_team_goals=guest_goals)
            match.save()

            player = models.Player.objects.get(id=player_id)
            match_event = models.MatchEvent.objects.create(match=match, player=player,
                                                               event_type=event,
                                                               event_value=sub_event,
                                                               event_time=time)
            match_event.save()
            if player.position == 'Вратарь':
                try:
                    goalkeeper_stat = models.GoalkeeperStat.objects.get(goalkeeper_id=player,
                                                                            match_id=match)
                except ObjectDoesNotExist:
                    goalkeeper_stat = models.GoalkeeperStat.objects.create(goalkeeper_id=player,
                                                                            match_id=match,
                                                                            goals=0, passes=0,
                                                                            missed_goals=0,
                                                                            yellow_cards=0,
                                                                            red_cards=0, mins=0,
                                                                            shots_on_target=0,
                                                                            beat_off_shots=0,
                                                                            dr_plus=0, dr_minus=0,
                                                                            errors=0, saves=0,
                                                                            min_in=0, min_out=0)
                if match_event.event_type == 'result':
                    if match_event.event_value == 'goal':
                        goalkeeper_stat.goals += 1
                    elif match_event.event_value == 'pass':
                        goalkeeper_stat.passes += 1
                elif match_event.event_type == 'dribble_successful':
                    goalkeeper_stat.dr_plus += 1
                elif match_event.event_type == 'dribble_unsuccessful':
                        goalkeeper_stat.dr_minus += 1
                elif match_event.event_type == 'parried':
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.beat_off_shots += 1
                elif match_event.event_type == 'goal':
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.missed_goals += 1
                elif match_event.event_type == 'mistake':
                    goalkeeper_stat.errors += 1
                    if match_event.event_value == 'goal':
                        goalkeeper_stat.missed_goals += 1
                        goalkeeper_stat.shots_on_target += 1
                    elif match_event.event_value == 'yellow_card':
                        goalkeeper_stat.yellow_cards += 1
                    elif match_event.event_value == 'red_card':
                        goalkeeper_stat.red_cards += 1
                elif match_event.event_type == 'save':
                    goalkeeper_stat.saves += 1
                    goalkeeper_stat.shots_on_target += 1
                    goalkeeper_stat.beat_off_shots += 1
                elif match_event.event_type == 'replaced_to_match':
                    goalkeeper_stat.min_in = match_event.event_time
                elif match_event.event_type == 'replaced_from_match':
                    goalkeeper_stat.min_out = match_event.event_time
                    goalkeeper_stat.mins += goalkeeper_stat.min_out - goalkeeper_stat.min_in
                goalkeeper_stat.save()


            else:
                try:
                    player_stat = models.PlayerStat.objects.get(player_id=player,
                                                                match_id=match)
                except:
                    player_stat = models.PlayerStat.objects.create(player_id=player, match_id=match,
                                                                    goals=0, passes=0, yellow_cards=0,
                                                                    red_cards=0, mins=0, foul_plus=0,
                                                                    foul_minus=0, dr_plus=0, dr_minus=0,
                                                                    lost_ball=0, interceptions=0,
                                                                    in_target=0, out_target=0,
                                                                    min_in=0, min_out=0)
                if match_event.event_type == 'hit':
                    if match_event.event_value == 'goal':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'pass':
                        player_stat.passes += 1
                    elif match_event.event_value == 'goal_from_10':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'goal_from_6':
                        player_stat.goals += 1
                        player_stat.in_target += 1
                    elif match_event.event_value == 'no_goal_from_play':
                        player_stat.out_target += 1
                    elif match_event.event_value == 'no_goal_from_target':
                        player_stat.in_target += 1
                elif match_event.event_type == 'dribble_successful':
                    player_stat.dr_plus += 1
                elif match_event.event_type == 'dribble_unsuccessful':
                    player_stat.dr_minus += 1
                elif match_event.event_type == 'intercept':
                    player_stat.interceptions += 1
                elif match_event.event_type == 'lost':
                    player_stat.lost_ball += 1
                elif match_event.event_type == 'foul_on':
                    player_stat.foul_plus += 1
                elif match_event.event_type == 'foul_from':
                    player_stat.foul_minus += 1
                    if match_event.event_value == 'yellow_card':
                        player_stat.yellow_cards += 1
                    elif match_event.event_value == 'red_card':
                        player_stat.red_cards += 1
                elif match_event.event_type == 'replaced_to_match':
                    player_stat.min_in = match_event.event_time
                elif match_event.event_type == 'replaced_from_match':
                    player_stat.min_out = match_event.event_time
                    player_stat.mins += player_stat.min_out - player_stat.min_in
                player_stat.save()
    else:
        form = forms.EventForm()
    return render(
        request, 'match_event.html',
        {'form': form}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def user_add(request):
    info = ''
    if request.method == 'POST':
        form = forms.UserForm(request.POST)
        if form.is_valid():
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            users = models.User.objects.all()
            for user in users:
                if user.username == login:
                    info = 'Пользователь с таким логином уже существует'
                    return render(
                        request, 'user-add.html',
                        {'form': form, 'info': info}
                    )
            user = models.User.objects.create_user(username=login, first_name=first_name,
                                              last_name=last_name, phone_number=phone,
                                              email=email, password=password, role=role)
            user.save()
            info = 'Новый пользователь был успешно создан!'
            stat_permission = Permission.objects.filter(name='Can view stats')[:1].get()
            info_permission = Permission.objects.filter(name='Can edit info')[:1].get()
            user_permission = Permission.objects.filter(name='Can edit users')[:1].get()
            if role == 'admin':
                user.user_permissions.add(stat_permission, info_permission, user_permission)
                user.save()
                admin = models.Admin.objects.create(user=user)
                admin.save()
            elif role == 'manager':
                user.user_permissions.add(stat_permission, info_permission)
                user.save()
                manager = models.Manager.objects.create(user=user)
                manager.save()
            else:
                user.user_permissions.add(stat_permission)
                user.save()
                simple_user = models.SimpleUser.objects.create(user=user)
                simple_user.save()

    else:
        form = forms.UserForm()

    return render(
        request, 'user-add.html',
        {'form': form, 'info': info}
    )

def login_view(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    if not (username and password):
        return render(request, 'login.html')
    user = authenticate(username=username, password=password)
    if not user:
        return render(request, 'login.html', {'info': username + password})
    login(request, user)
    return redirect('/')

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
@permission_required('mediasportmobile.can_edit_users')
def user_list(request):
    users = models.User.objects.all()
    return render(
        request, 'users.html',
        {'users': users}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def edit_user(request, pk):
    info = ''
    users = models.User.objects.all()
    try:
        user = models.User.objects.get(id=pk)
    except ObjectDoesNotExist:
        return render(
            request, 'users.html',
            {'users': users}
        )
    if request.method == 'POST':
        form = forms.EditUserForm(request.POST, instance=user)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            role = form.cleaned_data['user_role']
            for curr_user in users:
                if curr_user.username == username and curr_user != user:
                    info = 'Пользователь с таким логином уже существует'
                    return render(
                        request, 'edit-user.html',
                        {'form': form, 'info': info, 'pk': pk}
                    )
            if user.role != role:
                user.role = role
                stat_permission = Permission.objects.filter(name='Can view stats')[:1].get()
                info_permission = Permission.objects.filter(name='Can edit info')[:1].get()
                user_permission = Permission.objects.filter(name='Can edit users')[:1].get()
                if role == 'admin':
                    user.user_permissions.clear()
                    user.user_permissions.add(stat_permission, info_permission, user_permission)
                elif role == 'manager':
                    user.user_permissions.clear()
                    user.user_permissions.add(stat_permission, info_permission)
                else:
                    user.user_permissions.clear()
                    user.user_permissions.add(stat_permission)
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = phone
            user.email = email
            user.username = username
            user.save()
            info = 'Изменения успешно сохранены!'
        else:
            info = 'Что-то пошло не так...'
    else:
        form = forms.EditUserForm(instance=user)
    return render(
        request, 'edit-user.html',
        {'form': form, 'info': info, 'pk': pk}
    )

@login_required
@permission_required('mediasportmobile.can_edit_users')
def delete_user(request, pk):

    try:
        user = models.User.objects.get(id=pk)
        user.delete()
        users = models.User.objects.all()
    except ObjectDoesNotExist:
        info=''
    users = models.User.objects.all()
    return render(
        request, 'users.html',
        {'users': users}
    )

@login_required
def user_profile(request):
    user = request.user
    info = ''
    bad_info = ''
    if request.method == 'POST':
        password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        password_confirmation = request.POST.get('password_confirmation')


        if (not new_password) or (not password_confirmation) or (new_password != password_confirmation):
            info = ''
            bad_info = 'Одно из полей не было заполнено или новые пароли не совпадают'

        elif user.check_password(password):
            username = user.username
            user.set_password(new_password)
            user.save()
            user = authenticate(username=username, password=new_password)
            login(request, user)
            info = 'Изменения были успешно сохранены!'
            bad_info = ''
        else:
            info = ''
            bad_info = 'Введен неверный пароль'

    return render(
        request, 'user-profile.html',
        {'user': user, 'info': info, 'bad_info': bad_info},
        RequestContext(request, {})
    )

@login_required
def user_edit_profile(request):
    user = request.user
    info = ''
    bad_info = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        user.username = (username or user.username)
        user.first_name = (first_name or user.first_name)
        user.last_name = (last_name or user.last_name)
        user.phone_number = (phone_number or user.phone_number)
        user.email = (email or user.email)
        user.save()
        return redirect('/user_profile/')
		
    return render(
        request, 'user-profile.html',
        {'user': user, 'info': info, 'bad_info': bad_info},
        RequestContext(request, {})
    )

@login_required
def home_page(request):
    leagues = models.League.objects.all()
    leagues_stat = []
    for league in leagues:
        cur_league = {}
        cur_league['name'] = league.name
        cur_league['goals'] = 0
        teams = models.Team.objects.filter(league_id=league)
        for team in teams:
            players = models.Player.objects.filter(team=team)
            for player in players:
                player_stat = models.PlayerStat.objects.filter(player_id=player)
                for stat in player_stat:
                    cur_league['goals'] += stat.goals
                goalkeeper_stat = models.GoalkeeperStat.objects.filter(goalkeeper_id=player)
                for stat in goalkeeper_stat:
                    cur_league['goals'] += stat.goals
        leagues_stat.append(cur_league)
    return render(
        request, 'index.html',
        {'leagues': leagues_stat}
    )

@login_required
def all_matches(request):
    matches_to_show = []
    if request.method == 'POST':
        form = forms.LeagueForm(request.POST)
        if form.is_valid():
            teams = models.Team.objects.filter(league_id=form.cleaned_data['league'])

            curr_match = {}
            matches = models.Match.objects.all()
            for match in matches:
                if (match.home_team in teams) or (match.guest_team in teams):
                    curr_match['home_team'] = match.home_team
                    curr_match['guest_team'] = match.guest_team
                    curr_match['home_team_goals'] = match.home_team_goals
                    curr_match['guest_team_goals'] = match.guest_team_goals
                    curr_match['date'] = match.date
                    matches_to_show.append(curr_match)
                    curr_match = {}

    else:
        form = forms.LeagueForm()
    return render(
        request, 'all-matches.html',
        {'form': form, 'matches': matches_to_show}
    )

class HttpResponseAjax(HttpResponse):
    def __init__(self, status='ok', **kwargs):
        kwargs['status'] = status
        super(HttpResponseAjax, self).__init__(
            content=json.dumps(kwargs),
            content_type='application/json',
        )

class HttpResponseAjaxError(HttpResponseAjax):
    def __init__(self, code, message):
        super(HttpResponseAjaxError, self).__init__(
            status='error',
            code=code,
            message=message,
        )