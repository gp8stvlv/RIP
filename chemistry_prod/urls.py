"""
URL configuration for chemistry_prod project.

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
from django.urls import path
from chemistry_prod.views import GetOrders
from chemistry_prod.views import GetOrder
from chemistry_prod.views import GetBasket
from chemistry_prod.views import SendText

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SendText, name='order_url'),
    path('order/<int:id>/', GetOrder, name='order_url'),     #параметр name='order_url' - передаем в orders.html <a href="{% url 'order_url' model.id %}"
    path('basket', GetBasket)
]