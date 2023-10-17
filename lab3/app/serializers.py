from app.models import ChemistryEquipment
from app.models import Requests
from app.models import RequestService
from rest_framework import serializers


class ChemistryEquipmentSerializer(serializers.ModelSerializer):
    class Meta: #меняет свойства основного класса
        # Модель, которую мы сериализуем
        model = ChemistryEquipment
        # Поля, которые мы сериализуем
        fields = ["chemistry_product_id",
                  "type",
                  "description",
                  "image_url",
                  "price",
                  "status"]
        
# class RequestsSerializer(serializers.ModelSerializer):
#     class Meta: #меняет свойства основного класса
#         # Модель, которую мы сериализуем
#         model = Requests
        
#         fields = ["request_id",
#                   "user_id",
#                   "status",
#                   "created_at",
#                   "formation_date",
#                   "completion_date",
#                   "moderator_id"]
        
class RequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = [
            "request_id",
            "user",
            "status",
            "created_at",
            "formation_date",
            "completion_date",
            "moderator"
        ]

        
class RequestServiceSerializer(serializers.ModelSerializer):
    class Meta: #меняет свойства основного класса
        # Модель, которую мы сериализуем
        model = Requests
        fields = ["request_id",
                  "chemistry_product_id",
                  "production_count"]