"""Build CAPC_CBC_1971_2025_v3.csv from v2, Audubon's export and Steve Hampton's compiler table.

Usage:
  python3 tools/build_capc_v3.py [--decisions CAPC_review_decisions.csv] --v2 data/CAPC_CBC_1971_2025_v2.csv \
      --audubon "HistoricalResultsByCount [CAPC-1901-2025].csv" --out-dir data

Rules:
  1971-2020  keep v2 (Steve Hampton's table, current taxonomy). Cells change only through
             --decisions, the CSV exported from the compiler's Review tab.
  2021-2024  take Audubon's published value for every row; where Audubon left the cell blank,
             keep the compiler's value. Subspecies rows that only duplicate the species row are zeroed.
  2025       keep v2 (eBird compilation of 2025-12-21, provisional).

Writes CAPC_CBC_1971_2025_v3.csv, CAPC_v3_corrections.csv and CAPC_v3_review.csv.
"""
import argparse
import csv
import re
from pathlib import Path

YEARS = [str(y) for y in range(1971, 2026)]
AUDUBON_YEARS = [str(y) for y in range(2021, 2025)]

V2_TO_AUDUBON = {
    'California Scrub-Jay': ['Western Scrub-Jay'],
    'Great Blue Heron (Great Blue)': ['Great Blue Heron (Blue form)'],
    'Snow Goose (white form)': ['Snow Goose'],
    'Northern House Wren': ['House Wren'],
    'American Barn Owl': ['Barn Owl'],
    'American Herring Gull': ['Herring Gull'],
    'African Collared Dove': ['African Collared-Dove'],
    'sapsucker, sp.': ['sapsucker sp.'],
    'Red-breasted Sapsucker X Red-naped Sapsucker (hybrid)': ['Red-naped x Red-breasted Sapsucker (hybrid)'],
    "Yellow-rumped Warbler (Audubon's x Myrtle)": ["Yellow-rumped Warbler (Myrtle x Audubon's)"],
    'Oak Titmouse': ['Oak Titmouse', 'Oak/Juniper Titmouse (Plain Titmouse)'],
    'Pacific Wren': ['Pacific Wren', 'Pacific/Winter Wren'],
}



def read_audubon(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    out = {}
    start = next(i for i, r in enumerate(rows) if r[:2] == ['COM_NAME', 'CountYear'])
    for r in rows[start + 1:]:
        if len(r) < 3 or not r[0].strip():
            continue
        m = re.match(r'(\d{4}) \[', r[1] or '')
        if not m:
            continue
        name = r[0].split('\n')[0].strip()
        val = r[2].strip()
        out.setdefault(name, {})[m.group(1)] = int(val) if val.isdigit() else None
    return out


def fmt(v):
    return '' if v is None else str(int(v)) if float(v).is_integer() else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v2', type=Path, required=True)
    ap.add_argument('--audubon', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--decisions', type=Path, help='CAPC_review_decisions.csv exported from the compiler Review tab')
    a = ap.parse_args()

    with open(a.v2, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    for r in rows:
        for y in YEARS:
            r[y] = float(r[y]) if r.get(y) not in ('', None) else 0.0

    aud = read_audubon(a.audubon)
    byname = {r['Species']: r for r in rows}
    corrections, review = [], []

    def log(target, r, y, old, new, why, audval):
        target.append({'Species': r['Species'], 'Year': y, 'v2': fmt(old), 'v3': fmt(new), 'Audubon': fmt(audval), 'Reason': why})

    matched_aud = set()
    unmatched = []
    for r in rows:
        names = V2_TO_AUDUBON.get(r['Species']) or [n for n in [r['Species'], (r.get('eBird') or '').strip()] if n in aud][:1]
        names = [n for n in names if n in aud]
        if not names:
            unmatched.append(r)
            continue
        matched_aud.update(names)
        for y in AUDUBON_YEARS:
            vals = [aud[n].get(y) for n in names]
            old = r[y]
            if all(v is None for v in vals):
                if old:
                    log(review, r, y, old, old, 'Audubon left this blank; kept the compiler value', None)
                continue
            new = float(sum(v or 0 for v in vals))
            if new != old:
                r[y] = new
                log(corrections, r, y, old, new, 'Use Audubon published value', new)

    print('rows without an Audubon match that carry 2021-2024 counts:',
          [(r['Species'], [int(r[y]) for y in AUDUBON_YEARS]) for r in unmatched if any(r[y] for y in AUDUBON_YEARS)])
    for r in unmatched:
        for y in AUDUBON_YEARS:
            if r[y]:
                log(corrections, r, y, r[y], 0.0, 'Not in Audubon published results for this year (subspecies row duplicating the species total)', None)
                r[y] = 0.0

    for name, vals in aud.items():
        if name in matched_aud or name in byname:
            continue
        if any(vals.get(y) for y in AUDUBON_YEARS):
            new = {'Species': name, 'eBird': '', 'class': 'sp' if ' sp.' in name else ('slash' if '/' in name else '')}
            for y in YEARS:
                new[y] = 0.0
            for y in AUDUBON_YEARS:
                if vals.get(y):
                    new[y] = float(vals[y])
                    log(corrections, new, y, None, new[y], 'Row missing from v2; added from Audubon', new[y])
            rows.append(new)
            byname[name] = new

    if a.decisions:
        with open(a.decisions, encoding='utf-8-sig') as f:
            for d in csv.DictReader(f):
                choice = (d.get('decision') or '').strip()
                if choice not in ('cbc', 'other'):
                    continue
                targets = [n.strip() for n in (d.get('rows') or '').split(' + ') if n.strip()]
                y = str(d['year']).strip()
                if len(targets) != 1 or targets[0] not in byname or d.get('value') in ('', None):
                    review.append({'Species': d.get('rows') or d.get('group'), 'Year': y, 'v2': d.get('steve', ''), 'v3': d.get('steve', ''),
                                   'Audubon': d.get('cbc', ''), 'Reason': 'Decision could not be applied automatically (several rows or no value); edit by hand'})
                    continue
                r = byname[targets[0]]
                old, new = r[y], float(d['value'])
                if old != new:
                    note = (d.get('note') or '').strip()
                    log(corrections, r, y, old, new, ('Review decision: CBC value' if choice == 'cbc' else 'Review decision: other value') + (f' ({note})' if note else ''), d.get('cbc') or None)
                    r[y] = new

    a.out_dir.mkdir(parents=True, exist_ok=True)
    with open(a.out_dir / 'CAPC_CBC_1971_2025_v3.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\r\n')
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(c, '') if c not in YEARS else fmt(r[c]) for c in header])
    for name, data in [('CAPC_v3_corrections.csv', corrections), ('CAPC_v3_review.csv', review)]:
        with open(a.out_dir / name, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['Species', 'Year', 'v2', 'v3', 'Audubon', 'Reason'], lineterminator='\n')
            w.writeheader()
            w.writerows(sorted(data, key=lambda d: (int(d['Year']), d['Species'])))
    print(f'rows {len(rows)}, corrections {len(corrections)}, for review {len(review)}')


if __name__ == '__main__':
    main()
