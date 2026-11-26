import itertools,json,hashlib,random,unittest
from collections import Counter
from pathlib import Path
from engine import *
class EngineTests(unittest.TestCase):
    def test_exact_matches_bruteforce(self):
        rng=random.Random(42)
        for _ in range(150):
            values=[rng.randint(1,12) for i in range(rng.randint(1,9))]
            target=rng.randint(0,45)
            good=[len(s) for n in range(len(values)+1) for s in itertools.combinations(values,n) if sum(s)==target]
            selected=select_exact(Counter(values),target)
            if not good:self.assertIsNone(selected)
            else:
                self.assertEqual(proof_count(selected),min(good))
                self.assertEqual(inventory_value(selected),target)
                self.assertFalse(selected-Counter(values))
    def test_nonbinary(self):
        split=unbounded_table([1,3,4],20)
        self.assertEqual(split(6),{3:2})
        with self.assertRaises(ValueError):unbounded_table([3,4],20)(2)
    def test_conservation(self):
        r=compare(2400,[120,75,230,95,400,65,180,50,200,125],DEMO)
        for k in ("compact","ready"):self.assertEqual(inventory_value(r[k]),2400)
        for k in ("prepared","baseline"):self.assertEqual(r[k]["remaining"]+r[k]["paid"],2400)
        self.assertEqual(r["prepared"]["success"],10)
        self.assertEqual(r["stress"],compare(2400,[120,75,230,95,400,65,180,50,200,125],DEMO)["stress"])
    def test_no_reuse(self):
        r=simulate({4:1,1:1},[4,4,1],100)
        self.assertEqual(r["success"],2);self.assertEqual(r["remaining"],0)
    def test_fee(self):
        self.assertEqual([fee(n,100) for n in (0,1,10,11)],[0,1,1,2])
    def test_validation(self):
        for b,o in [(10,[11]),(0,[1]),(50,[]),(50,[0]),(100001,[1])]:
            with self.assertRaises(ValueError):prepare(b,o,DEMO)
    def test_public_snapshot_and_tampering(self):
        p=Path(__file__).with_name("testnut-public-keys.json")
        raw=p.read_text(); self.assertTrue(read_keysets(raw)[0].verified)
        data=json.loads(raw);next(k for k in data["keysets"] if k["unit"]=="sat")["input_fee_ppk"]=101
        with self.assertRaises(ValueError):read_keysets(json.dumps(data))
    def test_v1(self):
        data=json.loads(Path(__file__).with_name("testnut-public-keys.json").read_text())
        k=next(k for k in data["keysets"] if k["unit"]=="sat"); pairs=sorted((int(a),v) for a,v in k["keys"].items())
        k["id"]="00"+hashlib.sha256(b"".join(bytes.fromhex(v) for _,v in pairs)).hexdigest()[:14]
        self.assertTrue(read_keysets(json.dumps(data))[0].verified)
    def test_expired(self):
        data=json.loads(Path(__file__).with_name("testnut-public-keys.json").read_text())
        next(k for k in data["keysets"] if k["unit"]=="sat")["final_expiry"]=1
        with self.assertRaises(ValueError):read_keysets(json.dumps(data))
if __name__=="__main__":unittest.main(verbosity=2)
