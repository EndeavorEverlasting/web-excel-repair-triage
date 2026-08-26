#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Doctrine is not a PROMPTS filter; it owns a dedicated renderer. Model it as a first-class
# profile mode instead of pretending it is a normal profile pack.
replace_once(
    "docs/prompt-kit-profiles.js",
    "var MODES=['all','standard','favorites','packs'];",
    "var MODES=['all','standard','favorites','doctrine','packs'];",
)
replace_once(
    "docs/prompt-kit-profiles.js",
    "  FUTURE_PROJECTS:{id:'FUTURE_PROJECTS',label:'Future Projects',rule:anyKeywords(['future project','roadmap','backlog'])},\n  GNHF:{id:'GNHF',label:'GNHF',rule:{op:'category',value:'gnhf'}},\n  DOCTRINE:{id:'DOCTRINE',label:'Doctrine',rule:{op:'category',value:'doctrine'}}\n};",
    "  FUTURE_PROJECTS:{id:'FUTURE_PROJECTS',label:'Future Projects',rule:anyKeywords(['future project','roadmap','backlog'])},\n  GNHF:{id:'GNHF',label:'GNHF',rule:{op:'category',value:'gnhf'}}\n};",
)
replace_once(
    "docs/prompt-kit-profiles.js",
    """    }else if(slot.mode==='favorites'){
      root.activeCat='all';
      root.activeSection='__favorites__'
    }else{
      root.activeCat='all';
      root.activeSection=null
    }
""",
    """    }else if(slot.mode==='favorites'){
      root.activeCat='all';
      root.activeSection='__favorites__'
    }else if(slot.mode==='doctrine'){
      root.activeCat='doctrine';
      root.activeSection=null
    }else{
      root.activeCat='all';
      root.activeSection=null
    }
""",
)
replace_once(
    "docs/prompt-kit-profiles.js",
    "Rename any tab. All, Standard, and Favorites preserve their built-in views; Custom composes one or more safe profile packs.",
    "Rename any tab. All, Standard, Favorites, and Doctrine are built-in views; Custom composes one or more safe profile packs.",
)
replace_once(
    "docs/prompt-kit-profiles.js",
    "[['all','All prompts'],['standard','Standard prompts'],['favorites','Favorites'],['packs','Custom profile packs']]",
    "[['all','All prompts'],['standard','Standard prompts'],['favorites','Favorites'],['doctrine','Doctrine'],['packs','Custom profile packs']]",
)

# Escape must keep visible navigation in sync with the state it clears.
replace_once(
    "docs/prompt-kit.js",
    "if(activeSection){activeSection=null;render();return}if(activeCat!=='all'){activeCat='all';render();return}",
    "if(activeSection){activeSection=null;renderSections();renderTypes();render();return}if(activeCat!=='all'){activeCat='all';syncLibraryTabs();renderTypes();render();return}",
)

# Human contracts: A-E are the only header keys; Home/End own page edges; Doctrine is assignable
# as a dedicated profile mode, while GNHF remains a normal profile pack.
replace_once(
    "PROMPT_KIT_ACCESS.md",
    """- Press **4** or use the header **Favorites** shortcut to clear transient search/type/category restrictions and show the complete saved Favorites list. Favorites remain persistent; they are not promoted ahead of normal chronological library order unless this explicit Favorites view is selected.
- **Doctrine** remains available in the header and moves to keyboard shortcut **5**.
""",
    """- Press **A** for All, **B** for Standard, or **C** for Favorites. Slots **D** and **E** are persisted user profiles (default SAS and PM) and may be renamed or reassigned in the Hotkeys panel.
- **Doctrine** remains a first-class built-in profile mode without consuming a sixth header slot: assign any A–E slot to **Doctrine** in the Hotkeys panel, then activate that slot by click/tap or its A–E key. The dedicated Doctrine view is restored after reload because slot configuration and the active slot are persisted.
- **GNHF** remains available as a predefined profile pack for custom profile composition.
- Press **Home** for the true document top and **End** for the document bottom; neither key changes the active A–E profile.
""",
)
replace_once(
    "web/README.md",
    "The top rail exposes five persistent keyboard slots, `A` through `E`. Every slot can be renamed and assigned a built-in view or a custom union of profile packs from the Hotkeys panel. Defaults are **All / Standard / Favorites / SAS / PM**; SAS selects the SAS pack, while PM composes PM + FUN + TRIAGE + H&H. Built-in packs also include CYBERSEC, AGENTIC LOOPING, Gardening, and Future Projects.",
    "The top rail exposes five persistent keyboard slots, `A` through `E`. Every slot can be renamed and assigned the built-in All, Standard, Favorites, or Doctrine view, or a custom union of profile packs from the Hotkeys panel. Defaults are **All / Standard / Favorites / SAS / PM**; SAS selects the SAS pack, while PM composes PM + FUN + TRIAGE + H&H. Built-in packs also include CYBERSEC, AGENTIC LOOPING, GNHF, Gardening, and Future Projects. Doctrine is a dedicated view mode rather than a prompt-filter pack, so assigning it to a slot opens the canonical Doctrine renderer instead of filtering the normal prompt list.",
)
replace_once(
    "docs/PROMPT_KIT_FIVE_TAB_PROFILES.md",
    "The slot key is stable; the visible name and selected mode/packs are user configuration. A user may\nrename every slot. A custom slot is the union of its selected profile packs.\n",
    "The slot key is stable; the visible name and selected mode/packs are user configuration. A user may\nrename every slot. Built-in modes are All, Standard, Favorites, and Doctrine; a custom slot is the union\nof its selected profile packs. Doctrine is a dedicated rendered surface, not a normal PROMPTS filter.\n",
)
replace_once(
    "docs/PROMPT_KIT_FIVE_TAB_PROFILES.md",
    "The runtime ships declarative packs for `TRIAGE`, `FUN`, `PM`, `CYBERSEC`, `AGENTIC_LOOPING`, `SAS`,\n`GARDENING`, `H_AND_H`, and `FUTURE_PROJECTS`. Packs match prompt metadata and text fields. They are\nbuilding blocks rather than cloned prompt collections.\n",
    "The runtime ships declarative packs for `TRIAGE`, `FUN`, `PM`, `CYBERSEC`, `AGENTIC_LOOPING`, `SAS`,\n`GARDENING`, `H_AND_H`, `FUTURE_PROJECTS`, and `GNHF`. Packs match prompt metadata and text fields. They\nare building blocks rather than cloned prompt collections. Doctrine stays outside this list because it\nis a dedicated profile mode backed by the canonical Doctrine renderer.\n",
)

# Static/runtime regressions for Doctrine mode, active-mode reapplication, and Escape UI synchronization.
profile_tests = ROOT / "tests" / "test_prompt_kit_profiles.py"
text = profile_tests.read_text(encoding="utf-8")
old = '''    def test_retired_header_views_remain_profile_packs(self) -> None:\n        proof = node_json(\n            """\nconst api=require('./docs/prompt-kit-profiles.js');\nconsole.log(JSON.stringify({ids:Object.keys(api.PREDEFINED_PACKS).sort()}));\n"""\n        )\n        self.assertIn("GNHF", proof["ids"])\n        self.assertIn("DOCTRINE", proof["ids"])\n        access = ACCESS.read_text(encoding="utf-8")\n        self.assertIn("`GNHF` and `DOCTRINE` profile packs", access)\n        self.assertIn("Press **Home** for the true document top", access)\n        self.assertNotIn("Press **4** or use the header **Favorites**", access)\n        self.assertNotIn("Doctrine** remains available in the header", access)\n\n'''
new = '''    def test_retired_header_views_keep_correct_profile_owned_routes(self) -> None:\n        proof = node_json(\n            """\nconst api=require('./docs/prompt-kit-profiles.js');\nconsole.log(JSON.stringify({ids:Object.keys(api.PREDEFINED_PACKS).sort(),modes:api.MODES}));\n"""\n        )\n        self.assertIn("GNHF", proof["ids"])\n        self.assertNotIn("DOCTRINE", proof["ids"])\n        self.assertIn("doctrine", proof["modes"])\n        access = ACCESS.read_text(encoding="utf-8")\n        self.assertIn("**Doctrine** remains a first-class built-in profile mode", access)\n        self.assertIn("**GNHF** remains available as a predefined profile pack", access)\n        self.assertIn("Press **Home** for the true document top", access)\n        self.assertNotIn("Press **4** or use the header **Favorites**", access)\n        self.assertNotIn("Doctrine** remains available in the header", access)\n\n    def test_doctrine_mode_uses_dedicated_renderer_and_persists_active_slot(self) -> None:\n        proof = node_json(\n            r"""\nconst api=require('./docs/prompt-kit-profiles.js');\nconst memory={};\nconst doc={\n  getElementById(id){return id==='prompt-kit-profile-styles'?{}:null},\n  querySelector(){return null},\n  addEventListener(){},\n  head:{appendChild(){}},\n  body:{}\n};\nconst root={\n  document:doc,\n  localStorage:{getItem(k){return memory[k]||null},setItem(k,v){memory[k]=String(v)}},\n  PROMPTS:[{id:'P1',category:'standard'}],activeCat:'all',activeSection:null,\n  render(){root.renderedCat=root.activeCat},renderTypes(){},renderSections(){},setTimeout(){},showToast(){}\n};\nconst installed=api.install(root);\nconst candidate=installed.getState().slots;\ncandidate[3]={key:'D',name:'Doctrine',mode:'doctrine',packIds:[]};\ninstalled.configureSlots(candidate);\ninstalled.activateSlot('D',true);\nconsole.log(JSON.stringify({\n  active:installed.getState().activeKey,\n  mode:installed.getState().slots[3].mode,\n  cat:root.activeCat,\n  renderedCat:root.renderedCat,\n  persistedActive:memory[api.STORAGE_KEYS.active],\n  persistedSlots:JSON.parse(memory[api.STORAGE_KEYS.slots]).slots[3]\n}));\n"""\n        )\n        self.assertEqual(proof["active"], "D")\n        self.assertEqual(proof["mode"], "doctrine")\n        self.assertEqual(proof["cat"], "doctrine")\n        self.assertEqual(proof["renderedCat"], "doctrine")\n        self.assertEqual(proof["persistedActive"], "D")\n        self.assertEqual(proof["persistedSlots"]["mode"], "doctrine")\n\n'''
if text.count(old) != 1:
    raise SystemExit("tests/test_prompt_kit_profiles.py: retired-view test anchor drifted")
text = text.replace(old, new, 1)
text = text.replace(
    '            "Digits remain available to configured prompt-ID sequences such as `P111`",\n',
    '            "Digits remain available to configured prompt-ID sequences such as `P111`",\n            "Built-in modes are All, Standard, Favorites, and Doctrine",\n',
    1,
)
profile_tests.write_text(text, encoding="utf-8")

filter_tests = ROOT / "tests" / "test_prompt_kit_filtering_access.py"
text = filter_tests.read_text(encoding="utf-8")
marker = "    def test_render_uses_unique_category_metadata_without_reordering_cards(self) -> None:\n"
addition = '''    def test_escape_resynchronizes_visible_navigation_after_filter_clear(self) -> None:\n        js = JS.read_text(encoding="utf-8")\n        self.assertIn(\n            "if(activeSection){activeSection=null;renderSections();renderTypes();render();return}",\n            js,\n        )\n        self.assertIn(\n            "if(activeCat!=='all'){activeCat='all';syncLibraryTabs();renderTypes();render();return}",\n            js,\n        )\n\n'''
if text.count(marker) != 1:
    raise SystemExit("tests/test_prompt_kit_filtering_access.py: insertion marker drifted")
if "test_escape_resynchronizes_visible_navigation_after_filter_clear" not in text:
    text = text.replace(marker, addition + marker, 1)
filter_tests.write_text(text, encoding="utf-8")

# Browser-observed closure: configure Doctrine through the actual Hotkeys UI, activate D, then reload
# and prove both slot configuration and dedicated Doctrine rendering survive.
browser = ROOT / "tests" / "prompt_kit_hotkey_identity_browser_proof.py"
text = browser.read_text(encoding="utf-8")
marker = '''            # Numeric input must never activate A-E header slots.\n            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")\n            observations.append({\n                "id": "numeric_sequences_do_not_drive_header",\n                "event": "digit-bearing prompt sequences leave header navigation in the expected All profile",\n                "occurred": True,\n                "passed": active_slot == "A",\n                "active_slot": active_slot,\n            })\n\n            screenshot.parent.mkdir(parents=True, exist_ok=True)\n'''
replacement = '''            # Numeric input must never activate A-E header slots.\n            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")\n            observations.append({\n                "id": "numeric_sequences_do_not_drive_header",\n                "event": "digit-bearing prompt sequences leave header navigation in the expected All profile",\n                "occurred": True,\n                "passed": active_slot == "A",\n                "active_slot": active_slot,\n            })\n\n            # Falsify the removed-header regression through the real user configuration UI: Doctrine\n            # must remain reachable without stealing an A-E slot or masquerading as a PROMPTS pack.\n            page.locator('#hotkeyHelpToggle').click()\n            page.wait_for_timeout(75)\n            doctrine_row = page.locator('.prompt-profile-slot-row[data-key="D"]')\n            doctrine_row.locator('[data-slot-name]').fill('Doctrine')\n            doctrine_row.locator('[data-slot-mode]').select_option('doctrine')\n            page.locator('[data-profile-save]').click()\n            page.wait_for_timeout(100)\n            saved_doctrine = 'Saved five profile tabs.' in page.locator('.prompt-profile-status').inner_text()\n            page.locator('.hotkey-help-close').click()\n            page.evaluate("document.activeElement && document.activeElement.blur()")\n            page.keyboard.press('d')\n            page.wait_for_timeout(120)\n            doctrine_active = page.evaluate("""() => {\n              const state=window.PromptKitProfiles&&window.PromptKitProfiles.getState();\n              const view=document.getElementById('doctrineView');\n              const cards=document.querySelectorAll('#doctrineList .doctrine-card');\n              return {\n                slot:state&&state.activeKey,\n                mode:state&&state.slots&&state.slots[3]&&state.slots[3].mode,\n                activeCat:window.activeCat,\n                viewActive:!!(view&&view.classList.contains('active')),\n                doctrineCards:cards.length\n              };\n            }""")\n            observations.append({\n                "id": "doctrine_profile_mode_reaches_dedicated_view",\n                "event": "D is configured to Doctrine through the Hotkeys UI and opens the dedicated Doctrine renderer",\n                "occurred": True,\n                "passed": bool(saved_doctrine and doctrine_active.get('slot') == 'D' and doctrine_active.get('mode') == 'doctrine' and doctrine_active.get('activeCat') == 'doctrine' and doctrine_active.get('viewActive') and doctrine_active.get('doctrineCards', 0) > 0),\n                "saved": bool(saved_doctrine),\n                **doctrine_active,\n            })\n\n            page.reload(wait_until='domcontentloaded')\n            page.wait_for_timeout(150)\n            doctrine_reload = page.evaluate("""() => {\n              const state=window.PromptKitProfiles&&window.PromptKitProfiles.getState();\n              const view=document.getElementById('doctrineView');\n              return {\n                slot:state&&state.activeKey,\n                mode:state&&state.slots&&state.slots[3]&&state.slots[3].mode,\n                activeCat:window.activeCat,\n                viewActive:!!(view&&view.classList.contains('active'))\n              };\n            }""")\n            observations.append({\n                "id": "doctrine_profile_mode_survives_reload",\n                "event": "The configured Doctrine slot and active D state survive a same-origin reload",\n                "occurred": True,\n                "passed": bool(doctrine_reload.get('slot') == 'D' and doctrine_reload.get('mode') == 'doctrine' and doctrine_reload.get('activeCat') == 'doctrine' and doctrine_reload.get('viewActive')),\n                **doctrine_reload,\n            })\n\n            screenshot.parent.mkdir(parents=True, exist_ok=True)\n'''
if text.count(marker) != 1:
    raise SystemExit("tests/prompt_kit_hotkey_identity_browser_proof.py: doctrine insertion marker drifted")
browser.write_text(text.replace(marker, replacement, 1), encoding="utf-8")
