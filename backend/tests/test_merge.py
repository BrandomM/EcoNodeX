"""Tests for the taxa merge workflow."""
import pytest


def _setup(client):
    p = client.post('/api/projects', json={'name': 'Merge Test'}).json()
    loc = client.post('/api/locations', json={'project_id': p['id'], 'name': 'Loc 1'}).json()
    ev = client.post('/api/sampling/events', json={
        'project_id': p['id'], 'location_id': loc['id'], 'start_date': '2024-01-01'
    }).json()
    rep = client.post('/api/sampling/replicates', json={'event_id': ev['id'], 'code': 'R1'}).json()

    src = client.post('/api/taxa', json={
        'project_id': p['id'], 'scientific_name': 'Morfo A', 'rank': 'morphospecies'
    }).json()
    tgt = client.post('/api/taxa', json={
        'project_id': p['id'], 'scientific_name': 'Morfo B', 'rank': 'morphospecies'
    }).json()

    # Add records under src
    for _ in range(3):
        client.post('/api/records', json={
            'replicate_id': rep['id'], 'taxon_id': src['id'], 'individual_count': 5
        })

    return p, src, tgt


def test_merge_preview(client):
    p, src, tgt = _setup(client)
    r = client.post('/api/taxa/merge/preview', json={
        'source_taxon_id': src['id'],
        'target_taxon_id': tgt['id'],
    })
    assert r.status_code == 200
    data = r.json()
    assert data['records_affected'] == 3
    assert data['source_taxon_id'] == src['id']
    assert data['target_taxon_id'] == tgt['id']


def test_merge_requires_confirmar(client):
    p, src, tgt = _setup(client)
    r = client.post('/api/taxa/merge/execute', json={
        'source_taxon_id': src['id'],
        'target_taxon_id': tgt['id'],
        'confirmation': 'confirmar',  # wrong case
    })
    assert r.status_code == 400


def test_merge_execute_remaps_records(client):
    p, src, tgt = _setup(client)
    r = client.post('/api/taxa/merge/execute', json={
        'source_taxon_id': src['id'],
        'target_taxon_id': tgt['id'],
        'confirmation': 'CONFIRMAR',
    })
    assert r.status_code == 200
    log = r.json()
    assert log['records_affected'] == 3

    # Source taxon should no longer exist
    r2 = client.get(f"/api/taxa/{src['id']}")
    assert r2.status_code == 404

    # Target should still exist
    r3 = client.get(f"/api/taxa/{tgt['id']}")
    assert r3.status_code == 200

    # All records should now point to target
    records = client.get(f"/api/records?project_id={p['id']}").json()
    for rec in records:
        assert rec['taxon_id'] == tgt['id']


def test_merge_same_taxon_blocked(client):
    p, src, tgt = _setup(client)
    r = client.post('/api/taxa/merge/execute', json={
        'source_taxon_id': src['id'],
        'target_taxon_id': src['id'],
        'confirmation': 'CONFIRMAR',
    })
    assert r.status_code == 400


def test_merge_logs_recorded(client):
    p, src, tgt = _setup(client)
    client.post('/api/taxa/merge/execute', json={
        'source_taxon_id': src['id'],
        'target_taxon_id': tgt['id'],
        'confirmation': 'CONFIRMAR',
    })
    logs = client.get(f"/api/taxa/merge/logs?project_id={p['id']}").json()
    assert len(logs) >= 1
    assert logs[0]['source_taxon_name'] == 'Morfo A'
    assert logs[0]['records_affected'] == 3
