from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models import Q
from . import models
from rest_framework.decorators import api_view
from rest_framework import filters
from django.db.models import Prefetch
from app.serializers import UsersSerializer, RequestsSerializer, ChemistryEquipmentSerializer, RequestServiceSerializer
from app.models import Users, Requests, ChemistryEquipment, RequestService
from minio import Minio
from django.utils import timezone
from django.db import IntegrityError

MODERATOR_ID = 4  # Идентификатор модератора (замените на фактический идентификатор)
USER_ID = 1  # Идентификатор модератора (замените на фактический идентификатор)


# химическое оборудование 
# get услуги с фильтром
client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='minio',          # логин админа
               secret_key='minio124',       # пароль админа
               secure=False)                # опциональный параметр, отвечающий за вкл/выкл защищенное TLS соединение

# гет с фильтром
@api_view(['Get'])
def chemistryEquipment_getAll(request, format=None):
    input_type = request.GET.get('type', '') # price добавить в поиск
    input_price = request.GET.get('price', '') 

    matching_models = models.ChemistryEquipment.objects.filter(status='действует').order_by("chemistry_product_id") #аналог (через ОРМ) SELECT * FROM chemistry_equipment WHERE status == 'действует'; 

    if input_type:
        matching_models = matching_models.filter(
        Q(type__icontains=input_type), #name__contains для частичного совпадения с введенным текстом.
        status='действует'
    )
        
    if input_price:
        matching_models = matching_models.filter(
        Q(price__icontains=input_price), #name__contains для частичного совпадения с введенным текстом.
        status='действует'
        )
    matching_model_ids = matching_models.values_list('chemistry_product_id', flat=True)
    print("matching_model_ids", matching_model_ids)
    serializer = ChemistryEquipmentSerializer(matching_models, many=True)
    return Response(serializer.data)

# гет по определенному item /4
@api_view(['Get'])
def chemistryEquipment_getByID(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    if request.method == 'GET':
        serializer = ChemistryEquipmentSerializer(equipment)
        return Response(serializer.data)

#добавляем в заявку, если ее нет, то создаем новую, status = введен, если есть, то добавляем в существующую заявку

# @api_view(['POST'])
# def chemistryEquipment_post(pk, quantity, format=None):  
#     draft_application = models.Requests.objects.filter(status='введен').first()
#     if draft_application:
#         print("draft_application", draft_application)
#         if pk:
#             try:
#                 chemistry_product = models.ChemistryEquipment.objects.get(chemistry_product_id=pk)
#             except models.ChemistryEquipment.DoesNotExist:
#                 return Response({'error': 'chemistry_product not found'}, status=status.HTTP_404_NOT_FOUND)

#             RequestService.objects.create(chemistry_product=chemistry_product, application=draft_application, quantity=quantity)

#         return Response({'message': 'chemistry_product added to the existing draft application'}, status=status.HTTP_200_OK)
#     else:
#         return
    

# @api_view(['POST'])
# def chemistryEquipment_post(request, user_id, format=None):
#     requests_entered = Requests.objects.filter(status='введен', user=user_id)   # Извлечение объектов Requests со статусом 'введен'
#     serializer_Requests = RequestsSerializer(requests_entered, many=True)

#     request_ids = [request['request_id'] for request in serializer_Requests.data] # Получение списка request_id со статусом введен
#     if request_ids == []:
#         print('empty')
#     else:
#         request_id = request_ids[0] # Извлечение первой подходящей заявки (вообще не нужно тк у всех только 1 черновик)
#         serializer = ChemistryEquipmentSerializer(data=request.data)
#         print("request_ids", request_id)
    
#     # if serializer.is_valid():
#     #     serializer.save()
#     #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["Post"])
def add_chemistryEquipment_post(application, format=None):
    serializer = ChemistryEquipmentSerializer(data=application.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def chemistryEquipment_post(request, user_id, production_count, chemistry_product_id, format=None):
#     # Проверка существования пользователя и его роли
#     try:
#         Users.objects.get(user_id=user_id)
#     except Users.DoesNotExist:
#         return Response({'error': 'Invalid user ID'}, status=status.HTTP_400_BAD_REQUEST)

#     # Извлечение объектов Requests со статусом 'введен'
#     requests_entered = Requests.objects.filter(status='введен', user=user_id)
#     serializer_Requests = RequestsSerializer(requests_entered, many=True)

#     # Получение списка request_id со статусом введен
#     request_ids = [request['request_id'] for request in serializer_Requests.data]

#     if not request_ids:
#         # Если request_ids пуст, новая пустая заявка
#         new_request = Requests()
#         new_request.user_id = user_id
#         new_request.status = 'введен'
#         new_request.created_at = timezone.now()
#         new_request.save()
#         request_id = new_request.request_id
#         print('Created new request with request_id ID:', request_id)

#         # Возможно, нужно также уведомить пользователя или выполнить другие действия

#     else:
#         # Продолжите обработку существующей заявки, взяв первый элемент из списка request_ids
#         request_id = request_ids[0]
#         print('Using existing request with ID:', request_id)

#     # Извлеките production_count из URL или установите значение по умолчанию
#     try:
#         production_count = int(production_count)
#     except ValueError:
#         production_count = 1

#     # Получите объект ChemistryEquipment по ID
#     chemistry_equipment = get_object_or_404(ChemistryEquipment, pk=chemistry_product_id)

#     try:
#         # Создайте запись в таблице RequestService, связанную с созданной выше заявкой и новым оборудованием
#         request_service = RequestService.objects.create(request_id=request_id, chemistry_product=chemistry_equipment, production_count=production_count)

#         # Возвращаем успешный ответ
#         return Response({'success': 'заявка успешно создана'}, status=status.HTTP_201_CREATED)
#     except IntegrityError as e:
#         # Выводим информацию об ошибке в консоль
#         print(f'IntegrityError: {e}')
#         return Response({'error': 'дубликат ключей (с такими id уже заполнена таблица RequestService, количество менять в put)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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



#изменение оборудования
@api_view(['Put'])
def chemistryEquipment_put(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    serializer = ChemistryEquipmentSerializer(equipment, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Логическое удаление оборудования
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
# @api_view(['GET'])
# def requests_getAll(request, format=None):
#     created_at = request.GET.get('created_at', None)
#     status = request.GET.get('status', None)

#     queryset = Requests.objects.all()

#     if created_at:
#         # Фильтрация по полю "created_at"
#         queryset = queryset.filter(created_at=created_at)

#     if status:
#         # Фильтрация по полю "status"
#         queryset = queryset.filter(status=status)

#     serializer = RequestsSerializer(queryset, many=True)
#     return Response(serializer.data)


 # http://0.0.0.0:8000/request/?status=в работе&formation_date_from=2020-09-01&formation_date_to=2024-09-30
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




# у каждой зявки есть id и нужно вывести все товары, которые прикреплены к данной заявке
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

# @api_view(['PUT'])
# def requests_put(request, pk, format=None):

#     try:
#         request_instance = Requests.objects.get(request_id=pk)
#     except Requests.DoesNotExist:
#         return Response({'error': 'неверный requist'}, status=404)
#     request_instance_status = get_object_or_404(Requests, pk=pk)
#     if request_instance.status == 'удален':
#         return Response({'error': 'у заявки статус удален'}, status=404)

#     # Define the fields you want to update
#     fields_to_update = ['formation_date', 'completion_date', 'status']
    
#     # Create an instance of the serializer with partial=True
#     serializer = RequestsSerializer(request_instance, data=request.data, partial=True)

#     # Filter the fields you want to update
#     filtered_data = {key: request.data[key] for key in fields_to_update if key in request.data}

#     # Check if 'status' is in the request data and not set to 'удален'
#     if 'status' in request.data:
#         new_status = request.data['status']
#         old_status = request_instance.status
#         allowed_statuses = {'введен', 'в работе', 'завершен', 'отменен', 'удален'}

#         if new_status not in allowed_statuses:
#             return Response({("доступные статусы: 'введен', 'в работе', 'завершен', 'отменен'")}, status=400)
        
#         # Check if the new status is 'удален' or if it's the same as the existing status
#         if new_status == 'удален':
#             return Response({'error': 'удалять может только user'}, status=400)

#     if serializer.is_valid():
#         serializer.update(request_instance, filtered_data)  # Use update instead of save
#         return Response(serializer.data)
#     else:
#         return Response(serializer.errors, status=400)

@api_view(['PUT'])
def requestsModerator_put(request, pk, format=None):

    try:
        request_instance = Requests.objects.get(request_id=pk)
    except Requests.DoesNotExist:
        return Response({'error': 'неверный requist'}, status=404)
    request_instance_status = get_object_or_404(Requests, pk=pk)

    if request_instance.status == 'удален':
        return Response({'error': 'у заявки статус удален'}, status=404)
    elif request_instance.status == 'завершен':
        return Response({'error': 'заявка завершена'}, status=404)
    elif request_instance.status == 'отменен':
        return Response({'error': 'заявка отменена'}, status=404)
    elif request_instance.status == 'введён':
        return Response({'error': 'у заявки статус введён'}, status=404)
        

    # Define the fields you want to update
    fields_to_update = ['formation_date', 'completion_date', 'status']
    
    # Create an instance of the serializer with partial=True
    serializer = RequestsSerializer(request_instance, data=request.data, partial=True)

    # Filter the fields you want to update
    filtered_data = {key: request.data[key] for key in fields_to_update if key in request.data}

    # Check if 'status' is in the request data and not set to 'удален'
    if 'status' in request.data:
        new_status = request.data['status']
        old_status = request_instance.status
        allowed_statuses = {'завершен', 'отменен'}

        if new_status not in allowed_statuses:
            return Response({("доступные статусы: 'завершен', 'отменен'")}, status=400)
        
        # Check if the new status is 'удален' or if it's the same as the existing status
        if new_status == 'удален':
            return Response({'error': 'удалять может только user'}, status=400)
        
        if new_status == 'в работе':
            return Response({'error': 'на статус в работе может переводить только user'}, status=400)

    if serializer.is_valid():
        serializer.update(request_instance, filtered_data)  # Use update instead of save
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)
    

@api_view(['PUT'])
def requestsUser_put(request, pk, format=None):

    try:
        request_instance = Requests.objects.get(request_id=pk)
    except Requests.DoesNotExist:
        return Response({'error': 'неверный requist'}, status=404)
    request_instance_status = get_object_or_404(Requests, pk=pk)

    if request_instance.status != 'введен':
        return Response({"error": f"У заявки должен быть статус 'введен', сейчас статус: {request_instance.status}"}, status=404)
        
    # Define the fields you want to update
    fields_to_update = ['status']
    
    # Create an instance of the serializer with partial=True
    serializer = RequestsSerializer(request_instance, data=request.data, partial=True)

    # Filter the fields you want to update
    filtered_data = {key: request.data[key] for key in fields_to_update if key in request.data}

    # Check if 'status' is in the request data and not set to 'удален'
    if 'status' in request.data:
        new_status = request.data['status']
        old_status = request_instance.status
        allowed_statuses = {'в работе'}

        if new_status not in allowed_statuses:
            return Response({("доступные статусы: 'в работе'")}, status=400)

        if new_status != 'в работе':
            return Response({'error': 'изменять на другие статусы может только модератор'}, status=400)

    if serializer.is_valid():
        serializer.update(request_instance, filtered_data)  # Use update instead of save
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)
     



# логическое удаление. удалить введенную заявку юзер: (был статус введен -> сделать удален) админ: если введен менять на другие статусы

@api_view(['DELETE'])
def user_requests_delete(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    serializer = RequestsSerializer(request_instance, data=request.data)
    if serializer.is_valid():
        new_status = serializer.validated_data.get('status')
        if  request_instance.status == 'введен' and (new_status == 'удален' or new_status == 'введен'):
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"message": "доступные статусы: 'удален' 'введен'."}, status=status.HTTP_403_FORBIDDEN)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    
#м-м
@api_view(['GET'])
def get_all_request_services(request, format=None):
    request_services = RequestService.objects.all()
    serializer = RequestServiceSerializer(request_services, many=True)
    return Response(serializer.data)

    
@api_view(['PUT'])
def mm_put(request, request_id, chemistry_product_id):
    try:
        # Attempt to get the existing record
        request_service = RequestService.objects.get(
            request_id=request_id,
            chemistry_product_id=chemistry_product_id
        )
    except RequestService.DoesNotExist:
        return Response({"error": "не удалось найти запись. проверьте id"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = RequestServiceSerializer(request_service, data=request.data)
        if serializer.is_valid():
            # Delete the existing record
            request_service.delete()

            # Create a new record with the updated quantity
            serializer.save(request_id=request_id, chemistry_product_id=chemistry_product_id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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