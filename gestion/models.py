from django.db import models
from django.contrib.auth.models import User # Importamos el modelo de Usuarios de Django
from django.conf import settings
from django.utils import timezone

class AuditoriaModelo(models.Model):
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_creado",
        verbose_name="Creado por"
    )
    creado_el = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_modificado",
        verbose_name="Modificado por"
    )
    modificado_el = models.DateTimeField(auto_now=True, verbose_name="Modificado el")

    class Meta:
        abstract = True


class Bombero(models.Model):
    # Conectamos cada Bombero con una cuenta de Usuario
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # El resto de tus campos
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    rol = models.CharField(max_length=20, choices=[('Bombero', 'Bombero'), ('Jefe de Guardia', 'Jefe de Guardia'), ('Admin', 'Administrador')])
    
    def __str__(self):
        # Mostramos el nombre de usuario de la cuenta enlazada
        return self.user.username

class Guardia(AuditoriaModelo):
    # Se enlaza con el modelo Bombero
    bombero = models.ForeignKey(Bombero, on_delete=models.CASCADE, related_name="guardias")
    fecha = models.DateField(verbose_name="Fecha de la guardia")
    tipo = models.CharField(max_length=20, default="Nocturna", verbose_name="Tipo de Guardia")
    
    # Hora de inicio y fin (como en tu diagrama de 'Asistencias')
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    
    # Campos adicionales para reporting (pueden permanecer vacíos si no se registran)
    herramientas = models.CharField(max_length=255, null=True, blank=True, verbose_name="Herramientas utilizadas")
    apoyo_externo = models.CharField(max_length=255, null=True, blank=True, verbose_name="Apoyo externo (Carabineros/SAMU/otros)")
    lugar = models.CharField(max_length=200, null=True, blank=True, verbose_name="Lugar o sector")

    def __str__(self):
        return f"Guardia de {self.bombero.user.username} - {self.fecha}"

class Emergencia(AuditoriaModelo):
    # (Este modelo sigue igual que antes)
    vipercode = models.CharField(max_length=50, verbose_name="Código VIPER", null=True, blank=True)
    tipo = models.CharField(max_length=100, verbose_name="Tipo de Emergencia (Clave)")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(null=True, blank=True)
    
    asistentes = models.ManyToManyField(Bombero, related_name="emergencias_atendidas")

    # Campos adicionales que ayudan al análisis y que se usaron en Guardias
    herramientas = models.CharField(max_length=255, null=True, blank=True, verbose_name="Herramientas utilizadas")
    apoyo_externo = models.CharField(max_length=255, null=True, blank=True, verbose_name="Apoyo externo (Carabineros/SAMU/otros)")
    lugar = models.CharField(max_length=200, null=True, blank=True, verbose_name="Lugar o sector")

    origen = models.CharField(
        max_length=20,
        choices=[('MANUAL', 'Registro Manual'), ('VIPER', 'Sincronizado desde VIPER')],
        default='MANUAL',
        verbose_name="Origen de la emergencia"
    )

    def __str__(self):
        return f"{self.tipo} - {self.direccion}"
    
    class Meta:
        verbose_name_plural = "Emergencias"


class MaterialMayor(AuditoriaModelo):
    """Registra el despacho de un vehículo/material mayor asociado a una Guardia.
    Se usan campos de tiempo para llegada al lugar, retiro y llegada al cuartel (6-3, 6-9, 6-10).
    """
    guardia = models.ForeignKey(Guardia, on_delete=models.CASCADE, related_name='materiales')
    vehiculo = models.CharField(max_length=50)
    llegada = models.DateTimeField(null=True, blank=True)
    retiro = models.DateTimeField(null=True, blank=True)
    llegada_cuartel = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehiculo} - {self.guardia}"




