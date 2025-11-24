# gestion/admin.py

from django.contrib import admin
import datetime
from .models import Bombero, Guardia, Emergencia


@admin.register(Bombero)
class BomberoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'rut', 'rol', 'user')
	search_fields = ('nombre', 'rut', 'user__username', 'user__email')
	list_filter = ('rol',)
	ordering = ('nombre',)


if hasattr(Emergencia, 'asistentes'):
	class EmergenciaInline(admin.TabularInline):
		model = Emergencia.asistentes.through
		extra = 0


@admin.register(Guardia)
class GuardiaAdmin(admin.ModelAdmin):
	list_display = ('fecha', 'hora_inicio', 'hora_fin', 'bombero', 'tipo', 'lugar', 'herramientas', 'apoyo_externo')
	list_filter = ('tipo', 'fecha', 'bombero__rol')
	search_fields = ('bombero__nombre', 'bombero__rut', 'lugar', 'herramientas', 'apoyo_externo')
	date_hierarchy = 'fecha'
	ordering = ('-fecha', 'bombero')
	list_editable = ('hora_inicio', 'hora_fin', 'tipo')
	autocomplete_fields = ('bombero',)
	fields = ('bombero', 'fecha', ('hora_inicio', 'hora_fin'), 'tipo', 'lugar', 'herramientas', 'apoyo_externo')
	actions = ['duplicate_guardias']

	def duplicate_guardias(self, request, queryset):
		"""Crea duplicados de las guardias seleccionadas desplazadas un día hacia adelante.
		Útil para generar datos de prueba rápidamente."""
		created = 0
		for g in queryset:
			new_date = g.fecha + datetime.timedelta(days=1)
			Guardia.objects.create(
				bombero=g.bombero,
				fecha=new_date,
				tipo=g.tipo,
				hora_inicio=g.hora_inicio,
				hora_fin=g.hora_fin,
				lugar=g.lugar,
				herramientas=g.herramientas,
				apoyo_externo=g.apoyo_externo
			)
			created += 1
		self.message_user(request, f"{created} guardia(s) duplicada(s) creada(s) con fecha desplazada +1 día.")
	duplicate_guardias.short_description = 'Duplicar guardias seleccionadas (+1 día)'


@admin.register(Emergencia)
class EmergenciaAdmin(admin.ModelAdmin):
	list_display = ('tipo', 'direccion', 'lugar', 'fecha_hora', 'herramientas', 'apoyo_externo')
	search_fields = ('tipo', 'direccion', 'lugar', 'herramientas', 'apoyo_externo')
	list_filter = ('tipo',)
	date_hierarchy = 'fecha_hora'
	filter_horizontal = ('asistentes',)
	# fecha_hora es auto_now_add en el modelo (no editable) — mostrar como read-only en admin
	readonly_fields = ('fecha_hora',)
	fields = ('vipercode', 'tipo', 'direccion', 'lugar', 'observaciones', 'asistentes', 'herramientas', 'apoyo_externo')

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.select_related()
