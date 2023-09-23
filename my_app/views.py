from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.db import connection
from . import models


def GetOrder(request, id):
    data_by_id = models.ChemistryEquipment.objects.filter(chemistry_product_id=id).first()

    return render(request, 'order.html', {
        'modeling': data_by_id
    })

def SendText(request):
    input_text = request.GET.get('value', '') 

    matching_models = [model for model in models.ChemistryEquipment.objects.all() if
                       input_text.lower() in model.type.lower() or
                       input_text.lower() in model.price.lower()]

    if not matching_models:
        matching_models = models.ChemistryEquipment.objects.all()

    if not input_text:
        input_text = ""

    return render(request, 'orders.html', {
        'init_data': {'modeling': matching_models},
        'search_value': input_text
    })

def hide_model(id):
    try:
        with connection.cursor() as cursor:
    
            quarry = f"UPDATE chemistry_equipment SET status = 'удален' WHERE chemistry_product_id = %s"
            cursor.execute(quarry, [id])
            connection.commit()
            
            return True
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return False

def update_chemistry_equipment_status(request, id):
    if not hide_model(id):
        pass
    return redirect(reverse('order_url'))
