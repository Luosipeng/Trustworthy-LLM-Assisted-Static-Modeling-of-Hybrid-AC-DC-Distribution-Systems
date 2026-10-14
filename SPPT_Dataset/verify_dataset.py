"""Read-only dataset integrity and DC interchange validation (Python stdlib)."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SPPT = 'urn:sppt:dataset:v1#'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gzjson(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def verify():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['name'] == 'SPPT_Dataset' and len(manifest['cases']) == 4
    expected = set(manifest['files']) | {'manifest.json'}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    assert actual == expected, ('Unexpected or missing files', actual ^ expected)
    for name, info in manifest['files'].items():
        path = ROOT / name
        assert sha(path) == info['sha256'] and path.stat().st_size == info['bytes'], name
    for case, info in manifest['cases'].items():
        folder = ROOT / case
        native = (folder / info['native_file']).read_bytes()
        hybrid = (folder / info['hybrid_file']).read_bytes()
        if info['representation'] == 'GLM':
            split = b'\n// BEGIN SPPT_DC_EXTENSION_V1'
            assert hybrid.split(split, 1)[0] == native
            block = hybrid.split(split, 1)[1].decode('utf-8')
            records = []
            for kind, body in re.findall(r'object sppt_(\w+) \{(.*?)\n\}', block, re.S):
                fields = {}
                for key, token in re.findall(r'^  (\w+) (.*);$', body, re.M):
                    if key != 'name':
                        fields[key] = json.loads(token)
                records.append([kind, fields])
        else:
            start, end = b'<!-- BEGIN SPPT_DC_EXTENSION_V1 -->\n', b'<!-- END SPPT_DC_EXTENSION_V1 -->\n'
            prefix, rest = hybrid.split(start, 1)
            block, tail = rest.split(end, 1)
            assert prefix + tail == native
            tree = ET.fromstring(hybrid)
            records = []
            uris = {e.get('{' + RDF + '}about') for e in tree if e.get('{' + RDF + '}about')}
            for item in tree:
                if not item.tag.startswith('{' + SPPT + '}'):
                    continue
                kind = item.tag.split('}')[1]
                fields = {}
                for child in item:
                    key = child.tag.split('}')[1]
                    fields[key] = child.text if child.get('type') == 'string' else json.loads(child.text)
                    target = child.get('{' + RDF + '}resource')
                    if target:
                        assert target in uris, (case, target)
                records.append([kind, fields])
        assert records == info['expected_overlay_records'], (case, 'DC export differs')
        snapshot = gzjson(folder / 'H_src.json.gz')
        assert snapshot['source_hash'] == sha(folder / info['native_file']) == info['native_sha256']
        assert sha(folder / 'H_src.json.gz') == info['snapshot_sha256']
        assert sha(folder / 'rich_model.json.gz') == info['rich_sha256']
        overlay = json.loads((folder / 'dc_overlay.json').read_text(encoding='utf-8'))
        s = gzjson(folder / 'rich_model.json.gz')['S_hat']
        nodes = {n['id'] for n in s['N']}
        devices = {d['id'] for d in s['D']}
        assert len(nodes) == len(s['N']) and len(devices) == len(s['D'])
        assert {n['id'] for n in s['N'] if n['domain'] == 'DC'} == set(overlay['dc_bus_ids'])
        for kind, fields in records:
            if kind == 'terminal':
                t = fields['id']
                assert s['delta'][t] == fields['owner'] in devices
                assert s['nu'][t] == fields['node'] in nodes
                assert s['terminal_domains'][t] == fields['domain']
                assert {k: fields[k] for k in ['owner', 'node', 'domain']} == overlay['terminal_associations'][t]
            elif kind in ['dc_line', 'vsc']:
                key = fields['id']
                assert {k[6:]: v for k, v in fields.items() if k.startswith('param_')} == s['a'][key]
                assert {k[5:]: v for k, v in fields.items() if k.startswith('ctrl_')} == s['kappa'][key]
        provenance = gzip.decompress((folder / 'normalization_provenance.json.gz').read_bytes())
        assert hashlib.sha256(provenance).hexdigest() == info['normalization_provenance_sha256']
        json.loads(provenance)
        validation = json.loads((folder / 'baseline_validation.json').read_text(encoding='utf-8'))
        assert validation['Admit_SPPT'] and all(x is True for x in validation['gates'].values())
        print(case + ': PASS (hashes, unchanged AC data, DC parameters/terminals, saved baseline checks)')
    print('SPPT_Dataset: PASS; no network request or power-flow run performed')


if __name__ == '__main__':
    verify()
