from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from TimeSyncPro.accounts.models import Company


class SignupCompanySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(max_length=255)
    password1 = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['company_name', 'email', 'password1', 'password2']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password1']
        company_name = validated_data['company_name']

        # Create the user
        user = User.objects.create_user(
            email=email,
            username=email,  # Assuming you're using email as the username
            password=password,
        )
        user.is_company = True
        user.save()

        # Create the company and associate it with the user
        company = Company.objects.create(
            company_name=company_name,
            user=user,
        )
        user.company = company
        company.save()
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")