import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomberos_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from gestion.models import Bombero

username = 'NicolasA'
u = User.objects.filter(username=username).first()
out = []
out.append('USER_FOUND:' + str(bool(u)))
if u:
    out.append('USERNAME:' + str(u.username))
    out.append('is_superuser:' + str(u.is_superuser))
    out.append('is_staff:' + str(u.is_staff))
    out.append('email:' + str(u.email))
else:
    out.append('User not found')

out.append('HAS_BOMBERO:' + str(Bombero.objects.filter(user__username=username).exists()))

with open(os.path.join(os.path.dirname(__file__), 'check_nicolas_out.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out))

print('WROTE OUTPUT')
