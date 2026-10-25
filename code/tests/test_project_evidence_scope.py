import importlib.util
import json
from pathlib import Path


def test_scoped_export_never_opens_unselected_source_and_preserves_history(tmp_path, monkeypatch):
    path = Path(__file__).parents[1] / 'scripts/export_project_evidence.py'
    spec = importlib.util.spec_from_file_location('scoped_export', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    source = tmp_path / 'code/outputs/current.json'; source.parent.mkdir(parents=True)
    source.write_text('{"current":true}')
    evidence = tmp_path / 'evidence'; evidence.mkdir()
    historical = {'result_id': 'OLD', 'files': [{'source_path': 'forbidden/secret.json', 'snapshot_path': 'forbidden/snapshot.json'}]}
    (evidence / 'EVIDENCE_MANIFEST.json').write_text(json.dumps({'results': [historical]}))
    monkeypatch.setattr(m, '_source_pairs', lambda: {'OLD': [('forbidden/secret.json','secret.json')], 'NEW': [('code/outputs/current.json','current.json')]})
    manifest = m.export_evidence(tmp_path, {'NEW'})
    assert manifest['results'][0] == historical
    assert m.verify_evidence(tmp_path, {'NEW'}) == []
    assert not (tmp_path / 'forbidden').exists()
