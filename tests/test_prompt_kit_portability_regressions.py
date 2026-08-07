from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
BASE_RUNTIME = ROOT / "docs" / "prompt-kit.js"
SITE = ROOT / "web" / "prompt-kit" / "index.html"


class PromptKitPortabilityRegressionTests(unittest.TestCase):
    def test_runtime_rejects_malformed_ids_and_merges_legacy_with_current(self) -> None:
        script = r"""
const fs=require('fs');
globalThis.PROMPTS=[{id:'P03'},{id:'P06'},{id:'P07'}];
globalThis.favoritePromptIds={P03:true,NOT_A_PROMPT:true};
globalThis.localStorage={
  data:{'promptKit.favoritePromptIds':'["p06"]','promptKit.favorites':'["P07","P06"]'},
  getItem(k){return this.data[k]||null},
  setItem(k,v){this.data[k]=v},
  removeItem(k){delete this.data[k]}
};
globalThis.saveFavoritePromptIds=function(){globalThis.saved=true};
globalThis.render=function(){globalThis.rendered=true};
const source=fs.readFileSync('docs/prompt-kit-favorites-portability.js','utf8');
eval(source);
const api=globalThis.PromptKitFavoritesPortability;
const payload=api.buildPayload();
if(JSON.stringify(payload.favorite_prompt_ids)!=='["P03","P06","P07"]')throw new Error('legacy merge did not preserve current plus legacy favorites: '+JSON.stringify(payload.favorite_prompt_ids));
if(globalThis.favoritePromptIds.NOT_A_PROMPT)throw new Error('malformed stored favorite survived sanitization');
if(!globalThis.favoritePromptIds.P03||!globalThis.favoritePromptIds.P06||!globalThis.favoritePromptIds.P07)throw new Error('expected current and legacy favorites after migration');
if(globalThis.localStorage.getItem('promptKit.favoritePromptIds')||globalThis.localStorage.getItem('promptKit.favorites'))throw new Error('migrated legacy keys were not retired');
let rejected=false;
try{api.parsePayload(JSON.stringify({schema_version:'prompt-kit-favorites/v1',favorite_prompt_ids:['NOT_A_PROMPT']}))}catch(error){rejected=true}
if(!rejected)throw new Error('malformed imported prompt id was accepted');
const unknown=api.parsePayload(JSON.stringify({schema_version:'prompt-kit-favorites/v1',favorite_prompt_ids:['P999']}));
if(JSON.stringify(unknown.favorite_prompt_ids)!=='["P999"]')throw new Error('well-formed unknown prompt id was not preserved');
console.log('PORTABILITY_REGRESSION_PASS');
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PORTABILITY_REGRESSION_PASS", completed.stdout)

    def test_base_runtime_is_storage_key_owner_and_generated_site_contains_it(self) -> None:
        base_runtime = BASE_RUNTIME.read_text(encoding="utf-8")
        site = SITE.read_text(encoding="utf-8")
        marker = "promptKit.favoritePromptIds.v1"
        self.assertIn(marker, base_runtime)
        self.assertIn(marker, site)
        self.assertNotIn(marker, RUNTIME.read_text(encoding="utf-8").split("function currentFavoritePromptIds", 1)[0])


if __name__ == "__main__":
    unittest.main()
