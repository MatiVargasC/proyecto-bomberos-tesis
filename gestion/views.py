from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # Para proteger páginas
from .models import Guardia, Bombero
from django.contrib.auth.models import User
from .forms import BomberoCreationForm, GuardiaForm
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
import datetime
import calendar
import json
from django.contrib import messages # Para mostrar mensajes
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import MaterialMayor
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template import loader
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required

@login_required # ¡Esta línea protege la página! Solo usuarios logueados pueden verla.
def index(request):
    # Permitimos que staff/superuser vean el panel incluso sin perfil Bombero enlazado
    bombero = None
    try:
        bombero = request.user.bombero
    except (Bombero.DoesNotExist, AttributeError):
        # Si no tiene perfil y no es admin, mostramos mensaje pero permitimos ver la UI
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Tu usuario no está enlazado a un perfil de Bombero. Contacta al administrador.')
            return render(request, 'gestion/index.html', {'error': True})

    # Obtenemos la fecha de hoy
    hoy = timezone.now().date()
    
    # Buscamos si ya hay una guardia abierta HOY para este bombero
    guardia_abierta = Guardia.objects.filter(bombero=bombero, fecha=hoy, hora_fin__isnull=True).first()
    
    # Buscamos si hay una guardia CERRADA hoy (para mostrar el estado)
    guardia_cerrada = Guardia.objects.filter(bombero=bombero, fecha=hoy, hora_fin__isnull=False).first()

    if request.method == 'POST':
        accion = request.POST.get('accion') # 'check-in' o 'check-out'

        if accion == 'check-in' and not guardia_abierta:
            # Si no hay guardia abierta, creamos una nueva
            Guardia.objects.create(
                bombero=bombero,
                fecha=hoy,
                hora_inicio=timezone.now().time()
            )
            messages.success(request, '¡Check-in de guardia registrado! Bienvenido.')

        # Accion especial: admin puede crear nueva guardia aunque ya exista una cerrada hoy
        elif accion == 'admin-check-in' and es_administrador(request.user) and not guardia_abierta:
            Guardia.objects.create(
                bombero=bombero,
                fecha=hoy,
                hora_inicio=timezone.now().time()
            )
            messages.success(request, '¡Check-in de guardia registrado por administrador!')

        elif accion == 'check-out' and guardia_abierta:
            # Si hay una guardia abierta, la cerramos
            guardia_abierta.hora_fin = timezone.now().time()
            guardia_abierta.save()
            messages.info(request, '¡Check-out de guardia registrado! Que descanses.')
        
        # Admin: registrar guardia para otro Bombero (seleccionado desde UI)
        elif accion == 'admin-check-in-for' and es_administrador(request.user):
            target_id = request.POST.get('target_bombero')
            try:
                target = Bombero.objects.get(id=target_id)
            except (Bombero.DoesNotExist, TypeError, ValueError):
                messages.error(request, 'Bombero seleccionado no válido.')
            else:
                # Verificamos que no exista una guardia abierta hoy para ese bombero
                guardia_abierta_target = Guardia.objects.filter(bombero=target, fecha=hoy, hora_fin__isnull=True).first()
                if guardia_abierta_target:
                    messages.error(request, f'El bombero {target.nombre} ya tiene una guardia abierta hoy.')
                else:
                    # Leer campos opcionales enviados desde el modal
                    fecha_raw = request.POST.get('fecha')
                    hora_inicio_raw = request.POST.get('hora_inicio')
                    hora_fin_raw = request.POST.get('hora_fin')
                    tipo = request.POST.get('tipo') or 'Nocturna'
                    herramientas = request.POST.get('material_mayor') or request.POST.get('herramientas') or None
                    apoyo_externo = request.POST.get('apoyo_externo') or None
                    lugar = request.POST.get('lugar') or None

                    # parseo seguro de fecha/hora
                    fecha_val = hoy
                    if fecha_raw:
                        try:
                            pd = parse_date(fecha_raw)
                            if pd:
                                fecha_val = pd
                        except Exception:
                            pass

                    hora_inicio_val = None
                    if hora_inicio_raw:
                        try:
                            hora_inicio_val = parse_time(hora_inicio_raw)
                        except Exception:
                            hora_inicio_val = None

                    hora_fin_val = None
                    if hora_fin_raw:
                        try:
                            hora_fin_val = parse_time(hora_fin_raw)
                        except Exception:
                            hora_fin_val = None

                    # Si no se entrega hora_inicio, usamos ahora
                    if not hora_inicio_val:
                        hora_inicio_val = timezone.now().time()

                    Guardia.objects.create(
                        bombero=target,
                        fecha=fecha_val,
                        hora_inicio=hora_inicio_val,
                        hora_fin=hora_fin_val,
                        tipo=tipo,
                        herramientas=herramientas,
                        apoyo_externo=apoyo_externo,
                        lugar=lugar,
                    )
                    # crear registros de MaterialMayor si vienen listas en POST
                    try:
                        created_guardia = Guardia.objects.filter(bombero=target, fecha=fecha_val, hora_inicio=hora_inicio_val).order_by('-id').first()
                        vehiculos = request.POST.getlist('material_vehiculo')
                        salidas = request.POST.getlist('material_salida')
                        llegadas = request.POST.getlist('material_llegada')
                        retiros = request.POST.getlist('material_retiro')
                        llegadas_cuartel = request.POST.getlist('material_llegada_cuartel')
                        for idx, v in enumerate(vehiculos):
                            code = v.strip()
                            if not code:
                                continue
                            # parse datetimes loosely; importer expects ISO or datetime strings
                            def parse_dt(s):
                                from datetime import datetime
                                try:
                                    return datetime.fromisoformat(s)
                                except Exception:
                                    return None

                            llegada_dt = parse_dt(llegadas[idx]) if idx < len(llegadas) else None
                            retiro_dt = parse_dt(retiros[idx]) if idx < len(retiros) else None
                            llegada_cuartel_dt = parse_dt(llegadas_cuartel[idx]) if idx < len(llegadas_cuartel) else None
                            salida_dt = parse_dt(salidas[idx]) if idx < len(salidas) else None
                            # If no arrival time provided, leave null
                            MaterialMayor.objects.create(
                                guardia=created_guardia,
                                vehiculo=code,
                                llegada=llegada_dt or salida_dt,
                                retiro=retiro_dt,
                                llegada_cuartel=llegada_cuartel_dt,
                            )
                    except Exception:
                        pass
                    messages.success(request, f'Guardia registrada para {target.nombre}.')
            
        return redirect('index') # Recargamos la página

    # Si no es POST, solo mostramos la página
    # Si el usuario es administrador, pasamos la lista de bomberos para el modal
    bomberos_list = Bombero.objects.all().order_by('nombre') if es_administrador(request.user) else None

    # Próxima guardia: si el usuario es bombero mostramos su próxima guardia, si es staff mostramos próximas guardias generales
    hoy = timezone.now().date()
    proxima_guardia = None
    if bombero:
        proxima_guardia = Guardia.objects.filter(bombero=bombero, fecha__gte=hoy).order_by('fecha').first()
    else:
        # para staff mostramos la próxima guardia próxima del conjunto
        proxima_guardia = Guardia.objects.filter(fecha__gte=hoy).order_by('fecha').first()

    # Personal operativo: lista de bomberos con guardia abierta hoy
    abiertos = Guardia.objects.filter(fecha=hoy, hora_fin__isnull=True)
    personal_operativo_list = [g.bombero.nombre for g in abiertos]
    personal_operativo_count = len(personal_operativo_list)

    contexto = {
        'bombero': bombero,
        'guardia_abierta': guardia_abierta,
        'guardia_cerrada': guardia_cerrada,
        'bomberos': bomberos_list,
        'proxima_guardia': proxima_guardia,
        'personal_operativo': personal_operativo_count,
        'personal_operativo_list': personal_operativo_list,
    }
    return render(request, 'gestion/index.html', contexto)


@login_required
def historial(request):
    # Buscamos todas las guardias del bombero logueado
    user = request.user
    try:
        bombero = user.bombero
    except (AttributeError, Bombero.DoesNotExist):
        messages.error(request, 'Tu usuario no está enlazado a un perfil de Bombero. Contacta al administrador.')
        return redirect('index')

    mis_guardias = Guardia.objects.filter(bombero=bombero).order_by('-fecha')
    # Determinar permiso para mostrar botón editar: staff/superuser o Jefe de Guardia
    user = request.user
    can_edit = False
    try:
        if user.is_staff or user.is_superuser:
            can_edit = True
        else:
            # comprobar rol si existe perfil bombero
            if hasattr(user, 'bombero') and user.bombero and getattr(user.bombero, 'rol', None) == 'Jefe de Guardia':
                can_edit = True
    except Exception:
        can_edit = False

    contexto = {
        'mis_guardias': mis_guardias,
        'can_edit': can_edit,
    }
    return render(request, 'gestion/historial.html', contexto)


@login_required
def editar_guardia(request, pk):
    guardia = get_object_or_404(Guardia, pk=pk)

    # Permisos: puede editar el dueño de la guardia o personal de staff/superuser
    user_bombero = getattr(request.user, 'bombero', None)
    if not (request.user.is_staff or request.user.is_superuser or user_bombero == guardia.bombero):
        messages.error(request, 'No tienes permiso para editar esta guardia.')
        return redirect('historial')

    if request.method == 'POST':
        form = GuardiaForm(request.POST, instance=guardia)
        if form.is_valid():
            form.save()
            # Procesar MaterialMayor enviados desde el formulario de edición
            try:
                # listas paralelas: material_id (opcional), material_vehiculo, material_llegada, material_retiro, material_llegada_cuartel
                ids = request.POST.getlist('material_id')
                vehs = request.POST.getlist('material_vehiculo')
                lleg = request.POST.getlist('material_llegada')
                ret = request.POST.getlist('material_retiro')
                lleg_c = request.POST.getlist('material_llegada_cuartel')

                # actualizar existentes o crear nuevos
                for idx, veh in enumerate(vehs):
                    code = veh.strip()
                    if not code:
                        continue
                    mid = ids[idx] if idx < len(ids) else ''
                    # helper parse
                    from datetime import datetime
                    def parse_dt(s):
                        try:
                            return datetime.fromisoformat(s)
                        except Exception:
                            return None

                    llegada_dt = parse_dt(lleg[idx]) if idx < len(lleg) else None
                    retiro_dt = parse_dt(ret[idx]) if idx < len(ret) else None
                    llegada_cuartel_dt = parse_dt(lleg_c[idx]) if idx < len(lleg_c) else None

                    if mid:
                        try:
                            mm = MaterialMayor.objects.get(pk=int(mid), guardia=guardia)
                            mm.vehiculo = code
                            mm.llegada = llegada_dt
                            mm.retiro = retiro_dt
                            mm.llegada_cuartel = llegada_cuartel_dt
                            mm.save()
                        except Exception:
                            # crear si no existe
                            try:
                                MaterialMayor.objects.create(
                                    guardia=guardia,
                                    vehiculo=code,
                                    llegada=llegada_dt,
                                    retiro=retiro_dt,
                                    llegada_cuartel=llegada_cuartel_dt,
                                )
                            except Exception:
                                pass
                    else:
                        try:
                            MaterialMayor.objects.create(
                                guardia=guardia,
                                vehiculo=code,
                                llegada=llegada_dt,
                                retiro=retiro_dt,
                                llegada_cuartel=llegada_cuartel_dt,
                            )
                        except Exception:
                            pass
            except Exception:
                pass
            messages.success(request, 'Guardia actualizada correctamente.')
            return redirect('historial')
    else:
        form = GuardiaForm(instance=guardia)

    return render(request, 'gestion/editar_guardia.html', {'form': form, 'guardia': guardia})
    
def es_administrador(user):
    # Devuelve True si el usuario es superusuario o si tiene permisos de staff
    return user.is_superuser or user.is_staff


@login_required
def detalle_guardia(request, pk):
    guardia = get_object_or_404(Guardia, pk=pk)

    # Permisos: el dueño o staff
    user_bombero = getattr(request.user, 'bombero', None)
    if not (request.user.is_staff or request.user.is_superuser or user_bombero == guardia.bombero):
        messages.error(request, 'No tienes permiso para ver este detalle.')
        return redirect('historial')

    # Emergencias relacionadas: aquellas donde el bombero fue asistente y la fecha coincide
    emergencias = guardia.bombero.emergencias_atendidas.filter(fecha_hora__date=guardia.fecha)

    # Material mayor asociado (relacionado por el nuevo modelo MaterialMayor)
    materiales = guardia.materiales.all()

    return render(request, 'gestion/detalle_guardia.html', {'guardia': guardia, 'emergencias': emergencias, 'materiales': materiales})

@login_required
def reportes_avanzados_view(request):
    """
    Renderiza la página de reportes avanzados. 
    Solo accesible para usuarios con privilegios de administrador o staff.
    """
    # Soporte para filtros por rango de fechas y export CSV
    hoy = timezone.now().date()
    # Leer parámetros GET
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    # Construimos queryset base de guardias
    guardias_qs = Guardia.objects.all().order_by('-fecha')
    if start_date:
        try:
            sd = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            guardias_qs = guardias_qs.filter(fecha__gte=sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            guardias_qs = guardias_qs.filter(fecha__lte=ed)
        except ValueError:
            pass

    # Preparamos datos para el gráfico: si hay filtro de fechas calculamos meses en ese rango
    labels = []
    data_counts = []

    def month_range(start_date, end_date):
        # genera (year, month) tuples desde start_date hasta end_date inclusive
        y, m = start_date.year, start_date.month
        while (y < end_date.year) or (y == end_date.year and m <= end_date.month):
            yield (y, m)
            m += 1
            if m > 12:
                m = 1
                y += 1

    # Si recibimos start/end válidos, usamos ese rango; si no, usamos últimos 6 meses
    try:
        if start_date and end_date:
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            # normalize: start at first of month, end at last of month for chart grouping
            start_month = start_dt.replace(day=1)
            end_month = end_dt.replace(day=1)
            for (yy, mm) in month_range(start_month, end_month):
                labels.append(calendar.month_name[mm])
                data_counts.append(Guardia.objects.filter(fecha__year=yy, fecha__month=mm).count())
        else:
            for delta in range(5, -1, -1):
                month = (hoy.month - delta - 1) % 12 + 1
                year = hoy.year + ((hoy.month - delta - 1) // 12)
                labels.append(calendar.month_name[month])
                data_counts.append(Guardia.objects.filter(fecha__year=year, fecha__month=month).count())
    except Exception:
        # Fallback: últimos 6 meses
        labels = []
        data_counts = []
        for delta in range(5, -1, -1):
            month = (hoy.month - delta - 1) % 12 + 1
            year = hoy.year + ((hoy.month - delta - 1) // 12)
            labels.append(calendar.month_name[month])
            data_counts.append(Guardia.objects.filter(fecha__year=year, fecha__month=month).count())

    # Si piden export CSV, generamos la respuesta
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse

        filename = f"guardias_{start_date or 'desde_inicio'}_{end_date or 'hasta_fin'}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Determinar columnas solicitadas (GET param 'cols' puede repetirse)
        requested_cols = request.GET.getlist('cols')
        all_cols = [
            ('fecha','Fecha'), ('hora_inicio','Hora inicio'), ('hora_fin','Hora fin'),
            ('nombre','Nombre Bombero'), ('rol','Rol Bombero'), ('emergencia','Emergencia (Si/No)'),
            ('tipo_emergencia','Tipo de emergencia'), ('lugar','Lugar/Sector'),
            ('herramientas','Herramientas utilizadas'), ('apoyo_externo','Apoyo externo')
        ]
        # Si no se piden columnas, incluimos todas
        if not requested_cols:
            requested_cols = [c[0] for c in all_cols]

        # Escribimos cabecera en el orden de all_cols filtrado
        headers = [label for key,label in all_cols if key in requested_cols]
        writer.writerow(headers)

        for g in guardias_qs:
            emergencias = g.bombero.emergencias_atendidas.filter(fecha_hora__date=g.fecha)
            emergencia_flag = 'Si' if emergencias.exists() else 'No'
            tipos = '; '.join(sorted({e.tipo for e in emergencias})) if emergencias.exists() else ''
            lugares = '; '.join(sorted({e.direccion for e in emergencias})) if emergencias.exists() else ''
            # recopilar herramientas y apoyo desde emergencias relacionadas si existen
            emerg_herr = '; '.join(sorted({(e.herramientas or '').strip() for e in emergencias if (e.herramientas or '').strip()})) if emergencias.exists() else ''
            emerg_apoyo = '; '.join(sorted({(e.apoyo_externo or '').strip() for e in emergencias if (e.apoyo_externo or '').strip()})) if emergencias.exists() else ''

            row_map = {
                'fecha': g.fecha.isoformat(),
                'hora_inicio': g.hora_inicio.isoformat() if g.hora_inicio else '',
                'hora_fin': g.hora_fin.isoformat() if g.hora_fin else '',
                'nombre': g.bombero.nombre,
                'rol': g.bombero.rol,
                'emergencia': emergencia_flag,
                'tipo_emergencia': tipos,
                'lugar': g.lugar or lugares,
                'herramientas': g.herramientas or emerg_herr or '',
                'apoyo_externo': g.apoyo_externo or emerg_apoyo or ''
            }

            writer.writerow([row_map[k] for k in [key for key,label in all_cols if key in requested_cols]])

        return response

    context = {
        'titulo_pagina': 'Reportes y Dashboard',
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data_counts),
    }
    # KPIs: Guardias creadas, Cobertura (%% guardias con emergencia), Asistencia total (horas)
    total_guardias = guardias_qs.count()
    guardias_con_em = 0
    total_seconds = 0
    for g in guardias_qs:
        emergencias = g.bombero.emergencias_atendidas.filter(fecha_hora__date=g.fecha)
        if emergencias.exists():
            guardias_con_em += 1
        if g.hora_inicio and g.hora_fin:
            try:
                dt_start = datetime.datetime.combine(g.fecha, g.hora_inicio)
                dt_end = datetime.datetime.combine(g.fecha, g.hora_fin)
                if dt_end <= dt_start:
                    dt_end += datetime.timedelta(days=1)
                total_seconds += (dt_end - dt_start).total_seconds()
            except Exception:
                pass

    kpi_guardias = total_guardias
    kpi_coverage = round((guardias_con_em / total_guardias * 100) if total_guardias else 0, 1)
    kpi_hours = round(total_seconds / 3600, 2)

    # Top 5 bomberos por número de guardias en el queryset filtrado
    top5_qs = (Guardia.objects
               .filter(id__in=guardias_qs.values_list('id', flat=True))
               .values('bombero__id', 'bombero__nombre')
               .annotate(count=Count('id'))
               .order_by('-count')[:5])
    top5 = [{'nombre': t.get('bombero__nombre') or '—', 'count': t.get('count', 0)} for t in top5_qs]
    context.update({'kpi_guardias': kpi_guardias, 'kpi_coverage': kpi_coverage, 'kpi_hours': kpi_hours, 'top5': top5})
    # Preparar filas de guardias para la tabla (precomputadas para facilitar el template)
    guardias_rows = []
    for g in guardias_qs[:500]:
        emergencias = g.bombero.emergencias_atendidas.filter(fecha_hora__date=g.fecha)
        emergencia_flag = 'Si' if emergencias.exists() else 'No'
        # Normalizar tipos: extraer solo códigos (ej: 10-4, 10-3-18, 7-0) de cualquier texto
        import re
        tipos_set = set()
        if emergencias.exists():
            for e in emergencias:
                if not e.tipo:
                    continue
                # buscar códigos del tipo N-N o N-N-N (por ejemplo 10-4, 10-3-18, 7-0)
                codes = re.findall(r"\d+(?:-\d+){1,2}", str(e.tipo))
                if codes:
                    for c in codes:
                        tipos_set.add(c)
                else:
                    # si no se encuentra código, añadimos el valor tal cual
                    tipos_set.add(str(e.tipo).strip())
        tipos = '; '.join(sorted(tipos_set)) if tipos_set else ''
        lugares = '; '.join(sorted({e.direccion for e in emergencias})) if emergencias.exists() else ''
        emerg_herr = '; '.join(sorted({(e.herramientas or '').strip() for e in emergencias if (e.herramientas or '').strip()})) if emergencias.exists() else ''
        emerg_apoyo = '; '.join(sorted({(e.apoyo_externo or '').strip() for e in emergencias if (e.apoyo_externo or '').strip()})) if emergencias.exists() else ''

        guardias_rows.append({
            'fecha': g.fecha,
            'hora_inicio': g.hora_inicio,
            'hora_fin': g.hora_fin,
            'nombre': g.bombero.nombre,
            'rol': g.bombero.rol,
            'emergencia': emergencia_flag,
            'tipo_emergencia': tipos,
            'lugar': g.lugar or lugares,
            'herramientas': g.herramientas or emerg_herr or '',
            'apoyo_externo': g.apoyo_externo or emerg_apoyo or ''
        })

    context['guardias'] = guardias_rows
    return render(request, 'gestion/reportes_avanzados.html', context)


@login_required
def gestion_personal_view(request):
    """
    Página de gestión de personal — accesible sólo para staff/superuser.
    Muestra una tabla con los `Bombero` registrados.
    """
    if not es_administrador(request.user):
        messages.error(request, 'Acceso denegado: necesitas permisos de administrador o staff.')
        return redirect('index')

    bomberos = Bombero.objects.all().order_by('nombre')
    contexto = {
        'bomberos': bomberos,
        'titulo_pagina': 'Gestión de Personal'
    }
    return render(request, 'gestion/gestion_de_personal.html', contexto)


@login_required
def mi_perfil(request):
    # Página simple de perfil del usuario
    user = request.user
    bombero = getattr(user, 'bombero', None)
    return render(request, 'gestion/mi_perfil.html', {'user': user, 'bombero': bombero})


@login_required
def asignar_guardias(request):
    # Sólo staff o superuser
    if not es_administrador(request.user):
        return HttpResponseForbidden('Acceso denegado')

    if request.method == 'POST':
        bomberos_ids = request.POST.getlist('bomberos')
        fecha_raw = request.POST.get('fecha')
        tipo = request.POST.get('tipo') or 'Nocturna'
        if not fecha_raw:
            messages.error(request, 'Debes indicar una fecha.')
            return redirect('gestion_personal')
        fecha_val = parse_date(fecha_raw) or None
        if not fecha_val:
            messages.error(request, 'Fecha inválida.')
            return redirect('gestion_personal')

        created = 0
        for bid in bomberos_ids:
            try:
                b = Bombero.objects.get(pk=int(bid))
            except Exception:
                continue
            # evitar duplicados: si ya existe guardia para esa fecha, saltar
            if Guardia.objects.filter(bombero=b, fecha=fecha_val).exists():
                continue
            Guardia.objects.create(bombero=b, fecha=fecha_val, tipo=tipo)
            created += 1

        messages.success(request, f'Asignadas {created} guardias para {fecha_val}.')
        return redirect('gestion_personal')
    else:
        return HttpResponseForbidden('Método no permitido')


@login_required
def personal_operativo_view(request):
    # Vista para staff: muestra bomberos con una racha de guardias Nocturna de >= dias
    if not es_administrador(request.user):
        messages.error(request, 'Acceso denegado: requiere permisos de staff.')
        return redirect('index')

    dias = int(request.GET.get('dias', 3))
    hoy = timezone.now().date()

    data = []
    for b in Bombero.objects.all().order_by('nombre'):
        # obtener sus guardias recientes ordenadas por fecha desc
        gs = list(Guardia.objects.filter(bombero=b, tipo='Nocturna').order_by('-fecha').values_list('fecha', flat=True))
        # contar consecutivos desde hoy hacia atrás
        consec = 0
        check_date = hoy
        idx = 0
        while consec < dias:
            if idx >= len(gs):
                break
            if gs[idx] == check_date:
                consec += 1
                idx += 1
                check_date = check_date - datetime.timedelta(days=1)
            else:
                break

        if consec >= dias:
            data.append({'bombero': b, 'consecutivos': consec})

    return render(request, 'gestion/personal_operativo.html', {'data': data, 'dias': dias})


@login_required
def nuevo_bombero_view(request):
    """Crear nuevo Bombero y su User asociado. Solo staff/superuser."""
    if not es_administrador(request.user):
        messages.error(request, 'Acceso denegado: necesitas permisos de administrador o staff.')
        return redirect('index')

    if request.method == 'POST':
        form = BomberoCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data.get('email')
            rut = form.cleaned_data['rut']
            nombre = form.cleaned_data['nombre']
            rol = form.cleaned_data['rol']

            user = User.objects.create_user(username=username, email=email)
            user.set_password(password)
            user.save()

            bombero = Bombero.objects.create(user=user, rut=rut, nombre=nombre, rol=rol)
            messages.success(request, f'Bombero {bombero.nombre} creado correctamente.')
            return redirect('gestion_personal')
    else:
        form = BomberoCreationForm()

    return render(request, 'gestion/nuevo_bombero.html', {'form': form})


def register_view(request):
    """Vista pública para que un nuevo usuario se registre como Bombero."""
    if request.user.is_authenticated:
        messages.info(request, 'Ya has iniciado sesión.')
        return redirect('index')

    if request.method == 'POST':
        form = BomberoCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data.get('email')
            rut = form.cleaned_data['rut']
            nombre = form.cleaned_data['nombre']
            # Forzamos rol a 'Bombero' para registros públicos
            rol = 'Bombero'

            user = User.objects.create_user(username=username, email=email)
            user.set_password(password)
            user.save()

            Bombero = Bombero.objects.create(user=user, rut=rut, nombre=nombre, rol=rol)
            messages.success(request, f'Registro completado. Por favor inicia sesión.')
            return redirect('login')
    else:
        form = BomberoCreationForm()

    # Ocultamos la selección de rol en el template (será forzada a 'Bombero')
    return render(request, 'registration/register.html', {'form': form})

@staff_member_required
def sincronizar_viper(request):
    from gestion.management.commands.sync_viper import Command
    Command().handle()
    messages.success(request, "Sincronización con VIPER completada (modo simulado)")
    return redirect('admin:index')  # o return redirect('dashboard_admin')