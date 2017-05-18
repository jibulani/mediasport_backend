from rest_framework import serializers
from . import models

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = ('id', 'home_team', 'guest_team',
                  'date', 'home_team_goals', 'guest_team_goals')

class EventSerializer(serializers.Serializer):
    # team_host = serializers.CharField(max_length=255)
    # team_guest = serializers.CharField(max_length=255)
    # date = serializers.IntegerField()
    # home_goals = serializers.IntegerField()
    # guest_goals = serializers.IntegerField()
    # event = serializers.CharField(max_length=50)
    # sub_event = serializers.CharField(max_length=50)
    # player = serializers.IntegerField()
    # time = serializers.IntegerField()
    # team = serializers.CharField(max_length=255)
    match_info = serializers.JSONField()
    stats = serializers.ListField()

class DataSerializer(serializers.Serializer):
    league_data = serializers.JSONField()