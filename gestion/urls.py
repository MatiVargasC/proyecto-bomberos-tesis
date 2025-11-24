from django.urls import path
from gestion import views

urlpatterns = [
    # La página principal (ej: http://127.0.0.1:8000/)
    path('', views.index, name='index'), 
    
    # La página de historial (ej: http://127.0.0.1:8000/historial/)
    path('historial/', views.historial, name='historial'),
    path('guardia/<int:pk>/editar/', views.editar_guardia, name='editar_guardia'),
    path('guardia/<int:pk>/detalle/', views.detalle_guardia, name='detalle_guardia'),
        # URL para Reportes Avanzados (Nuevo)
    path('reportes/', views.reportes_avanzados_view, name='reportes_avanzados'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('asignar-guardias/', views.asignar_guardias, name='asignar_guardias'),
    path('personal-operativo/', views.personal_operativo_view, name='personal_operativo'),
    # Gestión de personal (admin/staff)
    path('gestion-personal/', views.gestion_personal_view, name='gestion_personal'),
    # Crear nuevo bombero
    path('gestion-personal/nuevo/', views.nuevo_bombero_view, name='nuevo_bombero'),
]