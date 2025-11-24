import os
import sys
# Ensure project root is on sys.path so 'bomberos_project' package is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomberos_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from gestion.models import Bombero

username = 'NicolasA'
u = User.objects.filter(username=username).first()
if not u:
    print('USER_NOT_FOUND')
    raise SystemExit(0)

print('USERNAME', u.username)
print('is_superuser', u.is_superuser)
print('is_staff', u.is_staff)

if Bombero.objects.filter(user=u).exists():
    print('BOMBERO_EXISTS')
else:
    rut = 'AUTO-'+u.username+'-'+str(u.id)
    nombre = (u.first_name + ' ' + u.last_name).strip() or u.username
    bm = Bombero.objects.create(user=u, rut=rut, nombre=nombre, rol='Admin')
    print('BOMBERO_CREATED', bm.id, rut, nombre)
