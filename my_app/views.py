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

    matching_models = [model for model in models.ChemistryEquipment.objects.exclude(status='удален') if #.exclude(status='удален') используется для фильтрации записей, исключая те, у которых поле status имеет значение 'удален'
                       input_text.lower() in model.type.lower() or
                       input_text.lower() in model.price.lower()]

    if not matching_models:
        matching_models = models.ChemistryEquipment.objects.exclude(status='удален')  #аналог (через ОРМ) SELECT * FROM chemistry_equipment WHERE status <> 'удален'; 

    if not input_text:
        input_text = ""

    return render(request, 'orders.html', {
        'init_data': {'modeling': matching_models},
        'search_value': input_text
    })

def hide_model(id):
    try:
        with connection.cursor() as cursor:
    
            query = f"UPDATE chemistry_equipment SET status = 'удален' WHERE chemistry_product_id = %s"
            cursor.execute(query, [id])
            connection.commit()
            
            return True
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return False

def update_chemistry_equipment_status(request, id):
    hide_model(id)
    return redirect(reverse('order_url'))


#reverse('order_url'): Эта функция Django используется для генерации URL на основе имени URL-шаблона.
# В данном случае, она генерирует URL для представления, связанного с именем URL-шаблона 'order_url'. 
# Таким образом, эта часть кода получает URL, к которому должно быть выполнено перенаправление.

#redirect(...): Эта функция Django выполняет фактическое перенаправление пользователя на указанный URL.
#  Она принимает URL в качестве аргумента и отправляет HTTP-заголовок, который указывает браузеру пользователя перейти по этому URL.