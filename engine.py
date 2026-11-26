"""NutRelay offline Cashu denomination planner. No tokens, network, or custody."""
from dataclasses import dataclass
from collections import Counter
import hashlib, json, random, re, time
LIMIT = 100_000
@dataclass(frozen=True)
class Keyset:
    id: str
    denoms: tuple
    fee_ppk: int = 0
    expiry: int = 0
    verified: bool = False

def read_keysets(raw):
    """NUT-01 public JSON, NUT-02 ID verification (v1/v2); single active sat keyset."""
    if not isinstance(raw, str) or len(raw) > 1_000_000:
        raise ValueError("Keyset JSON exceeds size limit")
    obj = json.loads(raw)
    out = []; seen=set()
    if not isinstance(obj,dict) or not isinstance(obj.get("keysets"),list) or len(obj["keysets"])>64: raise ValueError("Invalid keysets array")
    for k in obj["keysets"]:
        if k.get("unit") != "sat" or k.get("active") is not True:
            continue
        fee, expiry = k.get("input_fee_ppk") or 0, k.get("final_expiry") or 0
        if type(fee) is not int or not 0 <= fee <= 1_000_000 or type(expiry) is not int or expiry < 0:
            raise ValueError("Invalid fee or expiry")
        if expiry and expiry <= int(time.time()):
            continue
        pairs = sorted((int(a), v.lower()) for a,v in k["keys"].items())
        if not pairs or len(pairs)>64 or len({a for a,_ in pairs})!=len(pairs):
            raise ValueError("Invalid denomination set")
        if any(a <= 0 or a > 2**63-1 or not re.fullmatch(r"0[23][0-9a-f]{64}",v) for a,v in pairs):
            raise ValueError("Malformed denomination/public key")
        kid=k["id"].lower()
        if re.fullmatch(r"00[0-9a-f]{14}",kid):
            expect="00"+hashlib.sha256(b"".join(bytes.fromhex(v) for a,v in pairs)).hexdigest()[:14]
        elif re.fullmatch(r"01[0-9a-f]{64}",kid):
            pre=",".join(f"{a}:{v}" for a,v in pairs)+"|unit:sat"
            if fee: pre+=f"|input_fee_ppk:{fee}"
            if expiry: pre+=f"|final_expiry:{expiry}"
            expect="01"+hashlib.sha256(pre.encode()).hexdigest()
        else:
            raise ValueError("Unsupported keyset ID version")
        if kid!=expect: raise ValueError("Public keyset ID mismatch")
        if kid in seen: raise ValueError("Duplicate public keyset ID")
        seen.add(kid)
        if not any(a<=LIMIT for a,_ in pairs): continue
        out.append(Keyset(kid,tuple(a for a,_ in pairs if a<=LIMIT),fee,expiry,True))
    if not out: raise ValueError("No supported, active, unexpired sat keyset")
    return out

DEMO=Keyset("DEMO (not a real mint)",tuple(2**i for i in range(17)),100)

def validate(budget,orders):
    if type(budget) is not int or not 1<=budget<=LIMIT: raise ValueError("Budget: 1–100,000 sats")
    if not 1<=len(orders)<=60 or any(type(a) is not int or not 1<=a<=LIMIT for a in orders):
        raise ValueError("Enter 1–60 positive integer payment amounts, up to 100,000 sats")
    if sum(orders)>budget: raise ValueError("Planned payments exceed budget")

def unbounded_table(denoms,maximum):
    """Minimum proof count for arbitrary mint-supported denominations."""
    denoms=tuple(sorted(set(denoms),reverse=True))
    inf=maximum+1
    costs=[0]+[inf]*maximum; last=[0]*(maximum+1)
    for d in denoms:
        for a in range(d,maximum+1):
            if costs[a-d]+1<costs[a]:
                costs[a]=costs[a-d]+1;last[a]=d
    def split(a):
        if not 0<=a<=maximum or costs[a]==inf: raise ValueError("Amount not representable by this keyset")
        c=Counter()
        while a:
            d=last[a];c[d]+=1;a-=d
        return c
    return split

def inventory_value(inv): return sum(d*n for d,n in inv.items())
def proof_count(inv): return sum(inv.values())
def fee(n,ppk): return (n*ppk+999)//1000

def prepare(budget,orders,keyset):
    validate(budget,orders)
    split=unbounded_table(keyset.denoms,budget)
    compact=split(budget)
    ready=Counter()
    for a in orders: ready.update(split(a))
    reserve=split(budget-sum(orders));ready.update(reserve)
    return compact,ready

def select_exact(inv,target):
    """Bounded subset sum, minimum proofs, grouped via binary decomposition."""
    if target<0 or target>LIMIT: return None
    if target==0:return Counter()
    if inventory_value(inv)<target:return None
    # immutable path nodes ensure no accidental reuse during in-place DP
    dp={0:(0,None)}
    for d,n in sorted(inv.items(),reverse=True):
        remaining=min(n,target//d);chunk=1
        while remaining:
            count=min(chunk,remaining); remaining-=count; chunk*=2
            value=d*count
            for a,(cost,path) in list(dp.items()):
                b=a+value
                if b<=target and (b not in dp or cost+count<dp[b][0]):
                    dp[b]=(cost+count,(d,count,path))
    if target not in dp:return None
    result=Counter();node=dp[target][1]
    while node:
        d,n,node=node;result[d]+=n
    return result

def simulate(inventory,orders,ppk):
    inv=Counter(inventory); steps=[]
    for a in orders:
        chosen=select_exact(inv,a)
        if chosen is None:
            steps.append({"amount":a,"success":False,"proofs":0,"fee":0})
        else:
            inv.subtract(chosen)
            steps.append({"amount":a,"success":True,"proofs":proof_count(chosen),
                          "fee":fee(proof_count(chosen),ppk)})
    return {"steps":steps,"paid":sum(s["amount"] for s in steps if s["success"]),
            "success":sum(s["success"] for s in steps),"remaining":inventory_value(inv),
            "recipient_fee_estimate":sum(s["fee"] for s in steps)}

def compare(budget,orders,keyset):
    compact,ready=prepare(budget,orders,keyset)
    # The planned packets are allocated separately, guaranteeing non-overlap.
    split=unbounded_table(keyset.denoms,max(orders))
    packets=[split(a) for a in orders]
    prepared_steps=[{"amount":a,"success":True,"proofs":proof_count(p),
        "fee":fee(proof_count(p),keyset.fee_ppk)} for a,p in zip(orders,packets)]
    prepared={"steps":prepared_steps,"paid":sum(orders),"success":len(orders),
        "remaining":budget-sum(orders),"recipient_fee_estimate":sum(s["fee"] for s in prepared_steps)}
    # Stress test: each amount is jittered by up to 20%, then shuffled; pooled inventories.
    rng=random.Random(420); trials=max(2,min(40,2_000_000//(budget*len(orders)))); totals=[0,0]
    for _ in range(trials):
        sample=[max(1,min(LIMIT,a+rng.randint(-(a//5),a//5))) for a in orders]
        rng.shuffle(sample)
        for i,inv in enumerate((compact,ready)):
            totals[i]+=simulate(inv,sample,keyset.fee_ppk)["success"]
    return {"compact":dict(compact),"ready":dict(ready),"baseline":simulate(compact,orders,keyset.fee_ppk),
        "prepared":prepared,"stress":[round(100*t/(trials*len(orders)),1) for t in totals],
        "trials":trials,"packets":[dict(p) for p in packets]}
