from app.models import ChemistryEquipment
from app.models import Requests
from app.models import RequestService
from app.models import Users
from rest_framework import serializers


class UsersSerializer(serializers.ModelSerializer):
    class Meta: #меняет свойства основного класса
        # Модель, которую мы сериализуем
        model = Users
        # Поля, которые мы сериализуем
        fields = ["user_id",
                  "username",
                  "password",
                  "email",
                  "role"]
        
class ChemistryEquipmentSerializer(serializers.ModelSerializer):
    image_url_after_serializer = serializers.SerializerMethodField()

    class Meta:
        model = ChemistryEquipment
        fields = ["chemistry_product_id", "type", "description", "price", "status", "image_url_after_serializer"]
    def get_image_url_after_serializer(self, obj):
        image_url = obj.image_url

        if image_url:
            custom_value = f"http://localhost:9000/chemistry/{image_url[17:]}"
            return custom_value
        else:
            return None  # Or any default value you prefer
        
    # def get_image_url_after_serializer(self, obj):
    #     image_url = obj.image_url
    #     custom_value = f"http://localhost:9000/chemistry/{image_url[17:]}"
    #     return custom_value
    


class RequestServiceSerializer(serializers.ModelSerializer):
    class Meta: #меняет свойства основного класса
        # Модель, которую мы сериализуем
        model = RequestService
        fields = ["request_id",
                  "chemistry_product_id",
                  "production_count"]
        
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