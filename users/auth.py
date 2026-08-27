from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Embeds role and superuser status in the access token so the frontend
    can gate navigation/permissions without an extra round-trip.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        token['user_id'] = user.id
        token['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        return token


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer
