from web_social_service.models import Patronage
from web_social_service.models import Disabilities
from web_social_service.models import Disabilities_Patronage
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from collections import OrderedDict
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "password", "email", "is_staff", "is_active"]

    def update(self, instance, validated_data):
        # Обновление всех полей, кроме пароля
        password = validated_data.get("password", None)
        if password:
            instance.password = make_password(password)  # Хешируем новый пароль

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            if (
                attr != "password"
            ):  # Не обновляем пароль здесь, так как мы это делаем выше
                setattr(instance, attr, value)

        instance.save()
        return instance

    # def create(self, validated_data):
    #     user = User.objects.create_user(
    #         username=validated_data['username'],
    #         email=validated_data['email'],
    #         password=validated_data['password']
    #     )
    #     return user
    # def get_fields(self):
    #     new_fields = OrderedDict()
    #     for name, field in super().get_fields().items():
    #         field.required = False
    #         new_fields[name] = field
    #     return new_fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")


class UserAuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if user is None:
            raise serializers.ValidationError("Неверные учетные данные")
        return {"user": user}


class GetPatronagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patronage
        # Поля, которые мы сериализуем
        fields = ["id", "title", "img"]

    # def get_fields(self):
    #         new_fields = OrderedDict()
    #         for name, field in super().get_fields().items():
    #             field.required = False
    #             new_fields[name] = field
    #         return new_fields


class GetPatronagesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patronage
        # Поля, которые мы сериализуем
        fields = ["id", "title", "description", "img"]


class GetDisabylitiesSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source="creator.username", read_only=True)
    moderator = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="username",
        required=False,
        allow_null=True,
    )

    class Meta:
        # Модель, которую мы сериализуем
        model = Disabilities
        # Поля, которые мы сериализуем
        fields = [
            "id",
            "phone",
            "address",
            "status",
            "data_created",
            "data_compilation",
            "data_finished",
            "date_dilivery",
            "creator",
            "moderator",
            "qr",
        ]


class GetDisabilities_Patronage_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Disabilities_Patronage
        # Поля, которые мы сериализуем
        fields = ["id", "disabilities_id", "patronage_id", "comment"]


class GetDisabilitiesPatronageDetailSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="patronage_id.id")
    title = serializers.CharField(source="patronage_id.title")
    img = serializers.CharField(source="patronage_id.img")

    class Meta:
        model = Disabilities_Patronage
        # Поля, которые мы сериализуем
        fields = ["id", "title", "img", "comment"]


class GetDisabilityDetail_Serializer(serializers.ModelSerializer):
    patronages = serializers.SerializerMethodField()

    def get_patronages(self, obj):
        patronages = Disabilities_Patronage.objects.filter(disabilities_id=obj.id)
        serializer = GetDisabilitiesPatronageDetailSerializer(patronages, many=True)
        return serializer.data

    class Meta:
        model = Disabilities
        fields = [
            "id",
            "phone",
            "address",
            "status",
            "data_created",
            "data_compilation",
            "data_finished",
            "date_dilivery",
            "patronages",
        ]
