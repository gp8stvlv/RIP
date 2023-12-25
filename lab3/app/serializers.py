from app.models import ChemistryEquipment
from app.models import Requests
from app.models import RequestService
from app.models import Users
from rest_framework import serializers
from django.utils import timezone
from minio import Minio

client = Minio(
    endpoint="192.168.1.70:9000",
    access_key='minio',
    secret_key='minio124',
    secure=False
)

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
        fields = ["chemistry_product_id", "type", "description", "image_url", "price", "status", "image_url_after_serializer"]

    def get_image_url_after_serializer(self, obj):
        image_url = obj.image_url

        # print(f"Original image_url: {image_url}")

        if image_url:
            # Split the original URL by '/' and take the last part
            filename = image_url.split('/')[-1]
            # Construct the modified URL
            #195.19.58.23:9000
            custom_value = f"http://localhost:9000/chemistry/{filename}"
            # print(f"Custom image_url: {custom_value}")
            return custom_value
        else:
            # Provide a default image URL if image_url is None
            default_image_url = "http://localhost:9000/chemistry/default-image.jpg"
            # print(f"Default image_url: {default_image_url}")
            return default_image_url
    
    def create(self, validated_data):
        # Extract the image from the validated data
        image_file = validated_data.pop('image', None)

        # Call the parent create method to save the other fields
        instance = super().create(validated_data)

        # Upload the image to Minio if provided
        if image_file:
            try:
                filename = f"photo_new_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg"

                # Use Minio client to upload the file
                client.put_object(
                    bucket_name='chemistry',
                    object_name=filename,
                    data=image_file,
                    length=image_file.size,
                    content_type='image/jpeg',
                )

                # Update the instance with the modified image URL
                instance.image_url = f"http://localhost:9000/chemistry/{filename}"
                instance.save()

            except Exception as e:
                print(f'Error uploading image: {str(e)}')
                # Optionally, you can raise an exception or return an error response here

        return instance



        
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