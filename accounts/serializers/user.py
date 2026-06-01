import re

from rest_framework import serializers
from accounts.models import Account, UserRoleChoices


class RoleAssignmentMixin:
    """Faqat admin 'admin' rolini biriktira oladi; manager qila olmaydi.
    Manager faqat o'zining restoraniga xodim qo'sha oladi."""

    def validate_phone_number(self, value):
        # '+' va bo'shliqlarni tashlab, faqat O'zbekiston formatini qabul qilamiz: 998 + 9 raqam
        cleaned = re.sub(r'[\s+]', '', value or '')
        if not re.fullmatch(r'998\d{9}', cleaned):
            raise serializers.ValidationError(
                "Telefon raqami noto'g'ri. Format: 998 va 9 ta raqam (masalan 998901234567)."
            )
        return cleaned

    def validate_role(self, value):
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if value == UserRoleChoices.ADMIN and getattr(actor, 'role', None) != UserRoleChoices.ADMIN:
            raise serializers.ValidationError("Sizda admin rolini biriktirish huquqi yo'q.")
        return value

    def validate_restaurant(self, value):
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if getattr(actor, 'role', None) == UserRoleChoices.ADMIN:
            return value
        if value is not None and value != getattr(actor, 'restaurant', None):
            raise serializers.ValidationError(
                "Siz faqat o'z restoraningizga xodim qo'sha olasiz."
            )
        return value


class UserListSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(read_only=True)

    class Meta:
        model = Account
        fields = ('id', 'username', 'full_name', 'avatar', 'color', 'phone_number',
                  'role', 'restaurant', 'created_at')


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(read_only=True)

    class Meta:
        model = Account
        fields = ('id', 'username', 'full_name', 'avatar', 'color', 'phone_number',
                  'role', 'restaurant', 'tg_id', 'created_at')


class UserCreateSerializer(RoleAssignmentMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = ('id', 'username', 'full_name', 'color', 'phone_number',
                  'role', 'restaurant', 'tg_id', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Account(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(RoleAssignmentMixin, serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('username', 'full_name', 'color', 'phone_number', 'role', 'tg_id')
