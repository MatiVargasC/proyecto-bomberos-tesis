from django.core.management.base import BaseCommand, CommandError
import csv
import os
from django.utils.dateparse import parse_date, parse_time
from gestion.models import Bombero, Guardia
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
import unicodedata


class Command(BaseCommand):
    help = (
        'Import guardias desde un CSV o XLSX. Columnas soportadas: '
        'bombero_id,bombero_rut,bombero_username,fecha,hora_inicio,hora_fin,tipo,'
        'herramientas,apoyo_externo,lugar'
    )

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Ruta al archivo CSV o XLSX a importar')
        parser.add_argument('--dry-run', action='store_true', help='Validar sin guardar')
        parser.add_argument('--create-bombero', action='store_true', help='Crear Bombero (y User) si no existe')

    def handle(self, *args, **options):
        path = options['csvfile']
        dry = options['dry_run']
        create_bombero = options.get('create_bombero', False)

        created = 0
        skipped = 0
        errors = 0

        def get_val(r, key):
            # row may be dict with non-string values (from pandas); normalize
            v = r.get(key) if isinstance(r, dict) else None
            if v is None:
                return ''
            return str(v).strip()

        # Load rows from XLSX (pandas) or CSV
        rows = None
        if path.lower().endswith('.xlsx'):
            try:
                import pandas as pd
            except Exception:
                raise CommandError('Para importar .xlsx instala pandas y openpyxl: pip install pandas openpyxl')
            if not os.path.exists(path):
                cwd = os.getcwd()
                files = os.listdir(cwd)
                raise CommandError(f"Archivo no encontrado: {path}\nDirectorio actual: {cwd}\nArchivos en el directorio actual: {files}\n")
            df = pd.read_excel(path, engine='openpyxl')
            df.columns = [str(c) for c in df.columns]
            rows = df.fillna('').to_dict(orient='records')
        else:
            if not os.path.exists(path):
                cwd = os.getcwd()
                files = os.listdir(cwd)
                raise CommandError(f"Archivo no encontrado: {path}\nDirectorio actual: {cwd}\nArchivos en el directorio actual: {files}\n")
            fh = open(path, newline='', encoding='utf-8')
            reader = csv.DictReader(fh)

        with transaction.atomic():
            iterable = rows if rows is not None else list(reader)
            for i, row in enumerate(iterable, start=1):
                # Normalizar y validar fecha antes de crear usuarios
                fecha_raw = get_val(row, 'fecha')
                if not fecha_raw:
                    self.stdout.write(self.style.WARNING(f'Fila {i}: Fecha vacía. Omitido.'))
                    skipped += 1
                    continue

                # Intentamos varios formatos comunes (ISO y DD/MM/YYYY)
                fecha = parse_date(fecha_raw)
                if not fecha:
                    parsed = None
                    for fmt in ('%d/%m/%Y', '%d-%m-%Y'):
                        try:
                            parsed = datetime.strptime(fecha_raw, fmt).date()
                            break
                        except Exception:
                            parsed = None
                    fecha = parsed

                if not fecha:
                    self.stdout.write(self.style.WARNING(f'Fila {i}: Fecha inválida ({fecha_raw}). Omitido.'))
                    skipped += 1
                    continue

                # Identificar bombero (solo después de validar fecha)
                bombero = None
                val_id = get_val(row, 'bombero_id')
                val_rut = get_val(row, 'bombero_rut')
                val_uname = get_val(row, 'bombero_username')
                val_name = get_val(row, 'bombero_nombre')
                if val_id:
                    try:
                        bombero = Bombero.objects.get(id=int(val_id))
                    except Exception:
                        bombero = None
                if not bombero and val_rut:
                    try:
                        bombero = Bombero.objects.get(rut=val_rut)
                    except Exception:
                        bombero = None
                if not bombero and val_uname:
                    try:
                        bombero = Bombero.objects.get(user__username=val_uname)
                    except Exception:
                        bombero = None
                if not bombero and val_name:
                    try:
                        bombero = Bombero.objects.get(nombre=val_name)
                    except Exception:
                        bombero = None

                if not bombero:
                    if create_bombero:
                        rut_val = val_rut
                        nombre_val = get_val(row, 'bombero_nombre') or get_val(row, 'nombre') or ''
                        username_val = val_uname
                        def normalize_username(s):
                            if not s:
                                return ''
                            s = unicodedata.normalize('NFKD', s)
                            s = s.encode('ascii', 'ignore').decode('ascii')
                            s = ''.join(ch for ch in s if ch.isalnum())
                            return s[:30] or 'user'

                        if not username_val:
                            base = normalize_username(rut_val or nombre_val or 'user')
                            username_candidate = base
                            suffix = 0
                            while User.objects.filter(username=username_candidate).exists():
                                suffix += 1
                                username_candidate = f"{base}{suffix}"
                            username_val = username_candidate

                        pwd = get_random_string(12)
                        try:
                            user = User.objects.create_user(username=username_val, password=pwd)
                            bombero = Bombero.objects.create(
                                user=user,
                                rut=rut_val or username_val,
                                nombre=nombre_val or username_val,
                                rol='Bombero',
                            )
                            self.stdout.write(self.style.SUCCESS(f'Fila {i}: Se creó Bombero {bombero.nombre} (username: {user.username})'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Fila {i}: Error creando Bombero: {e}'))
                            skipped += 1
                            continue
                    else:
                        self.stdout.write(self.style.WARNING(f'Fila {i}: Bombero no encontrado (intente bombero_id,bombero_rut o bombero_username). Omitido.'))
                        skipped += 1
                        continue

                # Fecha (obligatoria)
                fecha_raw = get_val(row, 'fecha')
                if not fecha_raw:
                    self.stdout.write(self.style.WARNING(f'Fila {i}: Fecha vacía. Omitido.'))
                    skipped += 1
                    continue

                fecha = parse_date(fecha_raw)
                if not fecha:
                    self.stdout.write(self.style.WARNING(f'Fila {i}: Fecha inválida ({fecha_raw}). Omitido.'))
                    skipped += 1
                    continue

                hora_inicio_raw = get_val(row, 'hora_inicio')
                hora_fin_raw = get_val(row, 'hora_fin')
                hora_inicio = parse_time(hora_inicio_raw) if hora_inicio_raw else None
                hora_fin = parse_time(hora_fin_raw) if hora_fin_raw else None
                # 'tipo' removed from CSV; use default
                tipo = 'Nocturna'
                herramientas = get_val(row, 'herramientas') or get_val(row, 'material_mayor') or None
                # optional column with per-vehicle timestamps: llegada|retiro|llegada_cuartel;... (ISO datetimes)
                material_times_raw = get_val(row, 'material_times')
                apoyo_externo = get_val(row, 'apoyo_externo') or None
                lugar = get_val(row, 'lugar') or None
                tipo_emergencia = get_val(row, 'tipo_emergencia') or get_val(row, 'tipo_em') or None

                # Evitamos duplicados exactos: misma fecha y mismo bombero con mismas horas
                exists_qs = Guardia.objects.filter(bombero=bombero, fecha=fecha)
                if hora_inicio:
                    exists_qs = exists_qs.filter(hora_inicio=hora_inicio)
                if hora_fin:
                    exists_qs = exists_qs.filter(hora_fin=hora_fin)

                if exists_qs.exists():
                    self.stdout.write(self.style.NOTICE(f'Fila {i}: Ya existe una guardia similar para {bombero.nombre} en {fecha}. Omitido.'))
                    skipped += 1
                    continue

                if dry:
                    self.stdout.write(self.style.SUCCESS(f'Fila {i}: OK (dry-run) -> {bombero.nombre} {fecha}'))
                    created += 1
                    continue

                try:
                    Guardia.objects.create(
                        bombero=bombero,
                        fecha=fecha,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        tipo=tipo,
                        herramientas=herramientas,
                        apoyo_externo=apoyo_externo,
                        lugar=lugar,
                    )
                    # crear material mayor asociado si hay un código
                    created_guardia = Guardia.objects.filter(bombero=bombero, fecha=fecha, hora_inicio=hora_inicio).order_by('-id').first()
                    if created_guardia and (herramientas or ''):
                        # parse material_times if provided, otherwise generate default triplets
                        vehiculos = (herramientas or '').replace(';',',').split(',')
                        times_list = []
                        if material_times_raw:
                            parts = [p for p in material_times_raw.split(';') if p.strip()]
                            for part in parts:
                                triple = part.split('|')
                                if len(triple) == 3:
                                    times_list.append(triple)
                                else:
                                    times_list.append([None, None, None])

                        base_dt = datetime.combine(fecha, datetime.min.time())
                        default_triplet = [ (base_dt + timedelta(minutes=30)).isoformat(), (base_dt + timedelta(hours=2)).isoformat(), (base_dt + timedelta(hours=3)).isoformat() ]

                        for idx, v in enumerate(vehiculos):
                            vcode = v.strip()
                            if not vcode:
                                continue
                            trip = None
                            if idx < len(times_list):
                                trip = times_list[idx]
                            if trip and all(trip):
                                try:
                                    llegada_dt = datetime.fromisoformat(trip[0])
                                    retiro_dt = datetime.fromisoformat(trip[1])
                                    llegada_cuartel_dt = datetime.fromisoformat(trip[2])
                                except Exception:
                                    llegada_dt = datetime.fromisoformat(default_triplet[0])
                                    retiro_dt = datetime.fromisoformat(default_triplet[1])
                                    llegada_cuartel_dt = datetime.fromisoformat(default_triplet[2])
                            else:
                                llegada_dt = datetime.fromisoformat(default_triplet[0])
                                retiro_dt = datetime.fromisoformat(default_triplet[1])
                                llegada_cuartel_dt = datetime.fromisoformat(default_triplet[2])

                            try:
                                from gestion.models import MaterialMayor
                                MaterialMayor.objects.create(
                                    guardia=created_guardia,
                                    vehiculo=vcode,
                                    llegada=llegada_dt,
                                    retiro=retiro_dt,
                                    llegada_cuartel=llegada_cuartel_dt,
                                )
                            except Exception:
                                pass
                    # Crear una Emergencia relacionada si se proporcionó tipo_emergencia
                    if tipo_emergencia:
                        try:
                            from gestion.models import Emergencia
                            # Determinar fecha_hora de la emergencia: usamos la primera llegada si existe
                            emerg_dt = None
                            if material_times_raw:
                                parts0 = [p for p in material_times_raw.split(';') if p.strip()]
                                if parts0:
                                    triple0 = parts0[0].split('|')
                                    try:
                                        emerg_dt = datetime.fromisoformat(triple0[0])
                                    except Exception:
                                        emerg_dt = None

                            if not emerg_dt:
                                # fallback: combine fecha + hora_inicio si existe, o fecha + 00:30
                                try:
                                    if hora_inicio:
                                        emerg_dt = datetime.combine(fecha, hora_inicio)
                                    else:
                                        emerg_dt = datetime.combine(fecha, datetime.min.time()) + timedelta(minutes=30)
                                except Exception:
                                    emerg_dt = None

                            e = Emergencia.objects.create(
                                tipo=tipo_emergencia,
                                direccion=lugar or 'Calle Ficticia 1',
                                fecha_hora=emerg_dt or datetime.combine(fecha, datetime.min.time()),
                                herramientas=herramientas or None,
                                apoyo_externo=apoyo_externo or None,
                                lugar=lugar or None,
                            )
                            # asociar al bombero como asistente
                            try:
                                e.asistentes.add(bombero)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Fila {i}: Error al crear Guardia: {e}'))
                    errors += 1

        if rows is None:
            fh.close()

        self.stdout.write(self.style.SUCCESS(f'Import terminado. Creadas: {created}, Omitidas: {skipped}, Errores: {errors}'))
