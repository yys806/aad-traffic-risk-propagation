"""Pure audit counterexamples in a temporary empty working directory.

Only AST-extracted definitions and synthetic in-memory objects are evaluated.
No real proposal/approval/envelope is created; no execution entry is imported.
"""
import ast
from collections import Counter
from copy import copy, deepcopy
import hashlib
import math
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]


def extract(name, names, namespace):
    tree = ast.parse((ROOT / 'code/scripts' / name).read_text(encoding='utf-8'))
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), name, 'exec'), namespace)
    return namespace


class GuardReview(unittest.TestCase):
    def setUp(self):
        self.previous = os.getcwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        self.ns = extract('stage_0_5_native_capsule_v4.py', ['authorization_reasons'],
            dict(SCHEMA='aad.native-admission.v4', SMOKE_SCHEMA='aad.native-smoke.v4',
                 TASK='AAD-0.5-READY-TO-ADMIT-V3', SMOKE_TASK='AAD-0.5-LINUX-INTEGRATION-V4-SMOKE'))
        self.p = dict(schema=self.ns['SCHEMA'], task_id=self.ns['TASK'], isolation=dict(accepted_for_new_task=True))
        # Counterfactual synthetic data only, not a researcher decision or envelope.
        self.a = dict(task_id=self.ns['TASK'], run_id='SYNTHETIC_AUDIT_ONLY', proposal_sha256='synthetic-token',
            decision_record='Counterexample; never authorization', execution_allowed=True,
            researcher_confirmed=True, protocol_frozen=True,
            admission=dict(initialization_policy_approved=True, measurement_contract_approved=True, input_fidelity_approved=True))

    def tearDown(self):
        self.assertEqual(os.listdir('.'), [])
        os.chdir(self.previous)
        self.temp.cleanup()

    def reasons(self, approval):
        return self.ns['authorization_reasons'](self.p, approval, 'synthetic-token', 'SYNTHETIC_AUDIT_ONLY')

    def test_engineering_true_alone_refuses(self):
        result = self.reasons({})
        self.assertIn('researcher_confirmed_not_confirmed_for_exact_proposal', result)
        self.assertIn('protocol_frozen_not_confirmed_for_exact_proposal', result)

    def test_each_approval_required(self):
        self.assertEqual(self.reasons(self.a), [])
        for name in ['execution_allowed', 'researcher_confirmed', 'protocol_frozen']:
            self.assertIn(name + '_not_confirmed_for_exact_proposal', self.reasons(dict(self.a, **{name: False})))
        for name in self.a['admission']:
            a = dict(self.a, admission=dict(self.a['admission'], **{name: False}))
            self.assertIn(name + '_not_confirmed', self.reasons(a))

    def test_wrong_exact_object_refuses(self):
        for key in ['task_id', 'run_id', 'proposal_sha256']:
            self.assertIn('authorization_' + key + '_mismatch', self.reasons(dict(self.a, **{key:'wrong'})))

    def test_policy_false_refuses_after_engineering_acceptance(self):
        self.assertEqual(self.reasons(self.a), [])
        self.p['isolation']['accepted_for_new_task'] = False
        self.assertEqual(self.reasons(self.a), ['capsule_build_not_accepted'])

    def test_no_identity_from_absence(self):
        module = ast.parse((ROOT / 'code/scripts/stage_0_5_identity_observation.py').read_text())
        api = next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='API' for t in n.targets))
        namespace = dict(Counter=Counter, copy=copy, deepcopy=deepcopy, hashlib=hashlib, math=math, re=re,
            API=ast.literal_eval(api), VERSION='audit-only')
        ns=extract('stage_0_5_identity_observation.py', ['check','finite','IdentityObserver'], namespace)
        observer=ns['IdentityObserver']([dict(id='synthetic_pending',depart_s=0)])
        for i in range(3):
            frame=dict(time_s=i*.05,phase='initial_snapshot' if i==0 else 'after_simulationStep',
                       discarded=None,native_departures={},unavailable={})
            frame.update({key:[] for key in namespace['API']})
            frame['pending']=['synthetic_pending']
            observer.ingest(frame)
        result=observer.finish()
        self.assertTrue(result['identity_accounting_complete'])
        self.assertTrue(result['native_departure_clock_complete'])
        self.assertIsNone(result['vehicles']['synthetic_pending']['actual_departure_s'])
        self.assertTrue(result['vehicles']['synthetic_pending']['right_censored'])


if __name__=='__main__':
    unittest.main(verbosity=2)
