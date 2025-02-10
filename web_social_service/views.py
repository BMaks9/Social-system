from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from datetime import date, datetime, timedelta
from web_social_service.serializers import *
from web_social_service.models import Patronage, Disabilities, Disabilities_Patronage
from web_social_service.minio import add_pic, process_file_upload, delete_image
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from random import randint
from django.http import HttpResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework import viewsets
from rest_framework import permissions
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import redis
import uuid
from rest_framework.decorators import action
from web_social_service.qr_generate import generate_disability_qr

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and (request.user.is_staff or request.user.is_superuser)
        )


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["register", "login"]:
            permission_classes = [AllowAny]
        elif self.action in ["update_profile", "logout"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Пользователь зарегистрирован"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["put"], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data  # Это уже объект пользователя
            login(request, user)  # Входим как пользователь
            return Response(
                {
                    "message": "Успешный вход",
                    "username": user.username,
                    "password": user.password,
                    "is_staff": user.is_staff,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    @csrf_exempt  # Можно убрать CSRF, если необходимо
    def logout(self, request):
        # Если нужно, можно выполнить дополнительные действия перед выходом
        logout(request)
        return Response({"message": "Вы вышли из системы"}, status=status.HTTP_200_OK)


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


# @permission_classes([AllowAny])  # разрешаем доступ любому пользователю
# @authentication_classes([])  # не используем аутентификацию для этого эндпоинта
# @csrf_exempt  # отключаем CSRF для тестов с Postman или Swagger
# @swagger_auto_schema(method='post', request_body=UserSerializer())
# @api_view(['POST'])
# def login_view(request):
#     username = request.data.get("username")
#     password = request.data.get("password")
#     # Попытка аутентификации пользователя
#     user = authenticate(request, username=username, password=password)
#     if user is not None:
#         # Вход пользователя в систему
#         login(request, user)  # Django автоматически установит cookie для сессии
#         random_key = str(uuid.uuid4())
#         session_storage.set(random_key, username)
#         request.session['random_key'] = random_key
#         # Ответ с успешным логином
#         return Response({'status': 'ok', 'username': user.username,  # возвращаем имя пользователя
#             'password': user.password,})
#     else:
#         # Ошибка логина
#         return Response({'status': 'error', 'error': 'login failed'}, status=400)

# @permission_classes([AllowAny])  # Разрешаем доступ любому пользователю
# @authentication_classes([])  # Не используем аутентификацию для этого эндпоинта
# @csrf_exempt  # Отключаем CSRF для тестов с Postman или Swagger
# @swagger_auto_schema(method='post', request_body=UserSerializer())
# @api_view(['POST'])
# def login_view(request):
#     username = request.data.get("username")
#     password = request.data.get("password")

#     # Попытка аутентификации пользователя
#     user = authenticate(request, username=username, password=password)

#     if user is not None:
#         # Вход пользователя в систему
#         login(request, user)  # Django автоматически установит cookie для сессии

#         # Получаем или создаем disability (черновик заявки)
#         disability = Disabilities.objects.filter(status='draft', creator=request.user).first()

#         if disability:
#             # Сохраняем данные о disability в сессии
#             request.session['disability_id'] = disability.id
#             request.session['current_count'] = Disabilities_Patronage.objects.filter(disabilities_id=disability.id).count()

#         # Ответ с успешным логином
#         return Response({'status': 'ok', 'username': user.username, 'password': user.password})
#     else:
#         # Ошибка логина
#         return Response({'status': 'error', 'error': 'login failed'}, status=400)


# @api_view(['POST'])
# def logout_view(request):
#     logout(request._request)
#     return Response({'status': 'Success'})


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Обновить данные пользователя",
        request_body=UserSerializer,
        responses={
            200: "Profile updated successfully",
            400: "Invalid data or update failed",
        },
    )
    def put(self, request, pk, *args, **kwargs):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Сохраняем обновленные данные
            return Response(
                {"message": "Profile updated successfully"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#############################################
class PatronageList(APIView):
    model_class = Patronage
    serializer_class = GetPatronagesSerializer

    # Возвращает список услуг (все пользовватели)
    @swagger_auto_schema(
        operation_description="Get a list of patronages",
        manual_parameters=[
            openapi.Parameter(
                "patronageName",
                openapi.IN_QUERY,
                description="Optionally filter by name of patronage",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={200: GetPatronagesSerializer(many=True)},
    )
    def get(self, request, format=None):
        patronages = self.model_class.objects.filter(deleted=0).all()

        if "patronageName" in request.GET:
            query = request.GET.get("patronageName")
            patronages = self.model_class.objects.filter(title__istartswith=query)
        serializer = self.serializer_class(patronages, many=True)
        resp = serializer.data
        try:
            disability = Disabilities.objects.get(status="draft", creator=request.user)
            list_patronage = Disabilities_Patronage.objects.filter(
                disabilities_id=disability.id
            )
            current_count = list_patronage.count()
            resp.append(
                {"disabilities_id": disability.id, "current_count": current_count}
            )
        except:
            resp.append({"disabilities_id": None, "current_count": None})

        return Response(resp)

    # class PatronageList(APIView):
    #     model_class = Patronage
    #     serializer_class = GetPatronagesSerializer

    #     # Возвращает список услуг (для всех пользователей)
    #     @swagger_auto_schema(
    #         operation_description="Get a list of patronages",
    #         manual_parameters=[openapi.Parameter('patronageName', openapi.IN_QUERY, description="Optionally filter by name of patronage", type=openapi.TYPE_STRING)],
    #         responses={200: GetPatronagesSerializer(many=True)}
    #     )
    #     def get(self, request, format=None):
    #         patronages = self.model_class.objects.filter(deleted=0).all()

    #         # Применяем фильтр по имени услуги
    #         if 'patronageName' in request.GET:
    #             query = request.GET.get('patronageName')
    #             patronages = self.model_class.objects.filter(title__istartswith=query)

    #         # Сериализуем данные
    #         serializer = self.serializer_class(patronages, many=True)
    #         resp = serializer.data

    #         # Получаем информацию из сессии
    #         disability_id = request.session.get('disability_id', None)
    #         current_count = request.session.get('current_count', None)

    #         if disability_id:
    #             try:
    #                 # Попытка найти disability с заданным ID
    #                 disability = Disabilities.objects.get(id=disability_id)
    #                 resp.append({'disabilities_id': disability.id, 'current_count': current_count})
    #             except Disabilities.DoesNotExist:
    #                 resp.append({'disabilities_id': None, 'current_count': None})
    #         else:
    #             resp.append({'disabilities_id': None, 'current_count': None})

    #         return Response(resp)

    # Добавляет новую услугу (moderator)
    @swagger_auto_schema(
        operation_description="Add new patronage (moderators only).",
        request_body=GetPatronagesDetailSerializer,
        responses={201: GetPatronagesDetailSerializer, 400: "Bad request"},
    )
    @method_permission_classes([IsManager])
    def post(self, request, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = GetPatronagesDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatronageDetail(APIView):
    model_class = Patronage
    serializer_class = GetPatronagesDetailSerializer

    # Возвращает информацию об услуге (все пользователи)
    @swagger_auto_schema(
        operation_description="Get information about patronage",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Id of the patronage",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={200: GetPatronagesDetailSerializer(), 404: "Bad request"},
    )
    def get(self, request, id, format=None):
        patronage = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(patronage)
        return Response(serializer.data)

    # Обновляет информацию об услуге (для модератора)
    @swagger_auto_schema(
        operation_description="Update information about patronage (moderators only).",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Id of the patronage",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={200: GetPatronagesDetailSerializer(), 400: "Bad request"},
    )
    @method_permission_classes([IsManager])
    def put(self, request, id, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        patronage = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(patronage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаляет информацию об услуге (moderator) + удаление изображения minio
    @swagger_auto_schema(
        operation_description="Delete a patronage by Id (moderators only).",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Id of the patronage",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={204: "No Content", 403: "Forbidden"},
    )
    @method_permission_classes([IsManager])
    def delete(self, request, id, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        patronage = get_object_or_404(self.model_class, id=id)
        delete_image(patronage.img)
        patronage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PatronageDraft(APIView):
    model_class = Disabilities_Patronage
    serializer_class = GetDisabilities_Patronage_Serializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # формирование заявки (создатель)
    @swagger_auto_schema(
        operation_description="Create or update a patronage request for a disability",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Id of the patronage",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        request_body=GetDisabilities_Patronage_Serializer,
        responses={
            200: "Successfully",
            400: "Invalid data provided",
        },
    )
    @csrf_exempt
    def post(self, request, id, format=None):
        try:
            disability = Disabilities.objects.get(status="draft", creator=request.user)
        except:
            disability = Disabilities(
                status="draft", data_created=date.today(), creator=request.user
            )
            disability.save()
        request.data["disabilities_id"] = disability.id
        request.data["patronage_id"] = id
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatronageImage(APIView):
    model_class = Patronage
    serializer_class = GetPatronagesSerializer

    @swagger_auto_schema(
        operation_description="Update patronage image (logo) for a specific patronage",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="ID of the patronage",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        request_body=GetPatronagesSerializer,
        responses={
            200: openapi.Response(
                description="Patronage image successfully updated",
                schema=GetPatronagesSerializer,
            ),
            400: openapi.Response(description="Invalid data provided"),
            403: openapi.Response(description="Forbidden, user is not staff"),
        },
    )
    # Изменение фото логотипа (модератор)
    @method_permission_classes([IsManager])
    def post(self, request, id, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        patronage = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(patronage, data=request.data, partial=True)
        if "pic" in serializer.initial_data:
            pic_result = add_pic(patronage, serializer.initial_data["pic"])
            if "error" in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisabilitiesList(APIView):
    model_class = Disabilities
    serializer_class = GetDisabylitiesSerializer
    permission_classes = [IsAuthenticated]

    # Возвращает список заявок (создатель)/(модератор все заявки)
    @swagger_auto_schema(
        operation_description="Retrieve a list of disabilities based on optional filters for status and data_compilation.",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Filter by status of the disability (e.g. 'approved', 'pending').",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "data_compilation",
                openapi.IN_QUERY,
                description="Filter by the date of compilation of the disability request.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of disabilities",
                schema=GetDisabylitiesSerializer(many=True),
            ),
            400: openapi.Response(description="Invalid data format"),
        },
    )
    def get(self, request, format=None):
        status_filter = request.query_params.get("status", None)
        start_date_filter = request.query_params.get("start_date", None)
        end_date_filter = request.query_params.get("end_date", None)

        if request.user.is_staff:
            disabilities = self.model_class.objects.exclude(status__in=["draft"]).all()
        else:
            disabilities = (
                self.model_class.objects.exclude(status__in=["draft", "deleted"])
                .filter(creator=request.user)
                .all()
            )

        # Фильтрация по статусу
        if status_filter:
            disabilities = disabilities.filter(status=status_filter)

        # Фильтрация по диапазону дат компиляции
        if start_date_filter and end_date_filter:
            try:
                start_date = datetime.strptime(start_date_filter, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_filter, "%Y-%m-%d")
                disabilities = disabilities.filter(
                    data_compilation__range=[start_date, end_date]
                )
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )
        elif start_date_filter:
            try:
                start_date = datetime.strptime(start_date_filter, "%Y-%m-%d")
                disabilities = disabilities.filter(data_compilation__gte=start_date)
            except ValueError:
                return Response(
                    {"detail": "Invalid start date format. Use YYYY-MM-DD."}, status=400
                )
        elif end_date_filter:
            try:
                end_date = datetime.strptime(end_date_filter, "%Y-%m-%d")
                disabilities = disabilities.filter(data_compilation__lte=end_date)
            except ValueError:
                return Response(
                    {"detail": "Invalid end date format. Use YYYY-MM-DD."}, status=400
                )

        serializer = self.serializer_class(disabilities, many=True)
        resp = serializer.data
        return Response(resp)


class DisabilitiesDetail(APIView):
    model_class = Disabilities
    serializer_class = GetDisabilityDetail_Serializer
    permission_classes = [IsAuthenticated]

    # Просмотр заявки (создатель)
    @swagger_auto_schema(
        operation_description="Retrieve a specific disability request details by ID.",
        responses={
            200: openapi.Response(
                description="Disability request details",
                schema=GetDisabilityDetail_Serializer,
            ),
            404: openapi.Response(
                description="Disability not found or already deleted"
            ),
        },
    )
    def get(self, request, id, format=None):
        disability = get_object_or_404(
            self.model_class.objects.exclude(status="deleted"), id=id
        )
        serializer = self.serializer_class(disability)
        return Response(serializer.data)

    # Изменение заявки (создатель)
    @swagger_auto_schema(
        operation_description="Update a specific disability request (only 'draft' status can be updated).",
        request_body=GetDisabilityDetail_Serializer,
        responses={
            200: openapi.Response(
                description="Disability request successfully updated"
            ),
            400: openapi.Response(description="Invalid data provided"),
            404: openapi.Response(
                description="Disability not found or not in 'draft' status"
            ),
        },
    )
    def put(self, request, id, format=None):
        disability = get_object_or_404(self.model_class, id=id, status="draft")
        serializer = self.serializer_class(disability, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # удаление заявки (создатель)
    @swagger_auto_schema(
        operation_description="Soft delete a specific disability request (marks it as 'deleted').",
        responses={
            200: openapi.Response(
                description="Disability request successfully deleted"
            ),
            400: openapi.Response(description="Invalid data provided"),
            404: openapi.Response(description="Disability not found"),
        },
    )
    def delete(self, request, id, format=None):
        data = request.data.copy()
        data["status"] = "deleted"
        disability = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(disability, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisabilitiesSubmit(APIView):
    model_class = Disabilities
    serializer_class = GetDisabylitiesSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Submit a disability request, updating its status to 'formed' and setting the data_compilation date.",
        request_body=GetDisabylitiesSerializer,
        responses={
            200: openapi.Response(
                description="Disability request successfully submitted",
                schema=GetDisabylitiesSerializer,
            ),
            400: openapi.Response(
                description="Bad request, missing required fields (phone or address)"
            ),
            404: openapi.Response(
                description="Disability request not found or incorrect status"
            ),
        },
    )
    # Формирование заявки (создатель)
    def put(self, request, id, format=None):
        request.data["data_compilation"] = datetime.now()
        request.data["status"] = "formed"
        disability = get_object_or_404(
            self.model_class, id=id, status="draft", creator=request.user
        )
        if not (disability.phone or disability.address):
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data="Заполните поля заявки"
            )
        serializer = self.serializer_class(disability, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisabilitiesComplete(APIView):
    model_class = Disabilities
    serializer_class = GetDisabylitiesSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Complete or reject a disability request. Based on the action parameter, update the status to 'completed' or 'rejected'.",
        manual_parameters=[
            openapi.Parameter(
                "action",
                openapi.IN_QUERY,
                description="Action to perform, either 'completed' or 'rejected'.",
                type=openapi.TYPE_STRING,
                enum=["completed", "rejected"],
            ),
        ],
        request_body=GetDisabylitiesSerializer,
        responses={
            200: openapi.Response(
                description="Disability request successfully updated",
                schema=GetDisabylitiesSerializer,
            ),
            400: openapi.Response(description="Invalid data or action parameter"),
            403: openapi.Response(description="Forbidden, user is not staff"),
            404: openapi.Response(
                description="Disability request not found or incorrect status"
            ),
        },
    )
    # Завершение заявки (модератор)
    @method_permission_classes([IsManager])
    def put(self, request, id, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        disability = get_object_or_404(self.model_class, id=id, status="formed")

        request.data["data_finished"] = datetime.now()
        request.data["moderator"] = request.user.username
        action = request.GET.get("action")

        if action == "completed":
            request.data["status"] = "completed"
            request.data["date_dilivery"] = date.today() + timedelta(
                days=randint(1, 20)
            )

            patronages = Disabilities_Patronage.objects.filter(disabilities_id=id)
            patronages_serializer = GetDisabilitiesPatronageDetailSerializer(
                patronages, many=True
            )

            qr_code_base64 = generate_disability_qr(
                disability, patronages_serializer.data, request.data["date_dilivery"]
            )
            request.data["qr"] = qr_code_base64

        elif action == "rejected":
            request.data["status"] = "rejected"

        serializer = self.serializer_class(disability, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Disabilities_Patronage_Edit(APIView):
    model_class = Disabilities_Patronage
    serializer_class = GetDisabilities_Patronage_Serializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete the association between a disability and a patronage.",
        responses={
            204: openapi.Response(
                description="Disability patronage association successfully deleted"
            ),
            404: openapi.Response(
                description="Disability patronage association not found"
            ),
        },
    )
    # Удаление услуги из заявки (создатель)
    def delete(self, request, disabilityId, patronageId, format=None):
        disability_patronage = get_object_or_404(
            self.model_class, disabilities_id=disabilityId, patronage_id=patronageId
        )
        disability_patronage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Update the association between a disability and a patronage.",
        request_body=GetDisabilities_Patronage_Serializer,
        responses={
            200: openapi.Response(
                description="Disability patronage association successfully updated",
                schema=GetDisabilities_Patronage_Serializer,
            ),
            400: openapi.Response(
                description="Invalid data provided for updating disability patronage association"
            ),
            404: openapi.Response(
                description="Disability patronage association not found"
            ),
        },
    )
    # Изменение м-м заявки (создатель)
    def put(self, request, disabilityId, patronageId, format=None):
        disability_patronage = get_object_or_404(
            self.model_class, disabilities_id=disabilityId, patronage_id=patronageId
        )
        serializer = self.serializer_class(
            disability_patronage, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class UsersReg(APIView):
#     model_class = User
#     serializer_class = UserSerializer

#     def post(self, request, format=None):
#         serializer = self.serializer_class(data=request.data)

#         if serializer.is_valid():
#             user = serializer.save()
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({'token': token.key}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UsersProfile(APIView):
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UsersLogin(APIView):
#     model_class = User
#     serializer_class = UserAuthSerializer

#     def post(self, request, format=None):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({'token': token.key}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UsersLogout(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         request.user.auth_token.delete()  # Удаляем токен
#         logout(request)
#         return Response(status=status.HTTP_204_NO_CONTENT)
