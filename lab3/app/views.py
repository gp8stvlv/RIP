from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models import Q
from rest_framework import status as drf_status
from . import models
from rest_framework.decorators import api_view
from rest_framework import filters
from django.db.models import Prefetch
from app.serializers import UsersSerializer, RequestsSerializer, ChemistryEquipmentSerializer, RequestServiceSerializer
from app.models import Users, Requests, ChemistryEquipment, RequestService
from minio import Minio
from django.utils import timezone
from django.db import IntegrityError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView
from django.conf import settings
import io
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from minio import Minio
from minio.error import S3Error
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
import hashlib
import secrets


MODERATOR_ID = 4  # Идентификатор модератора (замените на фактический идентификатор)
USER_ID = 1  # Идентификатор модератора (замените на фактический идентификатор)


# химическое оборудование 
# get услуги с фильтром
from app.redis_view import (
    set_key,
    get_value,
    delete_value
)

def check_user(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id').decode())
        return user.role == 'USR'
    return False

def check_authorize(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id'))
        return user
    return None

def check_moderator(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id'))
        return user.role == 'MOD'
    return False

@api_view(['POST'])
def registration(request, format=None):
    required_fields = ['username', 'password', 'email', 'role']
    missing_fields = [field for field in required_fields if field not in request.data]

    if missing_fields:
        return Response({'Ошибка': f'Не хватает обязательных полей: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)

    if Users.objects.filter(email=request.data['email']).exists() or Users.objects.filter(username=request.data['username']).exists():
        return Response({'Ошибка': 'Пользователь с таким email или username уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    Users.objects.create(
        username=request.data['username'],
        password=request.data['password'],
        email=request.data['email'],
        role = request.data['role'],
    )
    
    return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_view(request, format=None):

    existing_session = request.COOKIES.get('session_key')
    if existing_session and get_value(existing_session):
        return Response({'user_id': get_value(existing_session)})
    
    username_ = request.data.get("username")
    password = request.data.get("password")

    print(username_)
    print(password)

    if not username_ or not password:
        return Response({'error': 'Необходимы логин и пароль'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        print("username_", username_)
        user = Users.objects.get(username=username_)
    except Users.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if password == user.password:
        random_part = secrets.token_hex(8)
        session_hash = hashlib.sha256(f'{user.user_id}:{username_}:{random_part}'.encode()).hexdigest()
        set_key(session_hash, user.user_id)

        response = JsonResponse({'user_id': user.user_id})
        response.set_cookie('session_key', session_hash, max_age=86400)
        return response

    return Response(status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def logout_view(request):
    session_key = request.COOKIES.get('session_key')

    if session_key:
        if not get_value(session_key):
            return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
        delete_value(session_key)
        response = JsonResponse({'message': 'Вы успешно вышли из системы'})
        response.delete_cookie('session_key')
        return response
    else:
        return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def login_view_get(request, format=None):
    existing_session = request.COOKIES.get('session_key')
    print(existing_session)
    if existing_session and get_value(existing_session):
        return Response({'user_id': get_value(existing_session)})
    return Response(status=status.HTTP_401_UNAUTHORIZED)



# Initialize Minio client
client = Minio(
    endpoint="127.0.0.1:9000",
    access_key='minio',
    secret_key='minio124',
    secure=False
)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'photo': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY),
        }
    )
)
@api_view(["POST"])
def upload_photo(request, format=None):
    # Check if the request contains the photo file
    if 'photo' not in request.FILES:
        return Response({'error': 'No photo file provided'}, status=status.HTTP_400_BAD_REQUEST)

    photo_file = request.FILES['photo']

    # Generate a unique filename for the photo
    filename = f"photo_new_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"

    try:
        # Use Minio client to upload the file
        client.put_object(
            bucket_name='chemistry',
            object_name=filename,
            data=photo_file,
            length=photo_file.size,
            content_type='image/jpeg',
        )

        # Construct the URL for the uploaded photo
        photo_url = f"http://localhost:9000/chemistry/{filename}"

        return Response({'photo_url': photo_url}, status=status.HTTP_201_CREATED)

    except S3Error as e:
        return Response({'error': f'Error uploading photo to Minio: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    operation_summary='Получить список химического оборудования',
    operation_description='Получить список химического оборудования.',
    responses={
        200: openapi.Response(
            description='Успешный ответ',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user_request': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'equipment': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT),  # Схема для элементов в массиве
                    ),
                },
            ),
        ),
        400: 'Неверный запрос',
        500: 'Внутренняя ошибка сервера',
    },
    manual_parameters=[
        openapi.Parameter('type', openapi.IN_QUERY, description='Фильтр по названию оборудования', type=openapi.TYPE_STRING),
        openapi.Parameter('price', openapi.IN_QUERY, description='Фильтр по цене оборудования', type=openapi.TYPE_NUMBER),
    ]
)
@api_view(['GET'])
def chemistryEquipment_getAll(request, format=None):
    user_id = USER_ID  # Replace this with your actual way of getting the user ID
    print(request.user.id)

    # Check if there is a request with status 'введен' for the current user
    user_request = Requests.objects.filter(status='введен', user=user_id).first()
    user_request_id = user_request.request_id if user_request else None

    input_type = request.GET.get('type', '')
    input_price = request.GET.get('price', '')

    matching_models = models.ChemistryEquipment.objects.filter(status='действует').order_by("chemistry_product_id")

    if input_type:
        matching_models = matching_models.filter(
            Q(type__icontains=input_type),
            status='действует'
        )

    if input_price:
        matching_models = matching_models.filter(
            Q(price__icontains=input_price),
            status='действует'
        )

    matching_model_ids = matching_models.values_list('chemistry_product_id', flat=True)
    print("matching_model_ids", matching_model_ids)
    serializer = ChemistryEquipmentSerializer(matching_models, many=True)

    return Response({
        'user_request_id': user_request_id,
        'equipment': serializer.data,
    })

@swagger_auto_schema(
    method='get',
    operation_summary='Получить информацию о химическом оборудовании по ID',
    operation_description='Получить информацию о химическом оборудовании по его уникальному идентификатору.',
    responses={
        200: openapi.Response(
            description='Успешный ответ',
            schema=ChemistryEquipmentSerializer,  # Замените на ваш сериализатор
        ),
        404: 'Не найдено',
        500: 'Внутренняя ошибка сервера',
    },
)
@api_view(['Get'])
def chemistryEquipment_getByID(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    if request.method == 'GET':
        serializer = ChemistryEquipmentSerializer(equipment)
        return Response(serializer.data)

@swagger_auto_schema(
    method='post',
    request_body=ChemistryEquipmentSerializer,  # Replace with your actual serializer
    responses={
        201: openapi.Response(
            description='Успешно создано',
            schema=ChemistryEquipmentSerializer,  # Replace with your actual serializer
        ),
        400: 'Неверный запрос',
    },
    operation_summary='Создать новое химическое оборудование',
    operation_description='Создает новую запись о химическом оборудовании с использованием предоставленных данных.',
)
@api_view(["Post"])
def add_chemistryEquipment_post(application, format=None):
    serializer = ChemistryEquipmentSerializer(data=application.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    responses={
        201: openapi.Response(description='Успешно создано'),
        500: 'Внутренняя ошибка сервера',
    },
)
@api_view(['POST'])
def chemistryEquipment_post(request, chemistry_product_id, format=None):

    user_id = USER_ID
    # Извлечение объектов Requests со статусом 'введен'
    requests_entered = Requests.objects.filter(status='введен', user=user_id)
    serializer_Requests = RequestsSerializer(requests_entered, many=True)

    # Получение списка request_id со статусом введен
    request_ids = [request['request_id'] for request in serializer_Requests.data]

    if not request_ids:
        # Если request_ids пуст, новая пустая заявка
        new_request = Requests()
        new_request.user_id = user_id
        new_request.status = 'введен'
        new_request.created_at = timezone.now()
        new_request.save()
        request_id = new_request.request_id
        print('Created new request with request_id ID:', request_id)

        # Возможно, нужно также уведомить пользователя или выполнить другие действия

    else:
        # Продолжите обработку существующей заявки, взяв первый элемент из списка request_ids
        request_id = request_ids[0]
        print('Using existing request with ID:', request_id)
    production_count = 1
    # Получите объект ChemistryEquipment по ID
    chemistry_equipment = get_object_or_404(ChemistryEquipment, pk=chemistry_product_id)

    try:
        # Создайте запись в таблице RequestService, связанную с созданной выше заявкой и новым оборудованием
        request_service = RequestService.objects.create(request_id=request_id, chemistry_product=chemistry_equipment, production_count=production_count)

        # Возвращаем успешный ответ
        return Response({'success': 'заявка успешно создана'}, status=status.HTTP_201_CREATED)
    except IntegrityError as e:
        # Выводим информацию об ошибке в консоль
        print(f'IntegrityError: {e}')
        return Response({'error': 'дубликат ключей (с такими id уже заполнена таблица RequestService, количество менять в put)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    method='put',
    request_body=ChemistryEquipmentSerializer,  # Replace with your actual serializer
    responses={
        200: openapi.Response(
            description='Успешно изменено',
            schema=ChemistryEquipmentSerializer,  # Replace with your actual serializer
        ),
        400: 'Неверный запрос',
    },
    operation_summary='Изменить существующее химическое оборудование',
    operation_description='Изменяет существующую запись о химическом оборудовании с использованием предоставленных данных.',
)
@api_view(['Put'])
def chemistryEquipment_put(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    serializer = ChemistryEquipmentSerializer(equipment, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    responses={
        204: openapi.Response(description='Успешно удалено'),
        404: 'Не найдено',
    },
    operation_summary='Логическое удаление химического оборудования',
    operation_description='Логически удаляет запись о химическом оборудовании, устанавливая статус "удален".',
)
@api_view(['DELETE'])
def chemistryEquipment_delete(request, pk, format=None):    
    # Проверка существования объекта с указанным id
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    
    # Установите статус 'удален'
    equipment.status = 'удален'
    
    # Сохраните объект
    equipment.save()

    # Возвращаем успешный ответ
    return Response({"detail": "Оборудование успешно удалено."}, status=status.HTTP_204_NO_CONTENT)

# добавить услугу в заявку, добавить вторую услугу, список услуг с заявкой-черновиком

#заявки
"""
--     введен,
--     в работе,
--     завершен,
--     отменен,
--     удален.
"""

# возвращает текущую роль
def get_role_by_Requests(request_instance):
    user_id = request_instance.user_id
    try:
        user = Users.objects.get(user_id=user_id)
        user_data = UsersSerializer(user).data
        user_role = user_data['role']
        return user_role
    except Users.DoesNotExist:
       pass

#request/?created_at=2023-09-15 - фильтрует объекты запросов по точной дате создания
#request/?status=в работе - фильтрует объекты запросов по статусу "в работе"
#request/?status=в работе&created_at=2020-09-15

 # http://0.0.0.0:8000/request/?status=в работе&formation_date_from=2020-09-01&formation_date_to=2024-09-30
@swagger_auto_schema(
    method='get',
    operation_summary='Получить список заявок с учетом фильтров',
    operation_description='Получить список заявок, отфильтрованных по дате создания, статусу, и дате формирования.',
    responses={
        200: openapi.Response(
            description='Успешный ответ',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'requests': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    # Add more properties if needed
                },
            ),
        ),
        400: 'Неверный запрос',
    },
    manual_parameters=[
        openapi.Parameter('created_at', openapi.IN_QUERY, description='Фильтр по дате создания (в формате YYYY-MM-DD)', type=openapi.TYPE_STRING),
        openapi.Parameter('status', openapi.IN_QUERY, description='Фильтр по статусу заявки', type=openapi.TYPE_STRING),
        openapi.Parameter('formation_date_from', openapi.IN_QUERY, description='Начальная дата формирования (в формате YYYY-MM-DD)', type=openapi.TYPE_STRING),
        openapi.Parameter('formation_date_to', openapi.IN_QUERY, description='Конечная дата формирования (в формате YYYY-MM-DD)', type=openapi.TYPE_STRING),
    ]
)


@api_view(['GET'])
def requests_getAll(request, format=None):
    
    created_at = request.GET.get('created_at', None)
    status = request.GET.get('status', None)
    formation_date_from = request.GET.get('formation_date_from', None)
    formation_date_to = request.GET.get('formation_date_to', None)

    queryset = Requests.objects.all()

    if created_at:
        queryset = queryset.filter(created_at=created_at)

    if status:
        queryset = queryset.filter(status=status)

    if formation_date_from and formation_date_to:
        queryset = queryset.filter(formation_date__range=[formation_date_from, formation_date_to])

    matching_RequestService_requests = RequestService.objects.filter(request_id__in=queryset.values_list('request_id', flat=True))
    chemistry_product_ids = matching_RequestService_requests.values_list('chemistry_product_id', flat=True)

    matching_equipment_requests = ChemistryEquipment.objects.filter(chemistry_product_id__in=chemistry_product_ids)

    requests_serializer = RequestsSerializer(queryset, many=True)
   
    equipment_serializer = ChemistryEquipmentSerializer(matching_equipment_requests, many=True)

   # Filter requests with status 'удален' или 'введен'
    filtered_requests = [request for request in requests_serializer.data if request['status'] not in ['удален', 'введен']]


    # Create a list to hold serialized data
    serialized_data = []

    for request_data in filtered_requests:
        user_id = request_data.get('user')
        user_instance = Users.objects.filter(user_id=user_id).first()

        if user_instance:
            username = UsersSerializer(user_instance).data.get('username')
            moderator_id = request_data.get('moderator')
            moderator_instance = Users.objects.filter(user_id=moderator_id).first()

            serialized_data.append({
                'request_id': request_data.get('request_id'),
                'status': request_data.get('status'),
                'created_at': request_data.get('created_at'),
                'formation_date': request_data.get('formation_date'),
                'completion_date': request_data.get('completion_date'),
                'username': username,
                'moderatorname': UsersSerializer(moderator_instance).data.get('username') if moderator_instance else None
            })

    # Combine the serialized data into a single response
    response_data = {
        'requests': serialized_data,
        # 'chemistry_equipment': equipment_serializer.data
    }

    return Response(response_data)

# @api_view(['GET'])
# def requests_getAll(request, format=None):
#     user = check_authorize(request)
    
#     if not user:
#         return Response(status=drf_status.HTTP_403_FORBIDDEN)

#     current_user_id = user.user_id
#     is_moderator = user.role == "moderator"

#     queryset = Requests.objects.filter(~Q(status__in=['удален', 'введен']))

#     if not is_moderator:
#         queryset = queryset.filter(user_id=current_user_id)

#     created_at = request.GET.get('created_at', None)
#     status = request.GET.get('status', None)
#     formation_date_from = request.GET.get('formation_date_from', None)
#     formation_date_to = request.GET.get('formation_date_to', None)

#     if created_at:
#         queryset = queryset.filter(created_at=created_at)

#     if status:
#         queryset = queryset.filter(status=status)

#     if formation_date_from and formation_date_to:
#         queryset = queryset.filter(formation_date__range=[formation_date_from, formation_date_to])

#     matching_RequestService_requests = RequestService.objects.filter(request_id__in=queryset.values_list('request_id', flat=True))
#     chemistry_product_ids = matching_RequestService_requests.values_list('chemistry_product_id', flat=True)

#     matching_equipment_requests = ChemistryEquipment.objects.filter(chemistry_product_id__in=chemistry_product_ids)

#     requests_serializer = RequestsSerializer(queryset, many=True)
#     equipment_serializer = ChemistryEquipmentSerializer(matching_equipment_requests, many=True)

#     serialized_data = []

#     for request_data in requests_serializer.data:
#         user_id = request_data.get('user')
#         user_instance = Users.objects.filter(user_id=user_id).first()
#         username = UsersSerializer(user_instance).data.get('username') if user_instance else None

#         moderator_id = request_data.get('moderator')
#         moderator_instance = Users.objects.filter(user_id=moderator_id).first()
#         moderatorname = UsersSerializer(moderator_instance).data.get('username') if moderator_instance else None

#         serialized_data.append({
#             'request_id': request_data.get('request_id'),
#             'status': request_data.get('status'),
#             'created_at': request_data.get('created_at'),
#             'formation_date': request_data.get('formation_date'),
#             'completion_date': request_data.get('completion_date'),
#             'username': username,
#             'moderatorname': moderatorname
#         })

#     response_data = {
#         'requests': serialized_data,
#     }

#     return Response(response_data)

@swagger_auto_schema(
    method='get',
    operation_summary='Получить заявку по ID с прикрепленными товарами',
    operation_description='Получить информацию о заявке по её уникальному идентификатору (ID), а также список товаров, прикрепленных к данной заявке.',
    responses={
        200: openapi.Response(
            description='Успешный ответ',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'requests': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'chemistry_equipment': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                },
            ),
        ),
        404: 'Заявка не найдена',
    },
    manual_parameters=[
        openapi.Parameter('pk', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['GET'])
def requests_getByID(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)

    user = None
    moderator = None

    if request_instance.user:
        user = Users.objects.filter(user_id=request_instance.user.user_id).first()
        user_serializer = UsersSerializer(user)

    if request_instance.moderator:
        moderator = Users.objects.filter(user_id=request_instance.moderator.user_id).first()
        moderator_serializer = UsersSerializer(moderator)

    matching_RequestService_requests = RequestService.objects.filter(request=request_instance)
    chemistry_product_ids = matching_RequestService_requests.values_list('chemistry_product_id', flat=True)

    matching_equipment_requests = ChemistryEquipment.objects.filter(chemistry_product_id__in=chemistry_product_ids)

    requests_serializer = RequestsSerializer(request_instance)
    equipment_serializer = ChemistryEquipmentSerializer(matching_equipment_requests, many=True)

    # Create a dictionary to hold the counts for each Chemistry Product ID
    equipment_count_dict = {}
    for item in matching_RequestService_requests:
        if item.chemistry_product_id not in equipment_count_dict:
            equipment_count_dict[item.chemistry_product_id] = item.production_count
        else:
            equipment_count_dict[item.chemistry_product_id] += item.production_count

    response_data = {
        'requests': {
            **requests_serializer.data,
            'user': user_serializer.data if user else None,
            'moderator': moderator_serializer.data if moderator else None
        },
        'chemistry_equipment': [
            {
                'equipment': equipment,
                'production_count': equipment_count_dict[equipment['chemistry_product_id']]
            } for equipment in equipment_serializer.data
        ] if matching_equipment_requests else None
    }

    return Response(response_data)

@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            # Add more properties if needed
        },
    ),
    responses={
        200: openapi.Response(
            description='Успешное обновление заявки',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'request_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    # Add more properties if needed
                },
            ),
        ),
        400: 'Неверный запрос',
        404: 'Заявка не найдена',
    },
    manual_parameters=[
        openapi.Parameter('pk', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['PUT'])
def requestsModerator_put(request, pk, format=None):
    try:
        request_instance = Requests.objects.get(request_id=pk)
    except Requests.DoesNotExist:
        return Response({'error': 'неверный requist'}, status=404)

    current_status = request_instance.status

    if current_status == 'удален':
        return Response({'error': 'у заявки статус удален'}, status=404)
    elif current_status == 'завершен':
        return Response({'error': 'заявка завершена'}, status=404)
    elif current_status == 'отменен':
        return Response({'error': 'заявка отменена'}, status=404)
    elif current_status != 'в работе':
        return Response({'error': 'заявка не в статусе "в работе", нельзя перевести в "завершен" или "отменен"'}, status=400)

    # Set completion_date to the current date and time
    request_instance.completion_date = timezone.now()

    # Define the fields you want to update
    fields_to_update = ['status', 'completion_date']

    # Create an instance of the serializer with partial=True
    serializer = RequestsSerializer(request_instance, data=request.data, partial=True)

    # Filter the fields you want to update
    filtered_data = {key: request.data[key] for key in fields_to_update if key in request.data}

    # Check if 'status' is in the request data and not set to 'удален'
    if 'status' in request.data:
        new_status = request.data['status']
        allowed_statuses = {'завершен', 'отменен'}

        if new_status not in allowed_statuses:
            return Response({("доступные статусы: 'завершен', 'отменен'")}, status=400)

    if serializer.is_valid():
        serializer.update(request_instance, filtered_data)  # Use update instead of save
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            # Add more properties if needed
        },
    ),
    responses={
        200: openapi.Response(
            description='Успешное обновление заявки',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'request_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    # Add more properties if needed
                },
            ),
        ),
        400: 'Неверный запрос',
        404: 'Заявка не найдена',
    },
    manual_parameters=[
        openapi.Parameter('pk', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['PUT'])
def requestsUser_put(request, pk, format=None):
    try:
        request_instance = Requests.objects.get(request_id=pk)
    except Requests.DoesNotExist:
        return Response({'error': 'неверный requist'}, status=404)

    if request_instance.status != 'введен':
        return Response({"error": f"У заявки должен быть статус 'введен', сейчас статус: {request_instance.status}"}, status=404)

    # Update the status to 'в работе' and set the formation_date
    request_instance.status = 'в работе'
    request_instance.formation_date = timezone.now()  # Import timezone from django if not already imported
    request_instance.save()

    # Serialize the updated request_instance
    serializer = RequestsSerializer(request_instance)
    
    return Response(serializer.data)


@api_view(['PUT'])
def requests_user_delete(request, pk, format=None):
    try:
        request_instance = Requests.objects.get(request_id=pk)
    except Requests.DoesNotExist:
        return Response({'error': 'неверный request'}, status=404)

    current_status = request_instance.status

    if current_status != 'введен':
        return Response({'error': 'заявка не в статусе "введен", нельзя удалить'}, status=400)

    # Check if 'status' is in the request data and set to 'удален'
    if 'status' in request.data:
        new_status = request.data['status']
        if new_status != 'удален':
            return Response({'error': 'неверный статус для удаления, используйте "удален"'}, status=400)

    # Set completion_date to the current date and time
    request_instance.completion_date = timezone.now()

    # Set the status to 'удален'
    request_instance.status = 'удален'

    # Define the fields you want to update
    fields_to_update = ['status', 'completion_date']

    # Create an instance of the serializer with partial=True
    serializer = RequestsSerializer(request_instance, data=request.data, partial=True)

    # Filter the fields you want to update
    filtered_data = {key: request.data[key] for key in fields_to_update if key in request.data}

    if serializer.is_valid():
        serializer.update(request_instance, filtered_data)  # Use update instead of save
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)

    


# логическое удаление. удалить введенную заявку юзер: (был статус введен -> сделать удален) админ: если введен менять на другие статусы
@swagger_auto_schema(
    method='delete',
    responses={
        200: openapi.Response(
            description='Успешное удаление заявки',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        403: 'Доступно изменение статуса только для заявок со статусом "введен"',
        404: 'Заявка не найдена',
    },
    manual_parameters=[
        openapi.Parameter('pk', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['DELETE'])
def user_requests_delete(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)

    # Check if the current status is 'введен' before updating to 'удален'
    if request_instance.status == 'введен':
        request_instance.status = 'удален'
        request_instance.save()
        return Response({"message": f"Статус заявки с ID {pk} успешно изменен на 'удален'"}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Доступно изменение статуса только для заявок со статусом 'введен'"}, status=status.HTTP_403_FORBIDDEN)


    
#м-м
@api_view(['GET'])
def get_all_request_services(request, format=None):
    request_services = RequestService.objects.all()
    serializer = RequestServiceSerializer(request_services, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'production_count': openapi.Schema(type=openapi.TYPE_INTEGER),
            # Add more properties if needed
        },
    ),
    responses={
        200: openapi.Response(
            description='Успешное обновление записи в связующей таблице',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'production_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    # Add more properties if needed
                },
            ),
        ),
        400: 'Неверный запрос',
        500: 'Внутренняя ошибка сервера',
    },
    manual_parameters=[
        openapi.Parameter('request_id', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
        openapi.Parameter('chemistry_product_id', openapi.IN_PATH, description='Идентификатор химического продукта', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['PUT'])
def mm_put(request, request_id, chemistry_product_id):
    try:
        # Attempt to get the existing record
        request_service = RequestService.objects.get(
            request_id=request_id,
            chemistry_product_id=chemistry_product_id
        )

        # If the record exists, update only the specified field
        serializer = RequestServiceSerializer(request_service, data=request.data, partial=True)

        if serializer.is_valid():
            request_service.production_count = request.data.get('production_count')
            try:
                request_service.save(update_fields=['production_count'])  # Save only the specified field
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Failed to save record during update: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except RequestService.DoesNotExist:
        # If the record does not exist, create a new one
        serializer = RequestServiceSerializer(data=request.data)

        if serializer.is_valid():
            try:
                serializer.save(request_id=request_id, chemistry_product_id=chemistry_product_id)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Failed to save record during creation: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"Unexpected error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='delete',
    responses={
        200: openapi.Response(
            description='Успешное удаление записи в связующей таблице',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        404: 'Не удалось найти запись. Проверьте ID',
    },
    manual_parameters=[
        openapi.Parameter('request_id', openapi.IN_PATH, description='Идентификатор заявки', type=openapi.TYPE_INTEGER),
        openapi.Parameter('chemistry_product_id', openapi.IN_PATH, description='Идентификатор химического продукта', type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['DELETE'])
def mm_delete(request, request_id, chemistry_product_id):
    # Поиск объектов, у которых request_id и chemistry_product_id совпадают
    matching_objects = RequestService.objects.filter(request_id=request_id, chemistry_product_id=chemistry_product_id)

    # Проверка наличия совпадающих объектов
    if matching_objects.exists():
        # Удаление найденных объектов
        matching_objects.delete()
        return Response({'message': 'запись успешно удалена'})
    else:
        # Возвращение ошибки, если нет совпадающих объектов
        return Response({'error': 'не удалось найти запись. проверьте id'}, status=404)