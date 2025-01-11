"""quantifiedante URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from userside import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name=''),
    path('trading_view_signal_webhook_listener', views.trading_view_signal_webhook_listener, name='trading_view_signal_webhook_listener'),
    path('callback', views.callback, name='callback'),
    path('broker_login', views.broker_login, name='broker_login'),
    path('user_register/', views.user_register, name='user_register'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_forgot_password/', views.user_forgot_password, name='user_forgot_password'),
    path('user_change_password/', views.user_change_password, name='user_change_password'),
    path('tradovate_functionalities_data/', views.tradovate_functionalities_data, name='tradovate_functionalities_data'),
    path('trade_execution/', views.trade_execution, name='trade_execution'),
    path('trade_signal_update/', views.trade_signal_update, name='trade_signal_update'),
    
]
