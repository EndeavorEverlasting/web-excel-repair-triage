from __future__ import annotations
import hashlib, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('phase_c_builder',ROOT/'scripts/build_prompt_topology_viewer.py');mod=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(mod)

def ch(payload): return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def fixture():
    topology={'schema_version':'prompt-topology-artifact/v1','content_hash_sha256':'a'*64,'nodes':[{'prompt_id':'P00','seq':'00','title':'Alpha','prompt_type':'DISCOVER','prompt_class':'TEST','family_declared':'Foundation','family_declared_id':'foundation','keywords':['alpha'],'category':'standard'},{'prompt_id':'P01','seq':'01','title':'Beta','prompt_type':'BUILD','prompt_class':'TEST','family_declared':'Build','family_declared_id':'build-repair','keywords':['beta'],'category':'standard'}],'edges':[{'source':'P00','target':'P01','strength_micros':900000,'channels':[{'type':'SEMANTIC_NEIGHBOR'}]}],'clusters':[{'cluster_id':'C-TEST','member_count':2,'member_prompt_ids':['P00','P01'],'representative_prompt_id':'P00','family_candidate_id':'foundation','lineage':'NEW'}],'opportunities':[{'cluster_id':'C-TEST','prompt_ids':['P00','P01'],'recommended_action':'INVESTIGATE','score':12,'sector_id':'C-TEST','state':'UNDERDEVELOPED'}],'outlier_prompt_ids':[]}
    projection={'schema_version':'1.0.0','algorithm':'umap','parameters':{'n_components':3},'points':{'P00':{'x':0.1,'y':0.2,'z':0.3},'P01':{'x':-0.1,'y':-0.2,'z':-0.3}}}
    state={'schema_version':'prompt-topology-projection-state/v1','epoch_id':'E-TEST','parent_epoch_id':None,'topology_content_hash_sha256':topology['content_hash_sha256'],'projection_sha256':ch(projection),'prompt_count':2,'content_hash_sha256':'b'*64,'alignment':{},'provenance':{}}
    return topology,projection,state

class PhaseCViewerTests(unittest.TestCase):
    def test_fixture_build_is_deterministic_and_self_contained(self):
        t,p,s=fixture(); a=mod.render_document(mod.compact_payload(t,p,s)); b=mod.render_document(mod.compact_payload(t,p,s));self.assertEqual(a,b);self.assertIn('Prompt Topology Universe',a);self.assertIn('window.PROMPT_TOPOLOGY_DATA=',a);self.assertNotIn('<script src=',a);self.assertNotIn('<link rel="stylesheet"',a);self.assertIn('Text index · 2 prompts',a);self.assertIn('id="prompt-P00"',a)
    def test_exact_hash_binding_and_prompt_point_parity(self):
        t,p,s=fixture();mod.validate_inputs(t,p,s)
        bad=dict(s);bad['topology_content_hash_sha256']='f'*64
        with self.assertRaisesRegex(mod.ViewerBuildError,'topology/state'):mod.validate_inputs(t,p,bad)
        badp=json.loads(json.dumps(p));badp['points'].pop('P01')
        bads=dict(s);bads['projection_sha256']=ch(badp)
        with self.assertRaisesRegex(mod.ViewerBuildError,'parity'):mod.validate_inputs(t,badp,bads)
    def test_duplicate_prompt_ids_fail_closed(self):
        t,p,s=fixture();t['nodes'].append(dict(t['nodes'][0]))
        with self.assertRaisesRegex(mod.ViewerBuildError,'duplicate'):mod.validate_inputs(t,p,s)
    def test_projection_hash_tamper_fails_closed(self):
        t,p,s=fixture();bad=json.loads(json.dumps(p));bad['points']['P00']['x']=0.9
        with self.assertRaisesRegex(mod.ViewerBuildError,'projection/state'):mod.validate_inputs(t,bad,s)
    def test_viewer_source_has_no_collection_or_persistence_apis(self):
        source=(ROOT/'docs/prompt-topology-viewer.js').read_text(encoding='utf-8')
        for forbidden in ('fetch(','XMLHttpRequest','WebSocket','EventSource','sendBeacon','localStorage','sessionStorage'):
            self.assertNotIn(forbidden,source)
    def test_contract_preserves_semantic_boundary(self):
        c=json.loads((ROOT/'harness/prompt-topology/phase-c-viewer.v1.json').read_text())
        self.assertIn('projection-driven classification',c['forbidden']);self.assertIn('registry mutation',c['forbidden']);self.assertFalse(c['privacy']['telemetry']);self.assertFalse(c['privacy']['persistent_browser_storage'])
if __name__=='__main__':unittest.main()
