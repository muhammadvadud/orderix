from rest_framework import serializers
from accounts.models import Account


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'phone_number', 'role', 'restaurant', 'created_at')


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'phone_number', 'role', 'restaurant', 'tg_id', 'created_at')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = ('id', 'username', 'phone_number', 'role', 'restaurant', 'tg_id', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Account(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('username', 'phone_number', 'role', 'tg_id')
