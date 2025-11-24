from django.contrib import admin
from django.urls import path, include
from gestion import views as gestion_views


urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de login/logout
    path('accounts/', include('django.contrib.auth.urls')),
    # Registro de usuarios
    path('accounts/register/', gestion_views.register_view, name='register'),
    # Incluye las URLs de la app 'gestion' en la raíz
    path('', include('gestion.urls')),

    path('sincronizar-viper/', gestion_views.sincronizar_viper, name='sincronizar_viper'),
]
