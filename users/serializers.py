from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User, AccessCode, StaffNote

from datetime import date

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    access_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['phone', 'password', 'access_code']

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Пользователь с таким номером телефона уже существует")
        return value

    def validate_access_code(self, value):
        active = AccessCode.get_active()
        if not active or active.code != value:
            raise serializers.ValidationError('Неверный код доступа')
        return value

    def create(self, validated_data):
        validated_data.pop('access_code')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            phone=attrs['phone'], 
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError("Неверный номер телефона или пароль")
        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):

    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone', 'role', 'first_name', 'last_name', 'full_name',
            'birth_date', 'age', 'photo', 'medical_notes']
        read_only_fields = ['role', 'id', 'age', 'full_name']

    def get_age(self, obj):
        if not obj.birth_date:
            return None
        today = date.today()
        return today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

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
    birth_date = serializers.DateField(required=False, allow_null=True)
    medical_notes = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ['phone', 'password', 'birth_date', 'medical_notes', 'first_name', 'last_name']

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Пользователь с таким номером телефона уже существует")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data, role=User.Role.CLIENT)


class StaffNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffNote
        fields = ['id', 'client', 'text', 'created_at']
        read_only_fields = fields

    def get_author_name(self, obj):
        if not obj.author:
            return None
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.phone


class StaffNoteCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)

    def create(self, validated_data):
        return StaffNote.objects.create(text=validated_data['text'], client=self.context['client'], author=self.context['request'].user)