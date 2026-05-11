"""
users/serializers.py

Serializers for the User model and JWT customization.

Serializers
───────────
  CustomTokenObtainPairSerializer — Injects role flags into JWT payload.
  UserSerializer                  — Read-only profile representation.
  UserRegistrationSerializer      — Write: create student or lecturer accounts.
  UserProfileUpdateSerializer     — Write: update phone / names (partial).
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# JWT — Custom token payload
# ─────────────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default SimpleJWT serializer to inject custom claims
    directly into the access token payload so clients can make role-based
    routing decisions without an extra /me/ round-trip.

    Referenced in settings.py:
        SIMPLE_JWT["TOKEN_OBTAIN_SERIALIZER"]
    """

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)

        # ── Custom claims ─────────────────────────────────────────────────────
        token["username"]    = user.username
        token["email"]       = user.email
        token["full_name"]   = user.get_full_name()
        token["is_student"]  = user.is_student
        token["is_lecturer"] = user.is_lecturer
        token["role"]        = user.role
        # ─────────────────────────────────────────────────────────────────────

        return token

    def validate(self, attrs):
        """Augment the standard token response with a 'user' profile block."""
        data = super().validate(attrs)

        # Append user profile to the login response body
        data["user"] = UserSerializer(self.user).data
        return data


# ─────────────────────────────────────────────────────────────────────────────
# USER — Read
# ─────────────────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a User.
    Used in: JWT login response, /api/users/me/, attendance records.
    """

    role = serializers.CharField(source="role", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_student",
            "is_lecturer",
            "matric_number",
            "staff_id",
            "phone",
            "date_joined",
        ]
        read_only_fields = fields  # This serializer is purely for reading

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.username


# ─────────────────────────────────────────────────────────────────────────────
# USER — Registration (Write)
# ─────────────────────────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Creates a new User account.

    Rules
    ─────
    • Password is validated against Django's AUTH_PASSWORD_VALIDATORS.
    • Exactly one of is_student / is_lecturer must be True.
    • matric_number required when is_student=True.
    • staff_id required when is_lecturer=True.
    • Password is never returned in the response.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "is_student",
            "is_lecturer",
            "matric_number",
            "staff_id",
            "phone",
        ]

    # ── Cross-field validation ─────────────────────────────────────────────

    def validate(self, attrs: dict) -> dict:
        # 1. Passwords must match
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        # 2. At least one role flag must be True
        if not attrs.get("is_student") and not attrs.get("is_lecturer"):
            raise serializers.ValidationError(
                {"role": "Account must be assigned as either a Student or a Lecturer."}
            )

        # 3. Students must supply a matric_number
        if attrs.get("is_student") and not attrs.get("matric_number"):
            raise serializers.ValidationError(
                {"matric_number": "Matric number is required for student accounts."}
            )

        # 4. Lecturers must supply a staff_id
        if attrs.get("is_lecturer") and not attrs.get("staff_id"):
            raise serializers.ValidationError(
                {"staff_id": "Staff ID is required for lecturer accounts."}
            )

        return attrs

    def create(self, validated_data: dict) -> User:
        """Use create_user() so the password is hashed correctly."""
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
            is_student=validated_data.get("is_student", False),
            is_lecturer=validated_data.get("is_lecturer", False),
            matric_number=validated_data.get("matric_number"),
            staff_id=validated_data.get("staff_id"),
            phone=validated_data.get("phone", ""),
        )
        return user


# ─────────────────────────────────────────────────────────────────────────────
# USER — Profile Update (Partial Write)
# ─────────────────────────────────────────────────────────────────────────────

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Allows a user to update their own non-sensitive profile fields.
    Role flags and identifiers (matric/staff) are immutable after creation.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
