from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-storage-lifecycle.js"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


def node_json(body: str) -> dict:
    prelude = r"""
const lifecycle=require('./docs/prompt-kit-storage-lifecycle.js');
function storage(seed){
  return{
    data:Object.assign({},seed||{}),
    failWrites:false,
    getItem(k){return Object.prototype.hasOwnProperty.call(this.data,k)?this.data[k]:null},
    setItem(k,v){if(this.failWrites)throw new Error('quota');this.data[k]=String(v)},
    removeItem(k){delete this.data[k]}
  }
}
"""
    completed = subprocess.run(
        ["node", "-e", prelude + body],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class PromptKitStorageLifecycleRuntimeTests(unittest.TestCase):
    def test_runtime_is_parseable_and_policy_matches_contract(self) -> None:
        subprocess.run(["node", "--check", str(RUNTIME)], cwd=ROOT, check=True)
        proof = node_json(
            r"""
const p=lifecycle.POLICIES;
console.log(JSON.stringify({
  schema:lifecycle.SCHEMA,
  journal:[p.local_journal.maxAgeMs,p.local_journal.maxBytes],
  reducer:[p.privacy_reducer_buffer.maxAgeMs,p.privacy_reducer_buffer.maxBytes,p.privacy_reducer_buffer.maxItems],
  retry:[p.sync_retry_queue.maxAgeMs,p.sync_retry_queue.maxBytes,p.sync_retry_queue.maxItems],
  polling:[p.polling_state.maxAgeMs,p.polling_state.maxItems],
  personal:lifecycle.PERSONAL_STATE_KEYS,
  usage:lifecycle.EXTERNAL_USAGE_KEY
}));
"""
        )
        day = 24 * 60 * 60 * 1000
        self.assertEqual(proof["schema"], "prompt-kit-storage-lifecycle/v1")
        self.assertEqual(proof["journal"], [14 * day, 2097152])
        self.assertEqual(proof["reducer"], [30 * day, 524288, 2048])
        self.assertEqual(proof["retry"], [7 * day, 262144, 64])
        self.assertEqual(proof["polling"], [day, 1])
        self.assertIn("promptKit.favoritePromptIds.v1", proof["personal"])
        self.assertIn("promptKit.profileSlots.v1", proof["personal"])
        self.assertEqual(proof["usage"], "promptKit.usage.v1")

    def test_journal_cleanup_expires_old_records_and_bounds_bytes(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const day=24*60*60*1000;const now=40*day;
const key=c.storageKey('local_journal');
s.data[key]=JSON.stringify({schema:lifecycle.SCHEMA,store:'local_journal',items:[
  {at:now-15*day,value:'expired'},
  {at:now-day,value:'fresh'}
]});
c.cleanupStore('local_journal',now);
const after=JSON.parse(s.data[key]);
const chunk='x'.repeat(900000);
c.append('local_journal',chunk,{at:now+1});
c.append('local_journal',chunk,{at:now+2});
c.append('local_journal',chunk,{at:now+3});
console.log(JSON.stringify({
  remaining:after.items.map(x=>x.value),
  count:c.inspect('local_journal',now+3).items.length,
  bytes:Buffer.byteLength(s.data[key]),
  limit:lifecycle.POLICIES.local_journal.maxBytes
}));
"""
        )
        self.assertEqual(proof["remaining"], ["fresh"])
        self.assertLessEqual(proof["bytes"], proof["limit"])
        self.assertLessEqual(proof["count"], 2)

    def test_reducer_retry_and_polling_counts_are_hard_bounded(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const now=1000000000;
function seed(name,count,withIds){
  const key=c.storageKey(name);const items=[];
  for(let i=0;i<count;i++)items.push(Object.assign({at:now-i,value:i},withIds?{id:'k'+i}:{}));
  s.data[key]=JSON.stringify({schema:lifecycle.SCHEMA,store:name,items});
  c.cleanupStore(name,now);
}
seed('privacy_reducer_buffer',2100,true);
seed('sync_retry_queue',80,false);
c.append('polling_state',{cursor:'first'},{at:now});
c.append('polling_state',{cursor:'second'},{at:now+1});
console.log(JSON.stringify({
  reducer:c.inspect('privacy_reducer_buffer',now).items.length,
  retry:c.inspect('sync_retry_queue',now).items.length,
  polling:c.inspect('polling_state',now+1).items
}));
"""
        )
        self.assertEqual(proof["reducer"], 2048)
        self.assertEqual(proof["retry"], 64)
        self.assertEqual(len(proof["polling"]), 1)
        self.assertEqual(proof["polling"][0]["value"]["cursor"], "second")

    def test_reducer_requires_aggregate_identity_and_deduplicates(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const now=5000;
const missing=c.append('privacy_reducer_buffer',{count:1},{at:now});
const first=c.append('privacy_reducer_buffer',{count:1},{at:now,id:'P07:success'});
const second=c.append('privacy_reducer_buffer',{count:2},{at:now+1,id:'P07:success'});
console.log(JSON.stringify({missing,first,second,items:c.inspect('privacy_reducer_buffer',now+1).items}));
"""
        )
        self.assertFalse(proof["missing"]["ok"])
        self.assertEqual(proof["missing"]["reason"], "aggregate-id-required")
        self.assertTrue(proof["first"]["ok"])
        self.assertTrue(proof["second"]["ok"])
        self.assertEqual(len(proof["items"]), 1)
        self.assertEqual(proof["items"][0]["value"]["count"], 2)

    def test_polling_cursor_expires_after_24_hours(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const day=24*60*60*1000;
c.append('polling_state',{cursor:'abc'},{at:1000});
c.cleanupStore('polling_state',1000+day+1);
console.log(JSON.stringify({items:c.inspect('polling_state',1000+day+1).items}));
"""
        )
        self.assertEqual(proof["items"], [])

    def test_storage_pressure_blocks_disposable_writes_without_deleting_personal_state(self) -> None:
        proof = node_json(
            r"""
const personal='promptKit.profileSlots.v1';const s=storage({[personal]:'personal-value'});const c=lifecycle.create(s);
s.failWrites=true;
const first=c.append('local_journal',{event:'x'},{at:1000});
const second=c.append('sync_retry_queue',{event:'y'},{at:1001});
console.log(JSON.stringify({first,second,status:c.status(),personal:s.data[personal]}));
"""
        )
        self.assertFalse(proof["first"]["ok"])
        self.assertEqual(proof["first"]["reason"], "storage-pressure")
        self.assertFalse(proof["second"]["ok"])
        self.assertEqual(proof["second"]["reason"], "writes-blocked")
        self.assertTrue(proof["status"]["writesBlocked"])
        self.assertEqual(proof["personal"], "personal-value")

    def test_automatic_cleanup_never_touches_personal_or_secret_compatible_state(self) -> None:
        proof = node_json(
            r"""
const seed={
  'promptKit.favoritePromptIds.v1':'["P07"]',
  'promptKit.profileSlots.v1':'not-our-json',
  'promptKit.secrets.v1':'opaque-secret',
  'promptKit.localJournal.v1':'malformed-disposable'
};
const s=storage(seed);const c=lifecycle.create(s);c.cleanupAll(1000);
console.log(JSON.stringify({data:s.data}));
"""
        )
        self.assertEqual(proof["data"]["promptKit.favoritePromptIds.v1"], '["P07"]')
        self.assertEqual(proof["data"]["promptKit.profileSlots.v1"], "not-our-json")
        self.assertEqual(proof["data"]["promptKit.secrets.v1"], "opaque-secret")

    def test_manual_clear_operations_are_separated_and_personal_delete_is_confirmed(self) -> None:
        proof = node_json(
            r"""
const seed={
  'promptKit.usage.v1':'usage',
  'promptKit.localJournal.v1':'journal',
  'promptKit.privacyReducerBuffer.v1':'collective',
  'promptKit.syncRetryQueue.v1':'retry',
  'promptKit.pollingState.v1':'poll',
  'promptKit.favoritePromptIds.v1':'favorites',
  'promptKit.profileSlots.v1':'profiles'
};
const s=storage(seed);const c=lifecycle.create(s);
c.clearUsageAndJournal();
const afterUsage=Object.assign({},s.data);
const denied=c.clearPersonalState('wrong');
const afterDenied=Object.assign({},s.data);
const deleted=c.clearPersonalState(lifecycle.DELETE_CONFIRMATION);
console.log(JSON.stringify({afterUsage,denied,afterDenied,deleted,final:s.data}));
"""
        )
        self.assertNotIn("promptKit.usage.v1", proof["afterUsage"])
        self.assertNotIn("promptKit.localJournal.v1", proof["afterUsage"])
        self.assertIn("promptKit.privacyReducerBuffer.v1", proof["afterUsage"])
        self.assertIn("promptKit.favoritePromptIds.v1", proof["afterUsage"])
        self.assertFalse(proof["denied"]["ok"])
        self.assertIn("promptKit.favoritePromptIds.v1", proof["afterDenied"])
        self.assertTrue(proof["deleted"]["ok"])
        self.assertNotIn("promptKit.favoritePromptIds.v1", proof["final"])
        self.assertNotIn("promptKit.profileSlots.v1", proof["final"])
        self.assertIn("promptKit.privacyReducerBuffer.v1", proof["final"])

    def test_reducer_accepts_prototype_named_aggregate_ids(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const now=9000;
const ids=['__proto__','constructor','toString'];
const writes=ids.map((id,index)=>c.append('privacy_reducer_buffer',{count:index+1},{at:now+index,id}));
console.log(JSON.stringify({writes,ids:c.inspect('privacy_reducer_buffer',now+ids.length).items.map(item=>item.id).sort()}));
"""
        )
        self.assertTrue(all(item["ok"] for item in proof["writes"]))
        self.assertEqual(proof["ids"], ["__proto__", "constructor", "toString"])

    def test_oversized_item_is_rejected_without_blocking_other_stores(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);
const tooBig=c.append('local_journal','x'.repeat(3*1024*1024),{at:1000});
const afterOversize=c.status();
const valid=c.append('sync_retry_queue',{event:'still-allowed'},{at:1001});
console.log(JSON.stringify({tooBig,afterOversize,valid,finalStatus:c.status()}));
"""
        )
        self.assertFalse(proof["tooBig"]["ok"])
        self.assertEqual(proof["tooBig"]["reason"], "item-exceeds-store-bounds")
        self.assertFalse(proof["afterOversize"]["writesBlocked"])
        self.assertTrue(proof["valid"]["ok"])
        self.assertFalse(proof["finalStatus"]["writesBlocked"])

    def test_null_and_empty_timestamp_inputs_use_current_time(self) -> None:
        proof = node_json(
            r"""
const s=storage();const c=lifecycle.create(s);const originalNow=Date.now;
Date.now=()=>424242;
const first=c.append('local_journal',{event:'null-time'},{at:null});
const second=c.append('local_journal',{event:'empty-time'},{at:''});
const items=c.inspect('local_journal',424242).items;
Date.now=originalNow;
console.log(JSON.stringify({first,second,times:items.map(item=>item.at)}));
"""
        )
        self.assertTrue(proof["first"]["ok"])
        self.assertTrue(proof["second"]["ok"])
        self.assertEqual(proof["times"], [424242, 424242])

    def test_storage_dialog_moves_focus_and_escape_restores_trigger(self) -> None:
        proof = node_json(
            r"""
function interactive(){
  return{
    hidden:false,
    focused:false,
    listeners:{},
    attributes:{},
    setAttribute(k,v){this.attributes[k]=v},
    addEventListener(name,fn){this.listeners[name]=fn},
    focus(){this.focused=true}
  }
}
const trigger=interactive();
const dialog=interactive();
const clearUsage=interactive();
const clearCollective=interactive();
const clearSync=interactive();
const clearPersonal=interactive();
const close=interactive();
dialog.querySelector=function(selector){
  return{
    'button':clearUsage,
    '[data-clear-usage]':clearUsage,
    '[data-clear-collective]':clearCollective,
    '[data-clear-sync]':clearSync,
    '[data-clear-personal]':clearPersonal,
    '[data-close-storage]':close
  }[selector]||null
};
const controls={appendChild(node){this.child=node}};
const body={appendChild(node){this.child=node}};
const doc={
  body,
  getElementById(){return null},
  querySelector(selector){return selector==='.header-controls'?controls:null},
  createElement(tag){return tag==='button'?trigger:dialog}
};
const c=lifecycle.create(storage(),{document:doc,prompt(){return null}});
c.ensureControls();
trigger.listeners.click();
const opened={hidden:dialog.hidden,firstFocused:clearUsage.focused};
let stopped=false;
trigger.focused=false;
dialog.listeners.keydown({key:'Escape',stopPropagation(){stopped=true}});
console.log(JSON.stringify({opened,closed:dialog.hidden,triggerFocused:trigger.focused,stopped}));
"""
        )
        self.assertFalse(proof["opened"]["hidden"])
        self.assertTrue(proof["opened"]["firstFocused"])
        self.assertTrue(proof["closed"])
        self.assertTrue(proof["triggerFocused"])
        self.assertTrue(proof["stopped"])

    def test_builder_and_generated_site_wire_lifecycle_before_profile_runtime(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn(
            'STORAGE_LIFECYCLE_RUNTIME = REPO_ROOT / "docs" / "prompt-kit-storage-lifecycle.js"',
            source,
        )
        self.assertLess(
            source.index("storage_lifecycle_script = _read_runtime"),
            source.index("profile_script = _read_runtime"),
        )
        self.assertLess(
            source.index('f"<script>\\n{storage_lifecycle_script}\\n</script>\\n"'),
            source.index('f"<script>\\n{profile_script}\\n</script>\\n"'),
        )
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn("prompt-kit-storage-lifecycle/v1", deployed)
        self.assertIn("data-clear-usage", deployed)
        self.assertLess(
            deployed.index("prompt-kit-storage-lifecycle/v1"),
            deployed.index("promptKit.profileSlots.v1"),
        )


if __name__ == "__main__":
    unittest.main()
