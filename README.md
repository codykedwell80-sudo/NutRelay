# NutRelay / Blackout Lab

**Prepare for the outage before it happens.**

A local-first Cashu denomination planner and outage simulator for festivals, emergency supply purchases and creator tips. It asks a deceptively simple question: if a wallet cannot contact its mint to make change, how many planned payments could it actually cover with the proofs it already has?

## Run

Requires Python 3.10+ and Tkinter. No Python package installs, servers, accounts, wallets or funds required.

```sh
python3 app.py
python3 test_engine.py
```

Choose a scenario, edit the budget and payment list, and run the simulator. Import the included `testnut-public-keys.json` to use a public Cashu test mint snapshot instead of synthetic settings. Or import a public NUT-01 /v1/keys response from a mint of your choice. Only public JSON is accepted; never paste a wallet seed, secret or token.

## How it works

- Reads active sat-denominated Cashu keysets from NUT-01 JSON, checks NUT-02 v1/v2 keyset IDs, skips expired sets, uses supported denominations and fee metadata. If multiple eligible keysets are present, the UI uses the first and tells you.
- Uses dynamic programming to find a minimum-count representation of the budget and each forecast payment, even for non-binary denominations.
- Plans disjoint packets for known payments and a reserve. Compares that plan against a compact minimum-proof inventory.
- Simulates bounded exact-change selection without reusing proofs, then compares pooled inventories in reproducible random order/amount stress scenarios (up to 40, seed 420).
- Estimates recipient input fees per separate hypothetical redemption swap using the NUT-02 integer formula. Fees are not subtracted from the simulated face-value budget, and preparation costs are not estimated.
- Exports a JSON denomination plan and scenario report. No wallet secrets, no network calls in the app.

The default festival example is deliberately a demonstration of a denomination bottleneck, not a claim that all ordinary wallets behave this way. The prepared plan's planned-payment success is guaranteed by construction if all requested amounts and reserve are representable. The randomized stress test compares both inventories using the same selector, and does not guarantee real-world reliability.

## Safety and scope

This is a planner, not a wallet. No ecash is minted, transferred, received or spent. It never handles actual Cashu proofs or their secrets. It checks the public keyset ID's consistency, not the validity of mint signatures, the mint's trustworthiness, its solvency, or public curve-point membership. A snapshot can become stale. Fees on legacy v1 keysets are not authenticated by their ID. Actual offline recipients still face double-spend and mint risk; eventual redemption requires connectivity. No claim that payments are guaranteed. Use trusted wallet software to implement a plan; fees and availability may differ. One active sat keyset at a time. Budgets limited to 100,000 sats, 60 planned payments; stress trial count decreases with workload. JSON export exposes your forecast amounts, so share it only if appropriate.

## Evidence

Tested on Arch Linux with Python/Tk. Nine automated tests including 150 random small exact-change cases compared against exhaustive enumeration, conservation, no proof reuse, keyset tamper detection, v1 compatibility, expiry and fee rounding. Desktop GUI smoke test passed. Public test-mint keyset snapshot fetched November 27, 2026; the active sat v2 ID matched its data. No real money was used.

## Protocol references

- NUT-01: https://cashubtc.github.io/nuts/01/
- NUT-02: https://cashubtc.github.io/nuts/02/
- Official Cashu test mint: https://testnut.cashu.space (test funds only)
- Hackathon: https://nutnovember.org/

New project created November 27, 2026 for Nut November; AI-assisted development. MIT license. No pre-November project code incorporated.
