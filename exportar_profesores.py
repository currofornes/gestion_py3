import os
import sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion.settings")
django.setup()

from django.contrib.auth.models import User,Group
user = User.objects.create_user(username='josedom',
                                 email='josedom24@mail.com',
                                 password='asdasd')
user.is_staff=True
user.groups.add(Group.objects.get(name="profesor").id)
user.save()