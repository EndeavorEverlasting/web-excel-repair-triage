from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'scripts/write_prompt_kit_promotion_receipt.py'
WORKFLOW=ROOT/'.github/workflows/prompt-kit-pages.yml'
HOOK_WORKFLOW=ROOT/'.github/workflows/prompt-kit-feedback-hook.yml'

class PromptKitPromotionPipelineTests(unittest.TestCase):
    def run_receipt(self,*args:str):
        return subprocess.run(['python',str(RECEIPT),*args],cwd=ROOT,text=True,capture_output=True)
    def test_receipt_rejects_unauthorized_target(self):
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        r=self.run_receipt('--candidate',head,'--target','production-other')
        self.assertNotEqual(r.returncode,0); self.assertIn('target not allowed',r.stderr+r.stdout)
    def test_receipt_rejects_stale_candidate(self):
        r=self.run_receipt('--candidate','0'*40,'--target','github-pages')
        self.assertNotEqual(r.returncode,0); self.assertIn('stale candidate',r.stderr+r.stdout)
    def test_receipt_accepts_exact_checkout_head(self):
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/'receipt.json'; r=self.run_receipt('--candidate',head,'--target','github-pages','--output',str(output))
            self.assertEqual(r.returncode,0,r.stderr+r.stdout); self.assertTrue(output.exists())
    def test_pull_request_and_manual_dispatch_cannot_deploy(self):
        text=WORKFLOW.read_text(encoding='utf-8')
        guard="if: github.event_name == 'push' && github.ref == 'refs/heads/main'"
        self.assertGreaterEqual(text.count(guard),3)
        self.assertIn('needs: [validate, package]',text)
        self.assertNotIn('contents: write',text)
        self.assertNotIn('continue-on-error',text)
    def test_hook_is_read_only_and_cannot_mutate_prompts(self):
        text=HOOK_WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('contents: read',text); self.assertNotIn('contents: write',text)
        self.assertNotIn('git push',text); self.assertNotIn('prompt_registry_ops.py',text)

if __name__=='__main__': unittest.main()
