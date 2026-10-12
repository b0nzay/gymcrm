from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User, AccessCode, StaffNote, ActivityLog
from .nicknames import normalize_username


def _unique_username(value, instance=None):
    try:
        value = normalize_username(value)
    except ValueError as e:
        raise serializers.ValidationError(str(e))
    qs = User.objects.filter(username=value)
    if instance:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise serializers.ValidationError('Пользователь с таким логином уже существует')
    return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    access_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'access_code']

    def validate_username(self, value):
        return _unique_username(value)

    def validate_access_code(self, value):
        active = AccessCode.get_active()
        if not active or active.code != value:
            raise serializers.ValidationError('Неверный код доступа')
        return value

    def create(self, validated_data):
        validated_data.pop('access_code')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            username = normalize_username(attrs['username'])
        except ValueError:
            raise serializers.ValidationError('Неверный логин или пароль')
        user = authenticate(
            username=username,
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError('Неверный логин или пароль')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'first_name', 'last_name', 'full_name', 'password']
        read_only_fields = ['role', 'id', 'full_name', 'username']

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None) or None
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class AccessCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessCode
        fields = ['code', 'is_active', 'created_at']
        read_only_fields = fields


class AccessCodeRotateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8, required=False, allow_blank=False)

    def validate_code(self, value):
        if AccessCode.objects.filter(code=value).exists():
            raise serializers.ValidationError('Такой код уже был')
        return value

    def save(self, **kwargs):
        new_code = self.validated_data.get('code')
        return AccessCode.rotate(new_code=new_code)


class ClientCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    last_name = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name']

    def validate_username(self, value):
        return _unique_username(value)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data, role=User.Role.CLIENT)


class StaffNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffNote
        fields = ['id', 'client', 'text', 'created_at', 'author_name']
        read_only_fields = fields

    def get_author_name(self, obj):
        if not obj.author:
            return None
        return obj.author.display_name


class StaffNoteCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)

    def create(self, validated_data):
        return StaffNote.objects.create(text=validated_data['text'], client=self.context['client'], author=self.context['request'].user)


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'role', 'first_name', 'last_name', 'full_name',
            'is_active',
        ]
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.display_name

    def validate_role(self, value):
        if value not in (User.Role.CLIENT, User.Role.TRAINER):
            raise serializers.ValidationError('Допустимы только роли client или trainer')
        return value

    def validate(self, attrs):
        if self.instance and self.instance.role == User.Role.ADMIN:
            raise serializers.ValidationError('Нельзя изменять администратора')
        return attrs


class TrainerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name']
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.display_name


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'description', 'created_at', 'actor', 'actor_name']
        read_only_fields = fields

    def get_actor_name(self, obj):
        if not obj.actor:
            return None
        return obj.actor.display_name
