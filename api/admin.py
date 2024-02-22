from django.contrib import admin

from api.models import *

# Register your models here.
admin.site.register(Letter)
admin.site.register(Trainee)
admin.site.register(User)
admin.site.register(TraineeToUser)
