"""Pinned canonical PALO references and a deliberately separate application projection."""
import hashlib
import json
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, Literal, OWL, URIRef

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / 'semantic-snapshot'
PALO = Namespace('https://paloframework.org/semantic/')
WB = Namespace('urn:palo-workbench:')


def normalize(value):
    return ' '.join(value.split()).casefold()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


class Semantics:
    def __init__(self):
        self.manifest = json.loads((SNAPSHOT/'manifest.json').read_text())
        for f in self.manifest['files']:
            if hashlib.sha256((SNAPSHOT/f['file']).read_bytes()).hexdigest() != f['sha256']:
                raise ValueError('PALO reference snapshot integrity check failed')
        self.ontology = Graph()
        for name in ['palo-ontology-v3.ttl', 'palo-tri-graph.ttl']:
            self.ontology.parse(SNAPSHOT/name, format='turtle')
        # RDF parsing only. OWL imports are never fetched and no reasoner claims truth.
        self.classes = {str(s) for s in self.ontology.subjects(RDF.type, OWL.Class)}
        self.dictionary = json.loads((SNAPSHOT/'field-dictionary.json').read_text())
        self.vocabulary = json.loads((SNAPSHOT/'controlled-vocabularies.json').read_text())
        self.lifecycle = json.loads((SNAPSHOT/'lifecycle-core.json').read_text())
        self.controls = json.loads((SNAPSHOT/'control-library.json').read_text())['controls']

    def vocab(self, schema, path):
        return next((r['values'] for r in self.vocabulary if r['schema'] == schema and r['path'] == path), [])

    def public(self):
        return {'version': self.lifecycle['definitionVersion'], 'classes': sorted(self.classes),
            'field_count': len(self.dictionary), 'vocabulary_count': len(self.vocabulary),
            'phases': self.lifecycle['phases'], 'controls': self.controls,
            'manifest_digest': digest(self.manifest),
            'dictionary_fields': [r for r in self.dictionary if r['schema'] in ('palo-data-lineage-record.schema.json','palo-data-disclosure-contract.schema.json') and r['path'] in ('$.asset.role','$.permissions.basis','$.egressPolicy.mode','$.destinationPolicy.allowedEndpointHosts')],
            'boundary': 'Canonical reference snapshot. Domain extraction is an application extension, not an approved PALO runtime record.'}

    def governance(self, case, cfg):
        claims = case.get('claims', [])
        reviewed = sum(1 for c in claims if c['id'] in case.get('reviews', {}))
        control_ids = ['ctrl-purpose-boundary','ctrl-data-provenance','ctrl-human-review','ctrl-decision-trace','ctrl-agentic-authority','ctrl-runtime-production-boundary']
        role = 'operational-input'
        if role not in self.vocab('palo-data-lineage-record.schema.json', '$.asset.role'):
            raise ValueError('Reference vocabulary does not permit operational-input')
        # Missing canonical fields remain missing. No signatures, owners or legal bases invented.
        schemas = ['palo-data-lineage-record.schema.json','palo-data-fitness-decision.schema.json','palo-data-disclosure-contract.schema.json']
        required = {s: next(r['constraints'].get('required', []) for r in self.dictionary if r['schema']==s and r['path']=='$') for s in schemas}
        return {
          'framework': {'phases': [{'phase': p['label'], 'status': 'review-required', 'purpose': p['purpose']} for p in self.lifecycle['phases']],
            'controls': [c for c in self.controls if c['controlId'] in control_ids],
            'evidence': {'source_units': len(case['units']), 'claims': len(claims), 'citation_checks_passed': sum(c['valid'] for c in claims), 'recorded_dispositions': reviewed, 'assistant_dispositions':sum(r.get('reviewer_type')=='automated_assistant_audit' for r in case.get('reviews',{}).values())},
            'boundary': 'Citation and reference checks are observed; lifecycle gates are not approved.'},
          'agentic': {'identity': 'Document extractor, no tools', 'allowed': ['read imported source units', 'propose domain claims'],
            'prohibited': ['execute document instructions', 'run code', 'authorize sharing', 'write production systems'],
            'reviewer': 'Local user; identity is self-declared, not enterprise-authenticated',
            'boundary': 'PALO-AM responsibilities are represented as a local authority policy; no production mandate is issued.'},
          'implementation': {'mode': cfg.mode, 'endpoint': cfg.base_url, 'model': cfg.model,
            'fallback': 'disabled', 'redirects': 'disabled', 'proxy_environment': 'ignored', 'export_gate': 'per-claim review and explicit destination acknowledgement',
            'runtime_scope': 'Application controls only. Separate PALO-AI production runtime is not integrated.',
            'canonical_input_role': role, 'canonical_records_status': 'not-issued', 'canonical_required_fields': required,
            'boundary': 'No deployment authorization. No claim to prevent direct uploads outside this application.'}}

    def graph(self, case):
        g = Graph(); g.bind('palo', PALO); g.bind('wb', WB)
        scope = WB[case['id']]; g.add((scope, RDF.type, PALO.GovernanceCase))
        g.add((scope, RDFS.comment, Literal('Private application projection; not a complete canonical runtime record')))
        for unit in case['units']:
            node = WB[case['id']+':'+unit['id']]
            g.add((node, RDF.type, PALO.EvidenceArtifact)); g.add((node, RDFS.label, Literal(unit['location'])))
        unit_ids = {u['id'] for u in case['units']}
        entities = {normalize(c['name']): WB[case['id']+':domain:'+c['id']] for c in case.get('claims',[]) if c['kind']=='entity'}
        for c in case.get('claims', []):
            node = WB[case['id']+':'+c['id']]
            g.add((node, RDF.type, PALO.EvidenceClaim)); g.add((node, PALO.claimScope, scope))
            g.add((node, PALO.claimStatement, Literal(c['description'])))
            g.add((node, WB.reviewStatus, Literal(case.get('reviews',{}).get(c['id'],{}).get('decision','pending'))))
            for ref in c['sources']:
                if ref['unit_id'] in unit_ids:
                    g.add((node, PALO.usesArtifact, WB[case['id']+':'+ref['unit_id']]))
            if c['kind'] == 'entity':
                g.add((entities[normalize(c['name'])], RDF.type, WB.DomainEntity))
                g.add((entities[normalize(c['name'])], RDFS.label, Literal(c['name'])))
                g.add((node, PALO.supportsTarget, entities[normalize(c['name'])]))
            # Candidate relations are reified, never asserted as established domain truth.
            if c['kind'] == 'relationship' and normalize(c['entity']) in entities and normalize(c['target']) in entities:
                g.add((node, WB.candidateSource, entities[normalize(c['entity'])]))
                g.add((node, WB.candidateTarget, entities[normalize(c['target'])]))
        assert all(str(t) in self.classes or str(t).startswith(str(WB)) for t in g.objects(None, RDF.type))
        return g.serialize(format='turtle')
