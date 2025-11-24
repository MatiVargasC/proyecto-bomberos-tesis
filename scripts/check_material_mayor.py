import csv
from collections import Counter

allowed = ["B1","BH1","H1","B2","BT2","BX2","B3","RB3","RH3","RX4","Q4","M4","B5","BX5","RX5","B6","BX6","Z6","B7","BX7","BR7","B8","BR8","Q8","K1","K2","K3","L1","S1"]
path = 'samples/Reportes_TESIS.csv'

invalid = []
counts = Counter()
with open(path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        key = row.get('material_mayor','').strip()
        counts[key] += 1
        if key not in allowed:
            invalid.append((i, key, row))

print('Total filas leídas:', sum(counts.values()))
print('Claves encontradas y conteo:')
for k, v in counts.most_common():
    print(f'  {k!r}: {v}')

if invalid:
    print('\nEntradas inválidas (primeras 10):')
    for i, key, row in invalid[:10]:
        print(f'  fila {i}: material_mayor={key!r} -- {row}')
    raise SystemExit(2)
else:
    print('\nTodas las claves pertenecen al conjunto permitido.')
