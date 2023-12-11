"""
URL configuration for lab3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path(r'equipment/', views.chemistryEquipment_getAll, name='chemistryEquipment_getAll'), #гет с фильтром всех записей ?price=8799&type=тикальной 
    path(r'equipment/post/', views.add_chemistryEquipment_post, name='add_chemistryEquipment_post'),
    path(r'equipment/chemistry_product_id/<int:chemistry_product_id>/post/', views.chemistryEquipment_post, name='chemistryEquipment_post'),
    # path(r'equipment/user_id/<int:user_id>/count/<int:production_count>/chemistry_product_id/<int:chemistry_product_id>/post/', views.chemistryEquipment_post, name='chemistryEquipment_post'),
    path(r'equipment/<int:pk>/', views.chemistryEquipment_getByID, name='chemistryEquipment_getByID'), #гет /id
    path(r'equipment/<int:pk>/put/', views.chemistryEquipment_put, name='chemistryEquipment_put'),
    path(r'equipment/<int:pk>/delete/', views.chemistryEquipment_delete, name='chemistryEquipment_delete'),

    path(r'request/', views.requests_getAll, name='requests_getAll'), # http://0.0.0.0:8000/request/?status=в работе&formation_date_from=2020-09-01&formation_date_to=2024-09-30
    # path(r'request/post/', views.requests_post, name='requests_post'),
    path(r'request/<int:pk>/', views.requests_getByID, name='requests_getByID'),
    path(r'request/moderator/<int:pk>/put/', views.requestsModerator_put, name='requestsModerator_put'),
    path(r'request/user/<int:pk>/put/', views.requestsUser_put, name='requestsUser_put'),
    path(r'request/<int:pk>/delete/', views.user_requests_delete, name='user_requests_delete'),

    # path(r'mm/request_id/<int:request_id>/chemistry_product_id/<int:chemistry_product_id>/count/<int:production_count>/put/', views.mm_put, name='m-m_put'),
    path(r'manyToMany/request_id/<int:request_id>/chemistry_product_id/<int:chemistry_product_id>/put/', views.mm_put, name='mm_put'),
    path(r'manyToMany/request_id/<int:request_id>/chemistry_product_id/<int:chemistry_product_id>/delete/', views.mm_delete, name='mm_delete'),

    
# данный метод не нужен!
    # path(r'manyToMany/', views.get_all_request_services, name='m-m_put'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]