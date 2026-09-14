from pathlib import Path

root = Path('.')

# The compact-browsing hotkey owner runs in capture phase, so detail-local
# Home/End must be routed there before the page-level edge handlers.
polish_path = root / 'docs/prompt-kit-polish.js'
polish = polish_path.read_text(encoding='utf-8')
old = """    if(editable)return;
    if(key==='`'){"""
new = """    if(editable)return;
    var detailOverlay=document.getElementById('promptDetailOverlay');
    var detailOwnsEdges=!!(detailOverlay&&detailOverlay.classList.contains('open'));
    if(detailOwnsEdges&&(key==='home'||key==='end')&&typeof scrollPromptDetailTo==='function'){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();scrollPromptDetailTo(key==='home'?'top':'bottom');return
    }
    if(key==='`'){"""
if old not in polish:
    raise SystemExit('compact hotkey editable seam not found')
polish = polish.replace(old, new, 1)
polish_path.write_text(polish, encoding='utf-8')

# Cross-input regression must bind the capture-phase implementation, not just prose.
cross_path = root / 'tests/test_prompt_kit_cross_input_modality.py'
cross = cross_path.read_text(encoding='utf-8')
old = """        self.assertIn("prompt detail container", by_id["scroll_edges"]["keyboard"])
        self.assertEqual(by_id["scroll_edges"]["semantic_action"], "scrollPromptKitTo / scrollPromptDetailTo")
"""
new = """        self.assertIn("prompt detail container", by_id["scroll_edges"]["keyboard"])
        self.assertEqual(by_id["scroll_edges"]["semantic_action"], "scrollPromptKitTo / scrollPromptDetailTo")
        polish = POLISH.read_text(encoding="utf-8")
        self.assertIn("var detailOwnsEdges=!!(detailOverlay&&detailOverlay.classList.contains('open'))", polish)
        self.assertIn("detailOwnsEdges&&(key==='home'||key==='end')", polish)
        self.assertIn("scrollPromptDetailTo(key==='home'?'top':'bottom')", polish)
        self.assertLess(polish.index("if(editable)return"), polish.index("detailOwnsEdges&&(key==='home'||key==='end')"))
"""
if old not in cross:
    raise SystemExit('cross-input detail assertion seam not found')
cross = cross.replace(old, new, 1)
cross_path.write_text(cross, encoding='utf-8')

# The old navigation regression pinned the no-event-argument Copy handler. Preserve
# its real invariant: dynamic prompt IDs stay out of inline HTML and explicit Copy
# uses p.id while stopping propagation from the broad detail click surface.
order_path = root / 'tests/test_prompt_kit_order_navigation_product.py'
order = order_path.read_text(encoding='utf-8')
old = '        self.assertIn("detailCopy.onclick=function(){copyPrompt(p.id)", source)\n'
new = '        self.assertIn("detailCopy.onclick=function(e){e.stopPropagation();copyPrompt(p.id)", source)\n'
if old not in order:
    raise SystemExit('order-navigation copy-handler assertion seam not found')
order = order.replace(old, new, 1)
order_path.write_text(order, encoding='utf-8')

# The browser proof originally compared modal scrollTop around a textarea appended
# at the bottom; native caret visibility can legitimately scroll an ancestor. The
# contract is that neither Prompt Kit edge handler runs for editable Home/End.
proof_path = root / 'tests/prompt_kit_detail_browser_proof.py'
proof = proof_path.read_text(encoding='utf-8')
old = """            editable_before = page.evaluate(\"\"\"() => {
              const detail=document.getElementById('promptDetail');
              const probe=document.createElement('textarea');
              probe.id='detailEditableProbe';
              probe.value='alpha beta gamma';
              probe.setAttribute('data-prompt-detail-no-copy','');
              detail.appendChild(probe);
              probe.focus({preventScroll:true});
              detail.scrollTop=Math.min(120,Math.max(0,detail.scrollHeight-detail.clientHeight));
              return detail.scrollTop;
            }\"\"\")
            page.keyboard.press('Home')
            page.keyboard.press('End')
            page.wait_for_timeout(30)
            editable_after = page.evaluate(\"document.getElementById('promptDetail').scrollTop\")
            editable_native = abs(editable_after - editable_before) <= 1
            page.evaluate(\"document.getElementById('detailEditableProbe').remove()\")
"""
new = """            page.evaluate(\"\"\"() => {
              const detail=document.getElementById('promptDetail');
              const probe=document.createElement('textarea');
              probe.id='detailEditableProbe';
              probe.value='alpha beta gamma';
              probe.setAttribute('data-prompt-detail-no-copy','');
              detail.insertBefore(probe,detail.firstChild);
              window.__detailEdgeCalls=0;
              window.__pageEdgeCalls=0;
              window.__detailEdgeOriginal=window.scrollPromptDetailTo;
              window.__pageEdgeOriginal=window.scrollPromptKitTo;
              window.scrollPromptDetailTo=function(edge){window.__detailEdgeCalls++;return window.__detailEdgeOriginal(edge)};
              window.scrollPromptKitTo=function(edge){window.__pageEdgeCalls++;return window.__pageEdgeOriginal(edge)};
              probe.focus({preventScroll:true});
            }\"\"\")
            page.keyboard.press('Home')
            page.keyboard.press('End')
            page.wait_for_timeout(30)
            editable_calls = page.evaluate(\"({detail:window.__detailEdgeCalls,page:window.__pageEdgeCalls})\")
            editable_native = editable_calls['detail'] == 0 and editable_calls['page'] == 0
            page.evaluate(\"\"\"() => {
              window.scrollPromptDetailTo=window.__detailEdgeOriginal;
              window.scrollPromptKitTo=window.__pageEdgeOriginal;
              document.getElementById('detailEditableProbe').remove();
            }\"\"\")
"""
if old not in proof:
    raise SystemExit('editable browser-proof seam not found')
proof = proof.replace(old, new, 1)
old = '                {"id":"detail_editable_home_end_native","event":"Home/End inside a textarea leave prompt-detail scroll position unchanged","occurred":True,"passed":bool(editable_native)},\n'
new = '                {"id":"detail_editable_home_end_native","event":"Home/End inside a textarea invoke neither Prompt Kit detail-edge nor page-edge handler","occurred":True,"passed":bool(editable_native),"detail_edge_calls":editable_calls["detail"],"page_edge_calls":editable_calls["page"]},\n'
if old not in proof:
    raise SystemExit('editable observation seam not found')
proof = proof.replace(old, new, 1)
proof_path.write_text(proof, encoding='utf-8')
