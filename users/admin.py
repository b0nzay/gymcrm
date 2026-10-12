from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group

from .models import User
from .nicknames import LOGIN_ERROR, normalize_username


admin.site.site_header = 'GymCRM'
admin.site.site_title = 'GymCRM'
admin.site.index_title = 'Аварийный доступ к данным'

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повтор пароля', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'role', 'first_name', 'last_name')

    def clean_username(self):
        try:
            return normalize_username(self.cleaned_data.get('username'))
        except ValueError:
            raise forms.ValidationError(LOGIN_ERROR)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label='Пароль',
        help_text=(
            'Пароль хранится в виде хеша. Сменить его можно '
            '<a href="../password/">этой формой</a>.'
        ),
    )

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = (
        'username',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined')
    actions = []

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Профиль', {
            'fields': (
                'first_name',
                'last_name',
            ),
        }),
        ('Роль в зале', {'fields': ('role',)}),
        ('Доступ в /admin/', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'role',
                'first_name',
                'last_name',
            ),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('username',)
        return self.readonly_fields
