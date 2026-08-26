#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# If a shorter exact prompt identity is pending because it prefixes a longer one,
# an unrelated key must settle that exact prompt without swallowing the unrelated
# header/global command carried by the same key event.
replace_once(
    "docs/prompt-kit-polish.js",
    """function handleConfiguredPromptShortcutKey(e,key){
  var gestures=Object.keys(promptShortcutBindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}
  if(!/^[a-z0-9]$/.test(key)){resetPromptShortcutBuffer();return false}
  function acceptCandidate(candidate){
    var exact=promptShortcutBindings[candidate];
    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}
    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
    return false
  }
  var candidate=promptShortcutBuffer+key;
  if(acceptCandidate(candidate))return true;
  resetPromptShortcutBuffer();
  return acceptCandidate(key)
}""",
    """function handleConfiguredPromptShortcutKey(e,key){
  var gestures=Object.keys(promptShortcutBindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}
  var pendingExact=promptShortcutBindings[promptShortcutBuffer]||null;
  if(!/^[a-z0-9]$/.test(key)){
    resetPromptShortcutBuffer();
    if(pendingExact)activatePromptShortcutTarget(pendingExact);
    return false
  }
  function acceptCandidate(candidate){
    var exact=promptShortcutBindings[candidate];
    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}
    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
    return false
  }
  var candidate=promptShortcutBuffer+key;
  if(acceptCandidate(candidate))return true;
  resetPromptShortcutBuffer();
  if(pendingExact){activatePromptShortcutTarget(pendingExact);return false}
  return acceptCandidate(key)
}""",
)

runtime = ROOT / "tests" / "test_prompt_kit_hotkey_identity_runtime.py"
text = runtime.read_text(encoding="utf-8")
old = """  resetProbe();
  ['p','1','.','1','1'].forEach(press);
  assert(JSON.stringify(activations)==='[\"P111\"]','p1.11 dotted longer resolution');

  console.log(JSON.stringify({status:'PASS',cases:['p11','p13','p111','p1.1','p1.11']}));
"""
new = """  resetProbe();
  ['p','1','.','1','1'].forEach(press);
  assert(JSON.stringify(activations)==='[\"P111\"]','p1.11 dotted longer resolution');

  resetProbe();
  var headerActivations=[];
  function dispatch(key){
    var event=eventStub();
    if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(event,key))return;
    if('abcde'.indexOf(key)!==-1){headerActivations.push(key.toUpperCase());return}
    handleConfiguredPromptShortcutKey(event,key)
  }
  ['p','1','1'].forEach(dispatch);
  dispatch('a');
  assert(JSON.stringify(activations)==='[\"P11\"]','pending p11 was lost on header A handoff');
  assert(JSON.stringify(headerActivations)==='[\"A\"]','header A was swallowed after pending p11');

  resetProbe();headerActivations=[];
  ['p','1'].forEach(dispatch);
  dispatch('b');
  assert(activations.length===0,'incomplete p1 incorrectly activated a prompt on header B');
  assert(JSON.stringify(headerActivations)==='[\"B\"]','header B was swallowed after incomplete prefix');

  console.log(JSON.stringify({status:'PASS',cases:['p11','p13','p111','p1.1','p1.11','p11-then-a','p1-then-b']}));
"""
if text.count(old) != 1:
    raise SystemExit("runtime identity marker drifted")
text = text.replace(old, new, 1)
old_assert = 'self.assertEqual(proof["cases"], ["p11", "p13", "p111", "p1.1", "p1.11"])'
new_assert = 'self.assertEqual(proof["cases"], ["p11", "p13", "p111", "p1.1", "p1.11", "p11-then-a", "p1-then-b"])'
if text.count(old_assert) != 1:
    raise SystemExit("runtime identity result assertion drifted")
runtime.write_text(text.replace(old_assert, new_assert, 1), encoding="utf-8")

browser = ROOT / "tests" / "prompt_kit_hotkey_identity_browser_proof.py"
text = browser.read_text(encoding="utf-8")
marker = """            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
"""
insert = """            # A pending shorter exact identity settles before the same key continues to the A-E header.
            set_clipboard("sentinel-p11-a")
            press("p11")
            page.keyboard.press("a")
            page.wait_for_timeout(180)
            p11_then_a = clipboard()
            slot_after_a = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "pending_p11_hands_off_to_header_a",
                "event": "A settles pending P11 and still activates the All profile",
                "occurred": True,
                "passed": p11_then_a == expected["P11"] and slot_after_a == "A",
                "prompt_matches": p11_then_a == expected["P11"],
                "active_slot": slot_after_a,
            })

            # An incomplete prefix has no exact prompt to settle and must not swallow B.
            set_clipboard("sentinel-p1-b")
            press("p1")
            page.keyboard.press("b")
            page.wait_for_timeout(180)
            p1_then_b = clipboard()
            slot_after_b = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
            observations.append({
                "id": "incomplete_prefix_hands_off_to_header_b",
                "event": "B abandons incomplete p1 without firing a prompt and activates Standard",
                "occurred": True,
                "passed": p1_then_b == "sentinel-p1-b" and slot_after_b == "B",
                "clipboard_unchanged": p1_then_b == "sentinel-p1-b",
                "active_slot": slot_after_b,
            })
            page.keyboard.press("a")
            page.wait_for_timeout(50)

            # Numeric input must never activate A-E header slots.
            active_slot = page.evaluate("window.PromptKitProfiles && window.PromptKitProfiles.getState().activeKey")
"""
if text.count(marker) != 1:
    raise SystemExit("browser identity handoff marker drifted")
browser.write_text(text.replace(marker, insert, 1), encoding="utf-8")
