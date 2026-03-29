"""Tests for export endpoints: shape, format, DwC-A structure."""
import io
import zipfile
import csv
import pytest


def _full_setup(client):
    """Create a minimal but complete dataset for export testing."""
    p = client.post('/api/projects', json={'name': 'Export Test'}).json()
    loc = client.post('/api/locations', json={'project_id': p['id'], 'name': 'Loc 1', 'latitude': -17.5, 'longitude': -66.2}).json()
    method = client.post('/api/methods', json={'project_id': p['id'], 'code': 'RED', 'label': 'Red barrido'}).json()
    ev = client.post('/api/sampling/events', json={
        'project_id': p['id'], 'location_id': loc['id'], 'start_date': '2024-03-15'
    }).json()
    rep = client.post('/api/sampling/replicates', json={
        'event_id': ev['id'], 'code': 'R1', 'method_id': method['id']
    }).json()
    t1 = client.post('/api/taxa', json={'project_id': p['id'], 'scientific_name': 'Taxon A', 'rank': 'especie'}).json()
    t2 = client.post('/api/taxa', json={'project_id': p['id'], 'scientific_name': 'Taxon B', 'rank': 'especie'}).json()
    client.post('/api/records', json={'replicate_id': rep['id'], 'taxon_id': t1['id'], 'individual_count': 5})
    client.post('/api/records', json={'replicate_id': rep['id'], 'taxon_id': t2['id'], 'individual_count': 3})
    return p, loc, method, ev, rep, t1, t2


def _read_csv_from_bytes(b):
    text = b.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ---- CSV exports ----

def test_taxa_csv(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/csv/taxa?project_id={p['id']}")
    assert r.status_code == 200
    rows = _read_csv_from_bytes(r.content)
    assert len(rows) >= 2
    assert 'scientific_name' in rows[0]


def test_records_csv(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/csv/records?project_id={p['id']}")
    assert r.status_code == 200
    rows = _read_csv_from_bytes(r.content)
    assert len(rows) == 2
    assert 'individual_count' in rows[0]


def test_abundance_matrix(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/csv/abundance-matrix?project_id={p['id']}")
    assert r.status_code == 200
    rows = _read_csv_from_bytes(r.content)
    assert len(rows) >= 1
    assert 'replicate_code' in rows[0]


def test_presence_absence_matrix(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/csv/presence-absence-matrix?project_id={p['id']}")
    assert r.status_code == 200
    rows = _read_csv_from_bytes(r.content)
    for row in rows:
        for key, val in row.items():
            if key not in ('replicate_id', 'event_id', 'replicate_code'):
                assert val in ('0', '1')


# ---- DwC-A ----

def test_dwca_structure(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/dwca?project_id={p['id']}")
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert 'meta.xml'        in names
    assert 'event.csv'       in names
    assert 'occurrence.csv'  in names
    assert 'taxon.csv'       in names
    assert 'multimedia.csv'  in names


def test_dwca_occurrence_rows(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/dwca?project_id={p['id']}")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    occ_text = zf.read('occurrence.csv').decode('utf-8')
    rows = list(csv.DictReader(io.StringIO(occ_text)))
    assert len(rows) == 2
    for row in rows:
        assert row['basisOfRecord'] == 'HumanObservation'
        assert row['occurrenceStatus'] in ('present', 'absent')


def test_dwca_meta_xml_content(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/dwca?project_id={p['id']}")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    meta = zf.read('meta.xml').decode('utf-8')
    assert 'http://rs.tdwg.org/dwc/terms/Event' in meta
    assert 'http://rs.tdwg.org/dwc/terms/Occurrence' in meta


# ---- Excel ----

def test_excel_structure(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/excel?project_id={p['id']}")
    assert r.status_code == 200
    # Check it's a valid ZIP (xlsx is a zip)
    assert zipfile.is_zipfile(io.BytesIO(r.content))


# ---- Project ZIP ----

def test_project_export_zip(client):
    p, *_ = _full_setup(client)
    r = client.get(f"/api/exports/project?project_id={p['id']}&include_photos=false")
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert 'manifest.json' in names
    assert 'econodex.db'   in names
    assert 'csv/taxa.csv'  in names
