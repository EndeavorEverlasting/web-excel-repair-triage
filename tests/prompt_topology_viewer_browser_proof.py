#!/usr/bin/env python3
from __future__ import annotations
import json, os, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Outputs/observed-proof/prompt-topology-phase-c.json';SHOT=ROOT/'Outputs/observed-proof/prompt-topology-phase-c.png'
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main():
    os.chdir(ROOT);server=ThreadingHTTPServer(('127.0.0.1',0),Quiet);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();port=server.server_address[1];checks=[]
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);ctx=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');page=ctx.new_page()
        requests=[];page.on('request',lambda r: requests.append(r.url) if r.resource_type not in {'document'} else None)
        page.goto(f'http://127.0.0.1:{port}/Outputs/prompt-topology-viewer/index.html',wait_until='domcontentloaded');page.wait_for_function('window.PromptTopologyViewer && PromptTopologyViewer.snapshot().nodeCount > 0')
        snap=page.evaluate('PromptTopologyViewer.snapshot()');checks.append({'id':'binding_and_parity','passed':snap['nodeCount']==snap['projectionPointCount'] and len(snap['topologyHash'])==64 and len(snap['projectionHash'])==64,'snapshot':snap})
        page.locator('#search').fill('P105');page.wait_for_timeout(80);searched=page.evaluate('PromptTopologyViewer.snapshot()');checks.append({'id':'search_selects_prompt','passed':searched['selectedId']=='P105','selected':searched['selectedId']});semantic_floor={k:searched[k] for k in ('nodeCount','edgeCount','projectionPointCount','topologyHash','projectionHash','epochId')}
        before=page.evaluate('PromptTopologyViewer.snapshot()');box=page.locator('#universe').bounding_box();assert box
        page.mouse.move(box['x']+box['width']*.4,box['y']+box['height']*.4);page.mouse.down();page.mouse.move(box['x']+box['width']*.55,box['y']+box['height']*.5,steps=4);page.mouse.up();after=page.evaluate('PromptTopologyViewer.snapshot()');checks.append({'id':'drag_rotates','passed':abs(after['yaw']-before['yaw'])>.01 or abs(after['pitch']-before['pitch'])>.01});checks.append({'id':'view_does_not_mutate_semantic_floor','passed':all(after[k]==v for k,v in semantic_floor.items())})
        zoom0=after['zoom'];page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.wheel(0,-240);page.wait_for_timeout(50);zoom1=page.evaluate('PromptTopologyViewer.snapshot().zoom');checks.append({'id':'wheel_zooms','passed':zoom1>zoom0,'before':zoom0,'after':zoom1});pan0=page.evaluate('PromptTopologyViewer.snapshot()');page.keyboard.down('Shift');page.mouse.move(box['x']+box['width']*.45,box['y']+box['height']*.45);page.mouse.down();page.mouse.move(box['x']+box['width']*.52,box['y']+box['height']*.52,steps=3);page.mouse.up();page.keyboard.up('Shift');pan1=page.evaluate('PromptTopologyViewer.snapshot()');checks.append({'id':'shift_drag_pans','passed':abs(pan1['panX']-pan0['panX'])>2 or abs(pan1['panY']-pan0['panY'])>2})
        cluster=page.locator('.cluster-btn').first;cid=cluster.get_attribute('data-cluster');cluster.click();page.wait_for_timeout(50);active=page.evaluate('PromptTopologyViewer.snapshot().activeCluster');checks.append({'id':'cluster_focus','passed':active==cid,'cluster':cid});fallback_count=page.locator('.text-fallback li').count();checks.append({'id':'static_text_fallback_complete','passed':fallback_count==snap['nodeCount'],'fallback_count':fallback_count});page.reload(wait_until='domcontentloaded');page.wait_for_function('window.PromptTopologyViewer');page.locator('#search').fill('P105');page.wait_for_timeout(50);reloaded=page.evaluate('PromptTopologyViewer.snapshot()');checks.append({'id':'prompt_identity_stable_across_reload','passed':reloaded['selectedId']=='P105' and all(reloaded[k]==v for k,v in semantic_floor.items())})
        checks.append({'id':'no_runtime_data_requests','passed':len(requests)==0,'requests':requests})
        SHOT.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(SHOT),full_page=False);ctx.close();browser.close()
    finally: server.shutdown();server.server_close()
    receipt={'schema_version':'prompt-topology-phase-c-browser-proof/v1','status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,'screenshot':str(SHOT.relative_to(ROOT))}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2,sort_keys=True));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
