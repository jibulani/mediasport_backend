from django import forms
from . import models

class PlayerStatForm(forms.Form):
    team = forms.ModelChoiceField(queryset=models.Team.objects.all(), empty_label='Выберите команду',
                                  label='', widget=forms.Select(attrs={'class': 'form-control input-sm',
                                                                       'style': 'width: inherit'}))

class MatchStatForm(forms.Form):
    home_team = forms.ModelChoiceField(queryset=models.Team.objects.all(), empty_label='Хозяева',
                                       label='')
    guest_team = forms.ModelChoiceField(queryset=models.Team.objects.all(), empty_label='Гости',
                                        label='')
    date = forms.DateField(label='',)
    position = forms.ChoiceField(choices=(('goalkeepers', 'Вратари'),
                                          ('field_players', 'Полевые')),
                                 widget=forms.Select(), required=True, label='')

class GoalkeeperStatForm(forms.ModelForm):
    # goalkeeper_id = forms.ModelChoiceField(queryset=models.Player.objects.filter(position='Вратарь'))
    # match_id = forms.ModelChoiceField(queryset=models.Match.objects.all())
    # goals = forms.IntegerField()
    # passes = forms.IntegerField()
    # missed_goals = forms.IntegerField()
    # yellow_cards = forms.IntegerField()
    # red_cards = forms.IntegerField()
    # mins= forms.IntegerField()
    # shots_on_target= forms.IntegerField()
    # beat_off_shots = forms.IntegerField()
    # dr_plus = forms.IntegerField()
    # dr_minus = forms.IntegerField()
    # errors = forms.IntegerField()
    # saves = forms.IntegerField()
    class Meta:
        model = models.GoalkeeperStat
        fields = ('goalkeeper_id', 'match_id', 'goals', 'passes', 'missed_goals', 'yellow_cards',
                  'red_cards', 'mins', 'shots_on_target', 'beat_off_shots', 'dr_plus', 'dr_minus',
                  'errors', 'saves')

class PlayerStatFormTest(forms.ModelForm):
    class Meta:
        model = models.PlayerStat
        fields = ('player_id', 'match_id', 'goals', 'passes', 'yellow_cards', 'red_cards', 'mins',
                  'foul_plus', 'foul_minus', 'dr_plus', 'dr_minus', 'lost_ball', 'interceptions',
                  'in_target', 'out_target', 'min_in', 'min_out')

class MatchForm(forms.ModelForm):
    class Meta:
        model = models.Match
        fields = ('home_team', 'guest_team', 'date', 'home_team_goals', 'guest_team_goals')

# class TeamForm(forms.ModelForm):
#     class Meta:
#         model = models.Match
#         fields = ('league_id', 'name')

class EventForm(forms.Form):
    match_date = forms.CharField(max_length=50)
    home_team = forms.CharField(max_length=50)
    guest_team = forms.CharField(max_length=50)
    player_id = forms.CharField(max_length=50)
    event = forms.CharField(max_length=50)
    sub_event = forms.CharField(max_length=50)
    time = forms.IntegerField()
    home_team_goals = forms.IntegerField()
    guest_team_goals = forms.IntegerField()

class EfficiencyStatForm(forms.Form):
    home_team = forms.ModelChoiceField(queryset=models.Team.objects.all(), empty_label='Хозяева',
                                       label='')
    guest_team = forms.ModelChoiceField(queryset=models.Team.objects.all(), empty_label='Гости',
                                        label='')
    match_date = forms.DateField(label='',)

    class Meta:
        widgets = {
            'match_date': forms.DateInput(format=('%d-%m-%Y'),
                                          attrs={'placeholder': 'Select a date'})
        }

class UserForm(forms.Form):
    login = forms.CharField(max_length=15, label='Логин', widget=forms.TextInput(attrs={'class': 'form-control',}))
    password = forms.CharField(max_length=15, label='Пароль', widget=forms.TextInput(attrs={'class': 'form-control',}))
    first_name = forms.CharField(max_length=20, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control',}))
    last_name = forms.CharField(max_length=20, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control',}))
    phone = forms.CharField(max_length=15, label='Телефон', widget=forms.TextInput(attrs={'class': 'form-control',}))
    email = forms.EmailField(label='Почта', widget=forms.TextInput(attrs={'class': 'form-control',}))
    role = forms.ChoiceField(choices=(('admin', 'Администратор'),
                                      ('manager', 'Менеджер'),
                                      ('simple_user', 'Пользователь')),
                             widget=forms.Select(attrs={'class': 'form-control',}), required=True, label='Роль')

class EditUserForm(forms.ModelForm):
    username = forms.CharField(max_length=15, label='Логин', widget=forms.TextInput(attrs={'class': 'form-control',}))
    first_name = forms.CharField(max_length=20, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control',}))
    last_name = forms.CharField(max_length=20, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control',}))
    phone_number = forms.CharField(max_length=15, label='Телефон', widget=forms.TextInput(attrs={'class': 'form-control',}))
    email = forms.EmailField(label='Почта', widget=forms.TextInput(attrs={'class': 'form-control',}))
    user_role = forms.ChoiceField(choices=(('admin', 'Администратор'),
                                      ('manager', 'Менеджер'),
                                      ('simple_user', 'Пользователь')),
                             widget=forms.Select(attrs={'class': 'form-control',}), required=True, label='Роль')
    class Meta:
        model = models.User
        fields = ('username', 'first_name', 'last_name', 'phone_number', 'email', 'user_role')

class EditUserProfile(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('username', 'first_name', 'last_name', 'phone_number', 'email')

class LeagueForm(forms.Form):
    league = forms.ModelChoiceField(queryset=models.League.objects.all(), empty_label='Лига', label='',
                                    widget=forms.Select(attrs={'class': 'form-control input-sm',
                                                               'style': 'width: inherit'}))