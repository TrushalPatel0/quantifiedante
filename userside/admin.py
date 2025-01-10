from django.contrib import admin

# Register your models here.
from userside.models import *

admin.site.register(User)
admin.site.register(User_Preference)
admin.site.register(Access_Token)

