from django.shortcuts import render
from datetime import date
# controller
# mvt - view = contoller
# Оборудование для химических лабораторий.
# Услуги - лабораторное оборудование, заявки - заявки на приобретение

data_modeling = {
    'modeling': [
        {
            'id': 0,
            'type': 'Спектрофотометр Nano-500',
            'description': 'Спектрофотометр и флуориметр в одном приборе. Измерения в малых объемах в диапазоне длин волн 200 – 800 нм.',
            'image_url': '../static/images/spektrofotometr-nano-500.png',
            'price': '9999₽'
            
        },
        {
            'id': 1,
            'type': 'Автоклав с вертикальной загрузкой MVS-83, объем 75 литров',
            'description': 'Паровой стерилизатор с вертикальной загрузкой с температурой стерилизации 115 - 135°C.',
            'image_url': '../static/images/avtoklav-s-vertikalnoy-zagruzkoy-mvs-83-obem-75-litrov.jpg',
            'price': '8799₽'
        },
        {
            'id': 2,
            'type': 'Низкотемпературный морозильник MDF-U880VH',
            'description': 'Вертикальный низкотемпературный морозильник MDF-U880VH объемом 861 л с температурой от -50°С до -86°С.',
            'image_url': '../static/images/nizkotemperaturnyy-morozilnik-mdf-u880vh.jpg',
            'price': '2599₽'
        },
        {
            'id': 3,
            'type': 'Гомогенизатор лабораторный Bioprep-24R с функцией охлаждения на 24 образца',
            'description': 'Гомогенизатор с функцией активного охлаждения на 24 образца объемом 2 мл или на 12 образцов объемом 5 мл.',
            'image_url': '../static/images/gomogenizator-laboratornyy-bioprep-24r-s-funktsiey-okhlazhdeniya-na-24-obraztsa.jpg',
            'price': '1799₽'
        },
        {
            'id': 4,
            'type': 'Планшетный спектрофотометр FlexA-200HT',
            'description': 'Планшетный ридер и кюветный спектрофотометр для видимой и УФ областей спектра.',
            'image_url': '../static/images/planshetnyy-spektrofotometr-flexa-200ht.jpg',
            'price': '5790₽'
        },
        {
            'id': 5,
            'type': 'Микроцентрифуга M1324',
            'description': 'Микроцентрифуга со скоростью вращения до 15000 об/мин, с возможностью работы со стандартными пробирками на 1,5/2 мл и ПЦР-стрипами.',
            'image_url': '../static/images/fluorimetr-fluo-800-siniy-i-krasnyy-kanaly.jpg',
            'price': '1899₽'
        }
    ]
}

def GetEquipments(request):
    return render(request, 'orders.html', {
        'init_data' : data_modeling
    })


def GetEquipment(request, id):
    data_by_id = data_modeling.get('modeling')[id]
    return render(request, 'order.html', {
        'modeling': data_by_id
    })

def SendText(request):
    input_text = request.GET.get('value', '') 

    matching_models = [model for model in data_modeling['modeling'] if
                       input_text.lower() in model['type'].lower() or
                       input_text.lower() in model['price'].lower()]

    if not matching_models:
        matching_models = data_modeling['modeling']

    if (not input_text):
        input_text = ""
    return render(request, 'orders.html', {
        'init_data': {'modeling': matching_models},
        'search_value': input_text
    })