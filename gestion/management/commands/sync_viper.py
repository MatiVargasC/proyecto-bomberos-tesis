# gestion/management/commands/sync_viper.py
from django.core.management.base import BaseCommand
from gestion.models import Emergencia, Bombero
from django.utils import timezone

class Command(BaseCommand):
    help = "Simula la sincronización de emergencias desde VIPER (modo demostración)"

    def handle(self, *args, **options):
        # Datos reales de claves radiales de Bomberos Rancagua (públicas)
        fake_emergencias = [
            {
                "vipercode": "Q-2025-0891",
                "tipo": "Rescate Vehicular con Persona Atrapada",
                "direccion": "Ruta 5 Sur km 87, sector Machalí",
            },
            {
                "vipercode": "I-2025-0456",
                "tipo": "Incendio Estructural en Vivienda",
                "direccion": "Calle Cáceres 1234, Rancagua",
            },
            {
                "vipercode": "M-2025-112",
                "tipo": "Traslado de Paciente Crítico",
                "direccion": "Hospital Regional Rancagua",
            },
            {
                "vipercode": "H-2025-003",
                "tipo": "Derrame de Sustancia Peligrosa",
                "direccion": "Av. España con Av. Kennedy",
            },
        ]

        creadas = 0
        for dato in fake_emergencias:
            # Evitamos duplicados por código VIPER
            if not Emergencia.objects.filter(vipercode=dato["vipercode"]).exists():
                Emergencia.objects.create(
                    vipercode=dato["vipercode"],
                    tipo=dato["tipo"],
                    direccion=dato["direccion"],
                    fecha_hora=timezone.now(),
                    origen="VIPER",
                    observaciones="Sincronizado automáticamente desde VIPER (modo simulación para tesis)",
                )
                creadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"Sincronización VIPER completada → {creadas} emergencias nuevas creadas.")
        )