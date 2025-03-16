"""
URL configuration for docweberserver project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from main.views import default
from main.views import db_update_request
from main.views import db_test, db_dump, udp_bcast, speed_test, lte_connected

urlpatterns = [
    path('',               default,                  name='default'),
    path('dbupdate',       db_update_request,        name='db_update_request'),
    path('dbtest',         db_test,                  name='db_test'),
    path('dbdump',         db_dump,                  name='db_dump'),
    path('udp_bcast',      udp_bcast,                name='udp_bcast'),
    path('speedtest',      speed_test,               name='speedtest'),
    path('lte_connected',  lte_connected,            name='lte_connected'),
    path('admin/', admin.site.urls),

]
