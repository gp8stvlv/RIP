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

MODERATOR_USER_ID = 1  # Идентификатор модератора (замените на фактический идентификатор)
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

@api_view(['POST'])
def chemistryEquipment_post(application, pk, quantity, format=None):  
    draft_application = models.Requests.objects.filter(status='введен').first()
    if draft_application:
        print("draft_application", draft_application)
        if pk:
            try:
                chemistry_product = models.ChemistryEquipment.objects.get(chemistry_product_id=pk)
            except models.ChemistryEquipment.DoesNotExist:
                return Response({'error': 'chemistry_product not found'}, status=status.HTTP_404_NOT_FOUND)

            RequestService.objects.create(chemistry_product=chemistry_product, application=draft_application, quantity=quantity)

        return Response({'message': 'chemistry_product added to the existing draft application'}, status=status.HTTP_200_OK)
    else:
        return

#изменение оборудования не работает изменение картинки!!!
@api_view(['Put'])
def chemistryEquipment_put(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    serializer = ChemistryEquipmentSerializer(equipment, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#удаление оборудования
@api_view(['Delete'])
def chemistryEquipment_delete(request, pk, format=None):    
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    equipment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

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




@api_view(['GET'])
def requests_getAll(request, format=None):
    created_at = request.GET.get('created_at', None)
    status = request.GET.get('status', None)

    queryset = Requests.objects.all()

    if created_at:
        queryset = queryset.filter(created_at=created_at)

    if status:
        queryset = queryset.filter(status=status)

    matching_RequestService_requests = models.RequestService.objects.filter(request_id__in=queryset.values_list('request_id', flat=True))
    chemistry_product_ids = matching_RequestService_requests.values_list('chemistry_product_id', flat=True)
    print(chemistry_product_ids)

    matching_equipment_requests = models.ChemistryEquipment.objects.filter(chemistry_product_id__in=chemistry_product_ids)
    print(matching_equipment_requests)

    requests_serializer = RequestsSerializer(queryset, many=True)
    equipment_serializer = ChemistryEquipmentSerializer(matching_equipment_requests, many=True)

    # Combine the serialized data into a single response
    response_data = {
        'requests': requests_serializer.data,
        'chemistry_equipment': equipment_serializer.data
    }

    return Response(response_data)






# Не делать POST заявки?? при создании заявки проверяем, что статус - введен
@api_view(['POST'])
def requests_post(request, format=None):
    serializer = RequestsSerializer(data=request.data)
    
    if request.data.get('status') != 'введен': 
        return Response("при создании статус заявки должен быть - введен")
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        # 'chemistry_equipment': [
        #     {
        #         'equipment': equipment,
        #         'production_count': equipment_count_dict[equipment['chemistry_product_id']]
        #     } for equipment in equipment_serializer.data
        # ] if matching_equipment_requests else None
    }

    return Response(response_data)


@api_view(['PUT'])
def requests_put(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    serializer = RequestsSerializer(request_instance, data=request.data)
    
    if serializer.is_valid():

        new_status = serializer.validated_data.get('status')
        current_role = get_role_by_Requests(request_instance)
        print("старый статус:", request_instance.status, "новый статус:", new_status, "текущая роль", current_role)
        if current_role == 'user' and request_instance.status == 'введен' and (new_status == 'удален' or new_status == 'введен'):
            serializer.save()
            return Response(serializer.data)
        elif current_role == 'moderator' and request_instance.status != 'удален' and new_status != 'удален':
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"message": "Недостаточно прав для изменения статуса заявки."}, status=status.HTTP_403_FORBIDDEN)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# логическое удаление. удалить введенную заявку  (был статус введен -> сделать удален)

@api_view(['DELETE'])
def requests_delete(request, pk, format=None):
    request_obj = get_object_or_404(Requests, pk=pk)
    request_instance = get_object_or_404(Requests, pk=pk)
    current_role = get_role_by_Requests(request_instance)
    if request_obj.status == 'введен':
        request_obj.status = 'удален'
        request_obj.save()
        return Response({'message': 'заявка успешно удаленена (введен -> удален)'}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'message': 'заявку не удалось удалить'}, status=status.HTTP_400_BAD_REQUEST)
    
#м-м

@api_view(['GET'])
def get_all_request_services(request, format=None):
    request_services = RequestService.objects.all()
    serializer = RequestServiceSerializer(request_services, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
def mm_put(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    serializer = RequestServiceSerializer(request_instance, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

