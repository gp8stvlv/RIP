from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models import Q
from . import models
from app.serializers import RequestsSerializer
from app.models import Requests
from app.serializers import ChemistryEquipmentSerializer
from app.models import ChemistryEquipment
from rest_framework.decorators import api_view

#химическое оборудование
@api_view(['Get'])
def chemistryEquipment_getAll(request, format=None):
    input_text = request.GET.get('value', '') 

    matching_models = models.ChemistryEquipment.objects.filter(status='действует').order_by("chemistry_product_id") #аналог (через ОРМ) SELECT * FROM chemistry_equipment WHERE status == 'действует'; 

    if input_text:
        matching_models = matching_models.filter(
        Q(type__icontains=input_text) | Q(price__icontains=input_text), #name__contains для частичного совпадения с введенным текстом.
        status='действует'
    )
    serializer = ChemistryEquipmentSerializer(matching_models, many=True)
    return Response(serializer.data)

@api_view(['Post'])
def chemistryEquipment_post(request, format=None):    
    serializer = ChemistryEquipmentSerializer(data=request.data)
    if serializer.is_valid():

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Get'])
def chemistryEquipment_getByID(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    if request.method == 'GET':
        serializer = ChemistryEquipmentSerializer(equipment)
        return Response(serializer.data)

@api_view(['Put'])
def chemistryEquipment_put(request, pk, format=None):
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    serializer = ChemistryEquipmentSerializer(equipment, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['Delete'])
def chemistryEquipment_delete(request, pk, format=None):    
    equipment = get_object_or_404(ChemistryEquipment, pk=pk)
    equipment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)










#заявки
#  проверить!!!! 
@api_view(['GET'])
def requests_getAll(request, format=None):
    # Получаем параметры запроса (query parameters)
    sort_by_status = request.GET.get('sort_by_status')
    sort_by_formation_date = request.GET.get('sort_by_formation_date')

    # Создаем объект запросов
    requests = Requests.objects.all()

    # Применяем сортировку на основе параметров
    if sort_by_status:
        requests = requests.order_by('status' if sort_by_status == 'asc' else '-status')

    if sort_by_formation_date:
        requests = requests.order_by('formation_date' if sort_by_formation_date == 'asc' else '-formation_date')

    serializer = RequestsSerializer(requests, many=True)
    return Response(serializer.data)

# @api_view(['GET'])
# def requests_getAll(request, format=None):
#     # Получаем параметры запроса (query parameters)
#     sort_by_status = request.GET.get('sort_by_status')
#     sort_by_formation_date = request.GET.get('sort_by_formation_date')

#     # Создаем объект запросов
#     requests = Requests.objects.all()

#     # Применяем сортировку на основе параметров
#     if sort_by_status:
#         requests = requests.order_by('status' if sort_by_status == 'asc' else '-status')

#     if sort_by_formation_date:
#         requests = requests.order_by('formation_date' if sort_by_formation_date == 'asc' else '-formation_date')

#     serializer = RequestsSerializer(requests, many=True)
#     return Response(serializer.data)


@api_view(['Post'])
def requests_post(request, format=None):    
    serializer = RequestsSerializer(data=request.data)
    print(serializer)
    if serializer.is_valid():
        # status_value = serializer.validated_data.get('user_id')
        # print(serializer.validated_data)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Get'])
def requests_getByID(request, pk, format=None):
    request = get_object_or_404(Requests, pk=pk)
    if request.method == 'GET':
        serializer = RequestsSerializer(request)
        return Response(serializer.data)

# @api_view(['Put'])
# def requests_put(request, pk, format=None):
#     request = get_object_or_404(Requests, pk=pk)
#     serializer = RequestsSerializer(request, data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Put'])
def requests_put(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    serializer = RequestsSerializer(request_instance, data=request.data)
    if serializer.is_valid():
        status_value = serializer.validated_data.get('user_id')
        print(status_value)
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# логическое удаление
@api_view(['Delete'])
def requests_delete(request, pk, format=None): 
    request = get_object_or_404(Requests, pk=pk)
    request.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)