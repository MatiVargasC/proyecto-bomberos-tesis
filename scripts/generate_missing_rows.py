import os
import sys
import csv

# Ajustar path para poder importar Django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomberos_project.settings')
import django
django.setup()

from django.utils.dateparse import parse_date, parse_time
from gestion.models import Bombero, Guardia

INPUT = os.path.join(PROJECT_ROOT, 'samples', 'Reportes_TESIS.csv')
OUTPUT = os.path.join(PROJECT_ROOT, 'samples', 'Reportes_TESIS_missing.csv')

def get_val(row, key):
    v = row.get(key) if isinstance(row, dict) else None
    if v is None:
        return ''
    return str(v).strip()

def find_bombero(row):
    val_id = get_val(row, 'bombero_id')
    val_rut = get_val(row, 'bombero_rut')
    val_uname = get_val(row, 'bombero_username')
    val_name = get_val(row, 'bombero_nombre')
    b = None
    if val_id:
        try:
            b = Bombero.objects.get(id=int(val_id))
            return b
        except Exception:
            b = None
    if val_rut:
        try:
            b = Bombero.objects.get(rut=val_rut)
            return b
        except Exception:
            b = None
    if val_uname:
        try:
            b = Bombero.objects.get(user__username=val_uname)
            return b
        except Exception:
            b = None
    if val_name:
        try:
            b = Bombero.objects.get(nombre=val_name)
            return b
        except Exception:
            b = None
    return None

def row_exists_in_db(row):
    fecha_raw = get_val(row, 'fecha')
    fecha = parse_date(fecha_raw)
    if not fecha:
        return False
    bombero = find_bombero(row)
    if not bombero:
        # if bombero not found, treat as missing (importer could create it with flag)
        return False
    hora_inicio_raw = get_val(row, 'hora_inicio')
    hora_fin_raw = get_val(row, 'hora_fin')
    hora_inicio = parse_time(hora_inicio_raw) if hora_inicio_raw else None
    hora_fin = parse_time(hora_fin_raw) if hora_fin_raw else None

    qs = Guardia.objects.filter(bombero=bombero, fecha=fecha)
    if hora_inicio:
        qs = qs.filter(hora_inicio=hora_inicio)
    if hora_fin:
        qs = qs.filter(hora_fin=hora_fin)
    return qs.exists()

def main():
    if not os.path.exists(INPUT):
        print('Archivo de entrada no encontrado:', INPUT)
        return

    with open(INPUT, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    missing = []
    total = len(rows)
    for i, row in enumerate(rows, start=1):
        try:
            if not row_exists_in_db(row):
                missing.append(row)
        except Exception as e:
            print(f'Fila {i}: error comprobando existencia: {e}')

    if not missing:
        print(f'No hay filas nuevas. Total leídas: {total}. Filas faltantes: 0')
        # crear archivo vacío con cabecera para claridad
        with open(OUTPUT, 'w', newline='', encoding='utf-8') as outfh:
            writer = csv.DictWriter(outfh, fieldnames=reader.fieldnames)
            writer.writeheader()
        return

    # Escribir CSV reducido
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as outfh:
        writer = csv.DictWriter(outfh, fieldnames=reader.fieldnames)
        writer.writeheader()
        for r in missing:
            writer.writerow(r)

    print(f'Total leídas: {total}. Filas faltantes escritas en: {OUTPUT} (count={len(missing)})')

if __name__ == '__main__':
    main()
