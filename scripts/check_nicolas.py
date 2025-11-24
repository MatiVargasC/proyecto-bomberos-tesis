import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomberos_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from gestion.models import Bombero

username = 'NicolasA'
u = User.objects.filter(username=username).first()
print('USER_FOUND:', bool(u))
if u:
    print('USERNAME:', u.username)
    print('is_superuser:', u.is_superuser)
    print('is_staff:', u.is_staff)
    print('email:', u.email)
else:
    print('User not found')

print('HAS_BOMBERO:', Bombero.objects.filter(user__username=username).exists())
