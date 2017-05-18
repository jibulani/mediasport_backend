from django.db import models
from django.conf import settings
import uuid
from django.contrib.auth.models import AbstractUser
# from django.conf.auth.models import User

# Create your models here.
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    role = models.CharField(max_length=20)


class SimpleUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='simple_user')

    class Meta:
        permissions = (
            ('can_view_stats', 'Can view stats'),
        )

class Manager(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='manager')

    class Meta:
        permissions = (
            ('can_view_stats', 'Can view stats'),
            ('can_edit_info', 'Can edit info'),
        )

class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='admin')

    class Meta:
        permissions = (
            ('can_view_stats', 'Can view stats'),
            ('can_edit_info', 'Can edit info'),
            ('can_edit_users', 'Can edit users'),
        )

class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'leagues'

    def __str__(self):
        return self.name

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league_id = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    e_mail = models.EmailField()

    class Meta:
        db_table = 'teams'

    def __str__(self):
        return self.name

class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=20, null=True)
    first_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=20, null=True)
    position = models.CharField(max_length=20)
    number = models.IntegerField()

    class Meta:
        db_table = 'players'

    def __str__(self):
        if self.middle_name:
            return self.last_name + ' ' + self.first_name[0] + '.' + self.middle_name[0] + '.'
        else:
            return self.last_name + ' ' + self.first_name[0] + '.'

# class Agent(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     team = models.ForeignKey(Team, on_delete=models.CASCADE)
#     middle_name = models.CharField(max_length=15)
#     first_name = models.CharField(max_length=15)
#     last_name = models.CharField(max_length=15)
#     phone = models.IntegerField()
#     e_mail = models.EmailField()
#
#     class Meta:
#         db_table = 'agents'
#
#     def __str__(self):
#         return self.middle_name + ' ' + self.first_name[0] + '.' + self.last_name[0] + '.'

class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_team')
    guest_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='guest_team')
    date = models.DateField()
    home_team_goals = models.IntegerField()
    guest_team_goals = models.IntegerField()

    class Meta:
        db_table = 'matches'

    def __str__(self):
        return self.home_team.name + ' - ' + self.guest_team.name

class MatchEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=25)
    event_value = models.CharField(max_length=25, null=True)
    event_time = models.IntegerField()

    class Meta:
        db_table = 'events'

    # def __str__(self):
    #     return self.event_type + ' ' + self.player

class PlayerStat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_id = models.ForeignKey(Player, on_delete=models.CASCADE)
    match_id = models.ForeignKey(Match, on_delete=models.CASCADE)
    goals = models.IntegerField()
    passes = models.IntegerField()
    yellow_cards = models.IntegerField()
    red_cards = models.IntegerField()
    mins = models.IntegerField()
    foul_plus = models.IntegerField()
    foul_minus = models.IntegerField()
    dr_plus = models.IntegerField()
    dr_minus = models.IntegerField()
    lost_ball = models.IntegerField()
    interceptions = models.IntegerField()
    in_target = models.IntegerField()
    out_target = models.IntegerField()
    min_in = models.IntegerField(null=True)
    min_out = models.IntegerField(null=True)

    class Meta:
        db_table = 'player_stat'

    def min_per_goal(self):
        if self.goals != 0:
            return round(self.mins/self.goals, 1)
        else:
            return 'Нет забитых голов'

    def goals_passes(self):
        return self.goals + self.passes

    def position(self):
        # player = Player.objects.get(id=self.player_id.id)
        return self.player_id.position

class GoalkeeperStat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goalkeeper_id = models.ForeignKey(Player, on_delete=models.CASCADE)
    match_id = models.ForeignKey(Match, on_delete=models.CASCADE)
    goals = models.IntegerField()
    passes = models.IntegerField()
    missed_goals = models.IntegerField()
    yellow_cards = models.IntegerField()
    red_cards = models.IntegerField()
    mins = models.IntegerField()
    shots_on_target = models.IntegerField()
    beat_off_shots = models.IntegerField()
    dr_plus = models.IntegerField()
    dr_minus = models.IntegerField()
    errors = models.IntegerField()
    saves = models.IntegerField()
    min_in = models.IntegerField(null=True)
    min_out = models.IntegerField(null=True)

    class Meta:
        db_table = 'goalkeeper_stat'

    def beaten_percentage(self):
        if self.shots_on_target != 0:
            return round(self.beat_off_shots/self.shots_on_target*100, 2)
        else:
            return round(100, 2)
    # def stat_sum(self):
    #     general_stat = {}
    #     goalkeeper_stat = self.filter(goalkeeper_id=self.goalkeeper_id)
    #     player = Player.objects.get(id=self.goalkeeper_id)
    #     general_stat['name'] = player.__str__()
    #     goals = goalkeeper_stat.annotate(stat_goals=models.Sum('goals'))
    #     general_stat['goals'] = goals[0].stat_goals
    #     passes = goalkeeper_stat.annotate(stat_passes=models.Sum('passes'))
    #     general_stat['passes'] = passes[0].stat_passes
    #     general_stat['goal_pass'] = goals[0].stat_goals + passes[0].stat_passes
    #     missed_goals = goalkeeper_stat.annotate(stat_missed_goals=models.Sum('missed_goals'))
    #     general_stat['missed_goals'] = missed_goals[0].stat_missed_goals
    #     yellow_cards = goalkeeper_stat.annotate(y_cards=models.Sum('yellow_cards'))
    #     general_stat['yellow_cards'] = yellow_cards[0].y_cards
    #     red_cards = goalkeeper_stat.annotate(r_cards=models.Sum('red_cards'))
    #     general_stat['red_cards'] = red_cards[0].r_cards
    #     games = goalkeeper_stat.annotate(stat_games=models.Count('match_id'))
    #     general_stat['games'] = games[0].stat_games
    #     mins = goalkeeper_stat.annotate(stat_mins=models.Sum('mins'))
    #     general_stat['mins'] = mins[0].stat_mins
    #     general_stat['min_missed'] = mins[0].stat_mins / missed_goals[0].stat_missed_goals
    #     return general_stat


# class MatchProtocol(models.Model):
#     match = models.ForeignKey(Match, on_delete=models.CASCADE)
#     team = models.ForeignKey(Team)
#     player = models.ForeignKey(Player)
#     goal = models.CharField(max_length=30)
#     yellow_card = models.CharField(max_length=15)
#     red_card = models.CharField(max_length=15)
#
#     class Meta:
#         db_table = 'protocols'