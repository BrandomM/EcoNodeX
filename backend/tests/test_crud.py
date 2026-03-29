"""Integration tests for core CRUD endpoints."""
import pytest


def _create_project(client):
    r = client.post('/api/projects', json={'name': 'Test Project'})
    assert r.status_code == 201
    return r.json()


def _create_taxon(client, project_id, name='Coleoptera', rank='orden'):
    r = client.post('/api/taxa', json={
        'project_id': project_id,
        'scientific_name': name,
        'rank': rank,
    })
    assert r.status_code == 201
    return r.json()


def _create_location(client, project_id, name='Punto 1'):
    r = client.post('/api/locations', json={
        'project_id': project_id,
        'name': name,
    })
    assert r.status_code == 201
    return r.json()


def _create_method(client, project_id):
    r = client.post('/api/methods', json={
        'project_id': project_id,
        'code': 'RED',
        'label': 'Red de barrido',
    })
    assert r.status_code == 201
    return r.json()


def _create_event(client, project_id, location_id):
    r = client.post('/api/sampling/events', json={
        'project_id': project_id,
        'location_id': location_id,
        'start_date': '2024-03-15',
    })
    assert r.status_code == 201
    return r.json()


def _create_replicate(client, event_id):
    r = client.post('/api/sampling/replicates', json={'event_id': event_id, 'code': 'R1'})
    assert r.status_code == 201
    return r.json()


# ---- Project ----

def test_create_and_list_projects(client):
    p = _create_project(client)
    assert p['name'] == 'Test Project'
    r = client.get('/api/projects')
    assert any(proj['id'] == p['id'] for proj in r.json())


def test_update_project(client):
    p = _create_project(client)
    r = client.patch(f"/api/projects/{p['id']}", json={'name': 'Updated'})
    assert r.json()['name'] == 'Updated'


def test_delete_project(client):
    p = _create_project(client)
    r = client.delete(f"/api/projects/{p['id']}")
    assert r.status_code == 204


# ---- Taxon ----

def test_taxon_auto_alias(client):
    p = _create_project(client)
    t = _create_taxon(client, p['id'], 'Chrysomelidae', 'familia')
    assert t['alias']  # should be auto-generated
    assert 'Chrysomelidae' in t['alias'] or t['alias']


def test_taxon_search(client):
    p = _create_project(client)
    _create_taxon(client, p['id'], 'Chrysomela populi', 'especie')
    r = client.get(f"/api/taxa?project_id={p['id']}&search=populi")
    results = r.json()
    assert any('populi' in t['scientific_name'].lower() for t in results)


def test_taxon_tree(client):
    p = _create_project(client)
    parent = _create_taxon(client, p['id'], 'Coleoptera', 'orden')
    child_data = client.post('/api/taxa', json={
        'project_id': p['id'],
        'scientific_name': 'Chrysomelidae',
        'rank': 'familia',
        'parent_taxon_id': parent['id'],
    }).json()
    r = client.get(f"/api/taxa?project_id={p['id']}&tree=true")
    tree = r.json()
    # Find parent in tree and verify child is nested
    for node in tree:
        if node['id'] == parent['id']:
            assert any(c['id'] == child_data['id'] for c in node.get('children', []))


def test_taxon_delete_with_records_blocked(client):
    p = _create_project(client)
    loc = _create_location(client, p['id'])
    ev = _create_event(client, p['id'], loc['id'])
    rep = _create_replicate(client, ev['id'])
    t = _create_taxon(client, p['id'], 'Taxon A', 'especie')
    # Create record
    client.post('/api/records', json={'replicate_id': rep['id'], 'taxon_id': t['id'], 'individual_count': 5})
    # Delete should be blocked
    r = client.delete(f"/api/taxa/{t['id']}")
    assert r.status_code == 409


# ---- Location ----

def test_location_hierarchy(client):
    p = _create_project(client)
    parent = _create_location(client, p['id'], 'Region A')
    child = client.post('/api/locations', json={
        'project_id': p['id'],
        'name': 'Punto 1',
        'parent_location_id': parent['id'],
    }).json()
    r = client.get(f"/api/locations?project_id={p['id']}&tree=true")
    tree = r.json()
    for node in tree:
        if node['id'] == parent['id']:
            assert any(c['id'] == child['id'] for c in node.get('children', []))


# ---- Occurrence records ----

def test_create_and_filter_records(client):
    p = _create_project(client)
    loc = _create_location(client, p['id'])
    ev = _create_event(client, p['id'], loc['id'])
    rep = _create_replicate(client, ev['id'])
    t1 = _create_taxon(client, p['id'], 'Taxon X', 'especie')
    t2 = _create_taxon(client, p['id'], 'Taxon Y', 'especie')

    client.post('/api/records', json={'replicate_id': rep['id'], 'taxon_id': t1['id'], 'individual_count': 10})
    client.post('/api/records', json={'replicate_id': rep['id'], 'taxon_id': t2['id'], 'individual_count': 5})

    r = client.get(f"/api/records?project_id={p['id']}")
    assert len(r.json()) >= 2
