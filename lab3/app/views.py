from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models import Q
from . import models
from rest_framework.decorators import api_view
from functools import wraps
from app.serializers import UsersSerializer, RequestsSerializer, ChemistryEquipmentSerializer, RequestServiceSerializer
from app.models import Users, Requests, ChemistryEquipment, RequestService

MODERATOR_USER_ID = 1  # Идентификатор модератора (замените на фактический идентификатор)

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

"""
--     введен,
--     в работе,
--     завершен,
--     отменен,
--     удален.
"""



# #  проверить!!!! 
# нужна сортировка 
@api_view(['GET'])
def requests_getAll(request, format=None):
    requests = Requests.objects.all()
    user_role = request.user
    print("user_role", user_role)
    serializer = RequestsSerializer(requests, many=True)
    return Response(serializer.data)


@api_view(['Post'])
def requests_post(request, format=None):    
    serializer = RequestsSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def requests_getByID(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    if request.method == 'GET':
        serializer = RequestsSerializer(request_instance)
        return Response(serializer.data)
    
# возвращает текущую роль
def get_role_by_Requests(request_instance): #пример вызова request_instance = get_object_or_404(Requests, pk=pk) get_role_by_Requests(request_instance)
    user_id = request_instance.user_id
    user = Users.objects.get(user_id = user_id)
    user_data = UsersSerializer(user).data
    user_role = user_data['role']
    print(user_role)

@api_view(['PUT'])
def requests_put(request, pk, format=None):
    request_instance = get_object_or_404(Requests, pk=pk)
    serializer = RequestsSerializer(request_instance, data=request.data)
    
    if serializer.is_valid():
        new_status = serializer.validated_data.get('status')
        # Проверяем, имеет ли пользователь право на изменение статуса
        current_role = get_role_by_Requests(request_instance)
        if current_role == 'user' and request_instance.status == 'введен' and new_status == 'удален':
            serializer.save()
            return Response(serializer.data)
        elif current_role == 'moderator' and request_instance.status != 'удален' and new_status != 'удален':
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"message": "Недостаточно прав для изменения статуса заявки."}, status=status.HTTP_403_FORBIDDEN)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['Put'])
# def requests_put(request, pk, format=None):
#     request_instance = get_object_or_404(Requests, pk=pk)
#     serializer = RequestsSerializer(request_instance, data=request.data)
#     if serializer.is_valid():
#         status_value = serializer.validated_data.get('user_id')
#         print(status_value)
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# логическое удаление
@api_view(['Delete'])
def requests_delete(request, pk, format=None): 
    request = get_object_or_404(Requests, pk=pk)
    request.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)