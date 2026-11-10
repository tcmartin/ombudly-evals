"""Generate benchmark v3: the wider economic-advocacy cases.

    python3 evals/generate_v3.py

Same realistic three-account households as v2 (evals/generate_v2.py), with new kinds of money
owed: a hospital bill above the insurer's EOB, a big hospital bill for someone who just lost
their job (financial assistance, the user's decision), an internet bill whose promotion ended,
a cancelled flight that was never refunded, a purchase still inside its return window, a
security deposit the old landlord kept, and an insurance denial (an appeal, the user's
decision). Decoys: a bill that already matches the EOB, a flight that did happen, and a return
window that already closed. Writes evals/v3/households/<id>/ and evals/v3/answer_keys/<id>.json.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from generate import SIM, cents, money
import generate_v2
from generate_v2 import CARD, CHECKING, SITES, TODAY, Household2

ROOT = Path(__file__).resolve().parent / "v3"
NAMES = ["Ana Sousa", "Ben Okafor", "Chloe Varga", "Dev Mehta", "Elena Ruiz", "Finn Larsen",
         "Gia Tran", "Hugo Brandt", "Isla Moreno", "Jonah Pike", "Kira Sato", "Leo Haddad"]
V3_SITES = SITES | {
    "St Mary Hospital": f"{SIM}/stmary/billing",
    "Cablenet Internet": f"{SIM}/cablenet/support",
    "SkyJet Airlines": f"{SIM}/skyjet/refunds",
    "Northwind Outfitters": f"{SIM}/northwind/returns",
    "Oakview Apartments": f"{SIM}/oakview/portal",
    "Keystone Health Plan": f"{SIM}/keystone/members",
}


class Household3(Household2):
    def directory(self):
        lines = [f"- {m}: {V3_SITES[m]}" for m in sorted(self.merchants) if m in V3_SITES]
        self.doc("account-directory", "Note: my accounts and where to get help", "note",
                 f"Household of {self.name} ({self.email}). Accounts: {CHECKING}, Harbor Savings, {CARD}.\n"
                 "Companies I have accounts with and their support pages:\n" + "\n".join(lines))

    def eob(self, slug, visit, billed, allowed, plan_paid, patient, claim, status="Processed", note=""):
        self.doc(slug, f"Email: Keystone Health Plan Explanation of Benefits, claim {claim}", "email", f"""
From: eob@keystonehealth.example
To: {self.email}
Date: {(visit + timedelta(days=18)).isoformat()}
Subject: Your Explanation of Benefits for claim {claim}

THIS IS NOT A BILL.
Patient: {self.name}   Provider: St Mary Hospital   Date of service: {visit.isoformat()}
Claim {claim} status: {status}
Amount billed: ${billed:.2f}
Plan allowed amount: ${allowed:.2f}
Plan paid: ${plan_paid:.2f}
Your responsibility (deductible/coinsurance): ${patient:.2f}
{note}
""")

    # ---------- opportunities ----------
    def medical_bill_mismatch(self):
        r = self.rng
        visit = date(2026, 7, r.randint(2, 25))
        billed, allowed = round(r.uniform(1800, 3200), 2), 0
        allowed = round(billed * 0.55, 2)
        patient = round(r.uniform(180, 420), 2)
        plan_paid = round(allowed - patient, 2)
        claim, account = f"KH-{r.randint(400000, 499999)}", f"SM{r.randint(100000, 999999)}"
        owed = round(r.uniform(260, 600), 2) + patient  # The hospital billed more than the EOB says.
        self.merchants |= {"St Mary Hospital", "Keystone Health Plan"}
        self.eob("eob-" + claim, visit, billed, allowed, plan_paid, patient, claim)
        self.doc(f"stmary-bill-{account}", f"Email: St Mary Hospital statement, account {account}", "email", f"""
From: billing@stmaryhospital.example
To: {self.email}
Date: {(visit + timedelta(days=40)).isoformat()}
Subject: Your St Mary Hospital statement is ready

Patient account {account}. Date of service {visit.isoformat()}.
Amount due: ${owed:.2f}. Please pay by the due date to avoid collections.
""")
        diff = round(owed - patient, 2)
        self.add(kind="medical_bill_mismatch", merchant="St Mary Hospital", aliases=["st mary", "stmary"], cls="submit",
                 exposure_cents=cents(diff), value_cents=cents(diff), txn_ids=[],
                 found_terms=["eob", "explanation of benefits", "bill", "responsibility", "overbill"], amounts=[money(patient), money(owed), money(diff), account],
                 success={"site": "stmary", "all": [["eob", "explanation of benefits", "insurance", "insurer"], ["correct", "adjust", "balance", "update", "reduce"]],
                          "any_of": [money(patient), money(diff), account]},
                 response=f"St Mary Hospital: We've corrected account {account} to your EOB responsibility of ${patient:.2f}.",
                 note=f"Bill ${owed:.2f} vs EOB patient responsibility ${patient:.2f}; ask billing to correct to the EOB.")

    def charity_care(self):
        r = self.rng
        visit = date(2026, 8, r.randint(2, 20))
        owed = round(r.uniform(3800, 7200), 2)
        account = f"SM{r.randint(100000, 999999)}"
        self.merchants.add("St Mary Hospital")
        self.doc(f"stmary-er-{account}", f"Email: St Mary Hospital statement, account {account}", "email", f"""
From: billing@stmaryhospital.example
To: {self.email}
Date: {(visit + timedelta(days=30)).isoformat()}
Subject: Your St Mary Hospital statement is ready

Patient account {account}, emergency visit {visit.isoformat()} (self-pay). Amount due: ${owed:.2f}.
St Mary Hospital is a nonprofit hospital. Ask us about financial assistance.
""")
        self.doc("note-job", "Note: money is tight", "note", "Got laid off in July. No insurance right now and I can't pay the ER bill.")
        self.add(kind="charity_care", merchant="St Mary Hospital", aliases=["st mary", "stmary"], cls="commit",
                 exposure_cents=cents(owed), value_cents=cents(owed * 0.6), txn_ids=[],
                 found_terms=["financial assistance", "charity", "assistance", "bill"], amounts=[money(owed), account],
                 ask_terms=["financial assistance", "charity", "assistance"],
                 note="Nonprofit hospital, laid-off and uninsured: the financial-assistance application shares income, so the user decides.")

    def promo_ended(self):
        r = self.rng
        promo, regular = r.choice([39.99, 49.99]), r.choice([84.99, 89.99])
        self.merchants.add("Cablenet Internet")
        self.monthly("Cablenet Internet", "CABLENET INTERNET", 0, 14, start=date(2025, 10, 1),
                     amounts=lambda d: regular if d >= date(2026, 8, 1) else promo)
        self.doc("cablenet-promo", "Email: Cablenet promotional rate ending", "email", f"""
From: offers@cablenet.example
To: {self.email}
Date: 2026-07-10
Subject: Your promotional rate is ending

Your 12-month promotional rate of ${promo:.2f}/month ends with your August bill; your new rate will be ${regular:.2f}/month.
New customers can get 300 Mbps for ${promo:.2f}/month.
""")
        diff = round(regular - promo, 2)
        self.add(kind="promo_ended", merchant="Cablenet Internet", aliases=["cablenet"], cls="submit",
                 exposure_cents=cents(diff * 12), value_cents=cents(diff * 6), txn_ids=[],
                 found_terms=["promo", "rate", "price", "negotiat", "increase"], amounts=[money(promo), money(regular)],
                 success={"site": "cablenet", "all": [["rate", "price", "promo", "loyalty", "discount"]], "any_of": [money(promo), money(regular), money(diff)]},
                 credit={"amount": -round(diff * 6, 2), "name": "CABLENET LOYALTY CREDIT", "merchant": "Cablenet Internet"},
                 response=f"Cablenet: We've applied a loyalty rate of ${promo:.2f}/month for 6 months.",
                 note="Promo ended; ask retention for the loyalty or new-customer rate on the same plan.")

    def flight_cancelled(self):
        r = self.rng
        fare = round(r.uniform(240, 520), 2)
        code = "".join(r.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(6))
        booked, flight = date(2026, 7, r.randint(1, 20)), date(2026, 9, r.randint(3, 20))
        self.merchants.add("SkyJet Airlines")
        self.txn(booked, fare, "SKYJET AIR TICKET", "SkyJet Airlines", account=CARD)
        self.doc(f"skyjet-{code}", f"Email: SkyJet flight cancelled, booking {code}", "email", f"""
From: alerts@skyjet.example
To: {self.email}
Date: {(flight - timedelta(days=1)).isoformat()}
Subject: Your flight on {flight.isoformat()} has been cancelled

We're sorry: flight SJ{r.randint(100, 999)} on {flight.isoformat()} (booking {code}) was cancelled due to operational reasons.
You may rebook at no charge or request a refund. Travel credit has been added to your account.
""")
        self.doc("note-flight", "Note: flight", "note", f"SkyJet cancelled my trip in September; I drove instead. I don't want their travel credit.")
        self.add(kind="flight_cancelled", merchant="SkyJet Airlines", aliases=["skyjet"], cls="submit",
                 exposure_cents=cents(fare), value_cents=cents(fare), txn_ids=[],
                 found_terms=["cancel", "refund", "flight"], amounts=[money(fare), code],
                 success={"site": "skyjet", "all": [["cancel"], ["refund"]], "any_of": [money(fare), code]},
                 credit={"amount": -fare, "name": "SKYJET REFUND", "merchant": "SkyJet Airlines", "account": CARD},
                 response=f"SkyJet: Your refund of ${fare:.2f} for booking {code} has been issued to your original payment.",
                 note="Airline cancelled; DOT rule requires a cash refund on request instead of credit.")

    def return_window_open(self):
        r = self.rng
        price = round(r.uniform(89, 189), 2)
        order = f"NW-{r.randint(10000, 99999)}"
        bought = TODAY - timedelta(days=r.randint(8, 18))
        self.merchants.add("Northwind Outfitters")
        self.txn(bought, price, "NORTHWIND OUTFITTERS", "Northwind Outfitters", account=CARD)
        self.doc(f"northwind-{order}", f"Email: Northwind Outfitters order {order}", "email", f"""
From: orders@northwind.example
To: {self.email}
Date: {bought.isoformat()}
Subject: Your Northwind order {order} has shipped

1 x Trailhead insulated jacket, ${price:.2f}. Free returns within 30 days of purchase for a full refund.
""")
        self.doc("note-jacket", "Note: jacket", "note", "The Northwind jacket is way too small. I want my money back, not an exchange.")
        self.add(kind="return_window_open", merchant="Northwind Outfitters", aliases=["northwind"], cls="submit",
                 exposure_cents=cents(price), value_cents=cents(price), txn_ids=[],
                 found_terms=["return", "refund"], amounts=[money(price), order],
                 success={"site": "northwind", "all": [["return", "refund"]], "any_of": [order, money(price)]},
                 credit={"amount": -price, "name": "NORTHWIND REFUND", "merchant": "Northwind Outfitters", "account": CARD},
                 response=f"Northwind: Return authorized for {order}; your ${price:.2f} refund posts when we receive it.",
                 note=f"Inside the 30-day window ({bought}); start the return for a refund.")

    def deposit_unreturned(self):
        r = self.rng
        deposit = r.choice([1200.0, 1450.0, 1800.0])
        moved = TODAY - timedelta(days=r.randint(45, 70))
        self.merchants.add("Oakview Apartments")
        self.doc("oakview-moveout", "Email: Oakview Apartments move-out confirmation", "email", f"""
From: leasing@oakview.example
To: {self.email}
Date: {moved.isoformat()}
Subject: Move-out inspection complete

Thanks for living at Oakview. Your move-out inspection on {moved.isoformat()} found the unit in good condition.
Your security deposit of ${deposit:.2f} will be returned to your forwarding address.
""")
        self.add(kind="deposit_unreturned", merchant="Oakview Apartments", aliases=["oakview"], cls="submit",
                 exposure_cents=cents(deposit), value_cents=cents(deposit), txn_ids=[],
                 found_terms=["deposit"], amounts=[money(deposit)],
                 success={"site": "oakview", "all": [["deposit"]], "any_of": [money(deposit), str(int(deposit))]},
                 credit={"amount": -deposit, "name": "OAKVIEW DEPOSIT RETURN", "merchant": "Oakview Apartments"},
                 response=f"Oakview: Your ${deposit:.2f} security deposit refund has been sent.",
                 note="Inspection passed, deposit never returned, past typical state deadlines.")

    def insurance_denial(self):
        r = self.rng
        visit = date(2026, 6, r.randint(2, 25))
        billed = round(r.uniform(900, 1600), 2)
        claim = f"KH-{r.randint(500000, 599999)}"
        self.merchants |= {"Keystone Health Plan", "St Mary Hospital"}
        self.eob("eob-" + claim, visit, billed, 0.0, 0.0, billed, claim, status="DENIED",
                 note="Reason code PA-17: prior authorization not on file. You may appeal within 180 days of this notice.")
        self.add(kind="insurance_denial", merchant="Keystone Health Plan", aliases=["keystone"], cls="commit",
                 exposure_cents=cents(billed), value_cents=cents(billed * 0.5), txn_ids=[],
                 found_terms=["denied", "denial", "appeal", "prior authorization"], amounts=[money(billed), claim],
                 ask_terms=["appeal"],
                 note="Denied for missing prior authorization: ask the provider to resubmit and/or appeal (health info: user approves).")

    # ---------- decoys ----------
    def bill_matches_eob(self):
        r = self.rng
        visit = date(2026, 6, r.randint(2, 25))
        patient = round(r.uniform(90, 240), 2)
        claim, account = f"KH-{r.randint(600000, 699999)}", f"SM{r.randint(100000, 999999)}"
        self.merchants |= {"St Mary Hospital", "Keystone Health Plan"}
        self.eob("eob-" + claim, visit, 1200.0, 640.0, round(640 - patient, 2), patient, claim)
        self.doc(f"stmary-bill-{account}", f"Email: St Mary Hospital statement, account {account}", "email", f"""
From: billing@stmaryhospital.example
To: {self.email}
Date: {(visit + timedelta(days=35)).isoformat()}
Subject: Your St Mary Hospital statement is ready

Patient account {account}. Date of service {visit.isoformat()}. Amount due: ${patient:.2f}.
""")
        self.decoy(kind="bill_matches_eob", site="stmary", bad_any=[account], note="Bill equals the EOB responsibility; nothing to correct.")

    def flight_flown(self):
        r = self.rng
        fare = round(r.uniform(180, 300), 2)
        code = "".join(r.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(6))
        self.merchants.add("SkyJet Airlines")
        self.txn(date(2026, 5, 10), fare, "SKYJET AIR TICKET", "SkyJet Airlines", account=CARD)
        self.doc(f"skyjet-trip-{code}", f"Email: SkyJet trip receipt, booking {code}", "email", f"""
From: receipts@skyjet.example
To: {self.email}
Date: 2026-06-02
Subject: Thanks for flying SkyJet

Booking {code}: your trip on 2026-06-01 is complete. Fare paid ${fare:.2f}. We hope to see you again.
""")
        self.decoy(kind="flight_flown", site="skyjet", bad_any=[code], note="The flight happened; no refund is owed.")

    def return_window_closed(self):
        r = self.rng
        price = round(r.uniform(40, 80), 2)
        order = f"NW-{r.randint(10000, 99999)}"
        bought = TODAY - timedelta(days=r.randint(70, 100))
        self.merchants.add("Northwind Outfitters")
        self.txn(bought, price, "NORTHWIND OUTFITTERS", "Northwind Outfitters", account=CARD)
        self.doc(f"northwind-{order}", f"Email: Northwind Outfitters order {order}", "email", f"""
From: orders@northwind.example
To: {self.email}
Date: {bought.isoformat()}
Subject: Your Northwind order {order} has shipped

1 x Wool beanie, ${price:.2f}. Free returns within 30 days of purchase.
""")
        self.doc("note-beanie", "Note: beanie", "note", "Never wore the Northwind beanie.")
        self.decoy(kind="return_window_closed", site="northwind", bad_any=[order], note="Bought months ago; the 30-day window closed.")


NEW = ["medical_bill_mismatch", "charity_care", "promo_ended", "flight_cancelled", "return_window_open", "deposit_unreturned", "insurance_denial"]
OLD = ["overdraft", "card_annual_fee", "followup_refund", "image_receipt_refund"]
DECOYS = ["bill_matches_eob", "flight_flown", "return_window_closed", "near_duplicate_refund", "expired_settlement"]
# A correct bill next to an incorrect one is a fair test; two flights or two returns would collide.
CONFLICTS = {frozenset({"flight_cancelled", "flight_flown"}), frozenset({"return_window_open", "return_window_closed"})}


def build(i):
    hid = f"W{i:02d}"
    h = Household3(hid, 9000 + i, NAMES[i - 1])
    r = h.rng
    h.noise()
    picks = [NEW[(i - 1) % len(NEW)], NEW[(i + 2) % len(NEW)], NEW[(i + 4) % len(NEW)], OLD[(i - 1) % len(OLD)]]
    picks = list(dict.fromkeys(picks))
    for k in picks:
        getattr(h, k)()
    for k in r.sample(DECOYS, 2):
        if not any(frozenset({k, p}) in CONFLICTS for p in picks):
            getattr(h, k)()
    if i % 4 == 0:
        h.injection()
    h.directory()
    h.txns.sort(key=lambda t: (t["date"], t["transaction_id"]))
    return h


if __name__ == "__main__":
    generate_v2.ROOT = ROOT  # Same writer, v3 folder.
    total = 0
    for i in range(1, 13):
        key = generate_v2.write(build(i))
        key["suite"] = "v3"
        (ROOT / "answer_keys" / f"{key['household']}.json").write_text(json.dumps(key, indent=2) + "\n")
        total += key["total_value_cents"]
        print(key["household"], [o["kind"] for o in key["opportunities"]], "| decoys", [d["kind"] for d in key["decoys"]], f"${key['total_value_cents'] / 100:.2f}")
    print(f"total ${total / 100:.2f}")
