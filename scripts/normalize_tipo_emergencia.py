import csv
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'samples' / 'Reportes_TESIS.csv'
# Allowed codes from the provided image (Clave 10 + related codes)
codes = ['10-0','10-1','10-2','10-3','10-4','10-5','10-6','10-7','10-8','10-10','10-13','10-15','10-3-18','10-3-19','10-4-1','7-0','7-3','10-11','10-12']
rows = []
with p.open(newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for i, row in enumerate(reader):
        if len(row) < 9:
            rows.append(row)
            continue
        row[6] = codes[i % len(codes)]
        rows.append(row)
with p.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)
print(f'CSV normalizado: tipos de emergencia actualizados a códigos válidos ({len(rows)} filas)')
