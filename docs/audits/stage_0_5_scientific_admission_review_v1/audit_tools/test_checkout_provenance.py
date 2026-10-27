"""Pure in-memory tests for two explicitly scoped review document representations."""
import ast
import hashlib
from pathlib import Path
import unittest

SCRIPT=Path(__file__).with_name('validate_review.py')
NS=dict(CHECKOUT_DOCS={'AGENTS.md','PROJECT_CONTEXT.md'},digest=lambda b:hashlib.sha256(b).hexdigest())
TREE=ast.parse(SCRIPT.read_text(encoding='utf-8'))
FUNC=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='verify_document_checkout')
exec(compile(ast.Module(body=[FUNC],type_ignores=[]),str(SCRIPT),'exec'),NS)

class CheckoutProvenance(unittest.TestCase):
    def setUp(self):
        self.blob=b'Header\nBody\n';self.reviewed=self.blob.replace(b'\n',b'\r\n')
        self.entry=dict(path='AGENTS.md',sha256=NS['digest'](self.reviewed),checkout_provenance=dict(
            schema='aad.reviewed-document-checkout.v1',git_blob_oid='synthetic_oid',
            git_blob_sha256=NS['digest'](self.blob),reviewed_bytes_sha256=NS['digest'](self.reviewed),
            relation='reviewed_CRLF_equals_baseline_LF_with_CRLF_only'))
    def check(self,actual,name='AGENTS.md',blob=None,oid='synthetic_oid'):
        return NS['verify_document_checkout'](name,self.entry,actual,self.blob if blob is None else blob,oid)
    def test_two_exact_representations(self):
        self.assertEqual(self.check(self.blob),'baseline_Git_LF_checkout')
        self.assertEqual(self.check(self.reviewed),'reviewed_CRLF_bytes')
    def test_content_change_refused(self):
        with self.assertRaises(AssertionError): self.check(b'Header\nOther\n')
    def test_mixed_or_lone_cr_refused(self):
        for value in [b'Header\r\nBody\n',b'Header\rBody\n']:
            with self.assertRaises(AssertionError): self.check(value)
    def test_scientific_path_refused(self):
        self.entry['path']='code/scripts/stage_0_5_native_capsule_v4.py'
        with self.assertRaises(AssertionError): self.check(self.blob,name=self.entry['path'])
    def test_wrong_blob_or_oid_refused(self):
        with self.assertRaises(AssertionError): self.check(self.blob,blob=b'Changed\n')
        with self.assertRaises(AssertionError): self.check(self.blob,oid='wrong')
    def test_reviewed_sha_not_weakened(self):
        self.entry['sha256']=NS['digest'](self.blob)
        with self.assertRaises(AssertionError): self.check(self.blob)

if __name__=='__main__': unittest.main(verbosity=2)
