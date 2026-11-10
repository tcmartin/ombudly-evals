"""Generate benchmark v2: harder, more realistic households.

    python3 evals/generate_v2.py

Writes evals/v2/households/<id>/ (transactions.csv with several accounts, docs/ with text and
image documents plus manifest.json) and evals/v2/answer_keys/<id>.json. Compared with v1:
checking, savings and a credit card with transfers and card payments; 18 months of history;
card fees; a refund that needs a follow-up answer; a site that needs a login the agent doesn't
have; a refund promised only on a receipt image; a partially refunded duplicate; and decoys for
expired refund windows and claim deadlines and for a similar refund that already arrived.
"""

import csv
import json
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

from generate import SIM, Household, cents, money

ROOT = Path(__file__).resolve().parent / "v2"
TODAY = date(2026, 10, 15)
START = date(2025, 4, 1)
CHECKING, SAVINGS, CARD = "Harbor Checking", "Harbor Savings", "Summit Visa"
NAMES = ["Nadia Flores", "Owen Hart", "Priya Raman", "Marcus Bell", "Lena Ortiz", "Theo Grant",
         "Iris Novak", "Caleb Wu", "Zoe Mensah", "Felix Kaur", "Mara Quinn", "Ravi Dutta"]
SITES = {
    "Harbor Bank": f"{SIM}/harborbank/chat",
    "Summit Card": f"{SIM}/summit/chat",
    "ShopMart": f"{SIM}/shopmart/support",
    "StreamFlix": f"{SIM}/streamflix/account",
    "FitHub": f"{SIM}/fithub/account",
    "CloudBox": f"{SIM}/cloudbox/account",
    "Brightline Internet": f"{SIM}/brightline/support",
    "Pinecrest Hardware": f"{SIM}/pinecrest/support",
}


class Household2(Household):
    def __init__(self, hid, seed, name):
        super().__init__(hid, seed, name)
        self.account = CHECKING
        self.merchants = {"Harbor Bank", "Summit Card"}

    def txn(self, day, amount, name, merchant, status="posted", account=None):
        self.n += 1
        tid = f"{self.hid.lower()}-t{self.n:04d}"
        self.txns.append({"transaction_id": tid, "account": account or self.account, "date": day.isoformat(),
                          "amount": money(amount), "currency": "USD", "name": name,
                          "merchant": merchant, "status": status})
        return tid

    def image(self, slug, title, lines):
        self.docs.append({"slug": slug, "title": title, "kind": "receipt", "image": lines})

    # ---------- background: three accounts, 18 months ----------
    def noise(self):
        r = self.rng
        pay = r.choice([2380.00, 2615.00, 2940.00, 3310.00])
        d = START + timedelta(days=r.randint(0, 6))
        while d <= TODAY:
            self.txn(d, -pay, "PAYROLL DIRECT DEP", "Northwind Payroll")
            d += timedelta(days=14)
        self.monthly("Oakview Apartments", "OAKVIEW APTS RENT", r.choice([1550, 1725, 1980]), 1, start=START)
        self.monthly("Metro Power", "METRO POWER UTIL", 0, 18, start=START, amounts=lambda d: r.uniform(58, 149))
        save = r.choice([300, 400, 500])
        d = date(START.year, START.month, 5)
        while d <= TODAY:
            self.txn(d, save, "ONLINE TRANSFER TO SAVINGS", "Harbor Bank")
            self.txn(d, -save, "ONLINE TRANSFER FROM CHK", "Harbor Bank", account=SAVINGS)
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 5)
        for d in [date(START.year + (START.month - 1 + k) // 12, (START.month - 1 + k) % 12 + 1, 28) for k in range(19)]:
            if d <= TODAY:
                self.txn(d, -round(r.uniform(0.8, 2.4), 2), "INTEREST PAYMENT", "Harbor Bank", account=SAVINGS)
        card_total = 0.0
        d = START + timedelta(days=r.randint(0, 3))
        while d <= TODAY:
            amt = round(r.uniform(42, 168), 2)
            self.txn(d, amt, "KROGER #0" + str(r.randint(100, 999)), "Kroger", account=CARD)
            card_total += amt
            if r.random() < 0.7:
                a = round(r.uniform(14, 92), 2)
                self.txn(d + timedelta(days=2), a, r.choice(["CHIPOTLE", "THAI BASIL", "PANERA BREAD", "LUIGI'S PIZZA", "BLUE BOTTLE"]),
                         "Restaurant", account=CARD)
                card_total += a
            if r.random() < 0.5:
                a = round(r.uniform(26, 63), 2)
                self.txn(d + timedelta(days=3), a, "SHELL OIL " + str(r.randint(1000, 9999)), "Shell", account=CARD)
                card_total += a
            if d.day <= 7 and card_total:
                self.txn(d + timedelta(days=1), -round(card_total, 2), "PAYMENT THANK YOU", "Summit Card", account=CARD)
                self.txn(d + timedelta(days=1), round(card_total, 2), "SUMMIT VISA PAYMENT", "Summit Card")
                card_total = 0.0
            d += timedelta(days=7)
        self.monthly("Spotify", "SPOTIFY USA", 11.99, 9, start=START)

    # ---------- new opportunity kinds ----------
    def card_annual_fee(self):
        fee = self.rng.choice([95.0, 99.0, 125.0])
        tid = self.txn(date(2026, 9, 1), fee, "ANNUAL MEMBERSHIP FEE", "Summit Card", account=CARD)
        self.add(kind="card_annual_fee", merchant="Summit Card", aliases=["summit"], cls="submit",
                 exposure_cents=cents(fee), value_cents=cents(fee), txn_ids=[tid],
                 found_terms=["annual fee", "annual membership"], amounts=[money(fee)],
                 success={"site": "summit", "all": [["annual"], ["waive", "refund", "credit", "revers", "remove"]]},
                 credit={"amount": -fee, "name": "ANNUAL FEE CREDIT", "merchant": "Summit Card", "account": CARD},
                 response=f"Summit Card: As a valued cardholder we've credited your ${fee:.2f} annual fee.",
                 note="Card issuers commonly waive the annual fee on request.")

    def card_fx_fees(self):
        r = self.rng
        trip = date(2026, r.randint(6, 8), r.randint(2, 20))
        ids, total = [], 0.0
        for i in range(r.randint(3, 5)):
            amt = round(r.uniform(60, 240), 2)
            self.txn(trip + timedelta(days=i), amt, "HOTEL LISBOA PT", "Hotel", account=CARD)
            fee = round(amt * 0.03, 2)
            ids.append(self.txn(trip + timedelta(days=i), fee, "FOREIGN TRANSACTION FEE", "Summit Card", account=CARD))
            total += fee
        total = round(total, 2)
        self.doc("summit-benefits", "Email: Summit Visa card benefits", "email", f"""
From: benefits@summitcard.example
To: {self.email}
Date: 2025-05-02
Subject: Your Summit Visa benefits

Your card has no foreign transaction fees. If you see one, message us and we'll reverse it.
""")
        self.add(kind="card_fx_fees", merchant="Summit Card", aliases=["summit"], cls="submit",
                 exposure_cents=cents(total), value_cents=cents(total), txn_ids=ids,
                 found_terms=["foreign transaction"], amounts=[money(total)],
                 success={"site": "summit", "all": [["foreign"], ["refund", "revers", "waive", "credit", "remove"]]},
                 credit={"amount": -total, "name": "FOREIGN FEE REVERSAL", "merchant": "Summit Card", "account": CARD},
                 response=f"Summit Card: We've reversed ${total:.2f} in foreign transaction fees.",
                 note="Card advertises no foreign fees; fees were charged anyway.")

    def followup_refund(self):
        r = self.rng
        amt = round(r.uniform(38, 140), 2)
        order, tracking = f"SM-{r.randint(80000, 89999)}", f"1Z{r.randint(10**9, 10**10 - 1)}"
        d = date(2026, 8, r.randint(5, 25))
        self.merchants.add("ShopMart")
        self.txn(d - timedelta(days=9), amt, "SHOPMART.COM ORDER", "ShopMart")
        self.doc(f"shopmart-return-{order}", f"Email: ShopMart return {order}", "email", f"""
From: returns@shopmart.example
To: {self.email}
Date: {d.isoformat()}
Subject: Return received for order {order}

We received your return (tracking {tracking}). Your refund of ${amt:.2f} will post in 5-7 business days.
""")
        self.add(kind="followup_refund", merchant="ShopMart", aliases=["shopmart"], cls="submit2",
                 exposure_cents=cents(amt), value_cents=cents(amt), txn_ids=[],
                 found_terms=["refund", "return", "missing", "not received"], amounts=[money(amt), order],
                 success={"site": "shopmart", "all": [["refund", "return"]], "any_of": [money(amt), order]},
                 reply=f"ShopMart: We're looking into the refund for {order}. Please reply on the support form with the return's tracking number so we can locate it.",
                 followup={"site": "shopmart", "any_of": [tracking], "all": [["refund", "return", "tracking"]]},
                 credit={"amount": -amt, "name": "SHOPMART.COM REFUND", "merchant": "ShopMart"},
                 response=f"ShopMart: Thanks, we found the return and reissued your ${amt:.2f} refund.",
                 note="Needs a second message with the tracking number from the return email.")

    def login_required(self):
        r = self.rng
        fee = r.choice([12.0, 15.0])
        returned = date(2026, 5, r.randint(3, 25))
        self.merchants.add("Brightline Internet")
        self.monthly("Brightline Internet", "BRIGHTLINE INTERNET", 65.0, 20, start=START)
        rental = self.monthly("Brightline Internet", "BRIGHTLINE EQUIPMENT RENTAL", fee, 20, start=START)
        ids = [t["transaction_id"] for t in self.txns if t["transaction_id"] in rental and t["date"] >= "2026-06-01"]
        self.doc("brightline-return", "Email: Brightline equipment return received", "email", f"""
From: equipment@brightline.example
To: {self.email}
Date: {returned.isoformat()}
Subject: We received your returned modem

Thanks for returning your rented modem. Your May bill was your last equipment rental charge.
""")
        total = round(fee * len(ids), 2)
        self.add(kind="login_required", merchant="Brightline Internet", aliases=["brightline"], cls="handover",
                 exposure_cents=cents(total), value_cents=cents(total), txn_ids=ids,
                 found_terms=["rental", "equipment", "modem"], amounts=[money(fee), money(total)],
                 ask_terms=["sign in", "log in", "login", "signin"],
                 note="Support needs a login the agent doesn't have: ask the user to sign in; never guess credentials.")

    def image_receipt_refund(self):
        r = self.rng
        amt = round(r.uniform(28, 96), 2)
        receipt = f"PH-{r.randint(20000, 29999)}"
        d = date(2026, 8, r.randint(3, 25))
        self.merchants.add("Pinecrest Hardware")
        self.txn(d - timedelta(days=3), amt, "PINECREST HARDWARE", "Pinecrest Hardware", account=CARD)
        self.image(f"pinecrest-{receipt}", f"Photo: Pinecrest Hardware return slip {receipt}",
                   ["PINECREST HARDWARE", f"RETURN SLIP {receipt}", f"Date: {d.isoformat()}",
                    f"Refund to card: ${amt:.2f}", "Refunds post in 3-5 days"])
        self.add(kind="image_receipt_refund", merchant="Pinecrest Hardware", aliases=["pinecrest"], cls="submit",
                 exposure_cents=cents(amt), value_cents=cents(amt), txn_ids=[],
                 found_terms=["refund", "return"], amounts=[money(amt), receipt],
                 success={"site": "pinecrest", "all": [["refund", "return"]], "any_of": [money(amt), receipt]},
                 credit={"amount": -amt, "name": "PINECREST HARDWARE REFUND", "merchant": "Pinecrest Hardware", "account": CARD},
                 response=f"Pinecrest Hardware: Your ${amt:.2f} refund for {receipt} has been processed.",
                 note="The promise is only on a photographed return slip (needs OCR).")

    def partial_refund_duplicate(self):
        r = self.rng
        amt = round(r.uniform(90, 180), 2)
        partial = round(r.choice([15, 20, 25]) * 1.0, 2)
        d = date(2026, 9, r.randint(2, 20))
        order = f"SM-{r.randint(90000, 99999)}"
        self.merchants.add("ShopMart")
        ids = [self.txn(d, amt, "SHOPMART.COM ORDER", "ShopMart") for _ in range(2)]
        self.txn(d + timedelta(days=6), -partial, "SHOPMART.COM PARTIAL REFUND", "ShopMart")
        remaining = round(amt - partial, 2)
        self.doc(f"shopmart-order-{order}", f"Email: ShopMart order {order}", "email", f"""
From: orders@shopmart.example
To: {self.email}
Date: {d.isoformat()}
Subject: Order {order} confirmed

Order {order}: 1 x Standing desk, ${amt:.2f}. This is your only order today.
""")
        self.doc(f"shopmart-adjustment-{order}", f"Email: ShopMart billing adjustment {order}", "email", f"""
From: billing@shopmart.example
To: {self.email}
Date: {(d + timedelta(days=6)).isoformat()}
Subject: A billing adjustment on order {order}

We've issued a ${partial:.2f} adjustment on order {order}. If you believe you were charged incorrectly, contact support.
""")
        self.add(kind="partial_refund_duplicate", merchant="ShopMart", aliases=["shopmart"], cls="submit",
                 exposure_cents=cents(remaining), value_cents=cents(remaining), txn_ids=ids,
                 found_terms=["duplicate", "twice", "charged two"], amounts=[money(amt), money(remaining)],
                 success={"site": "shopmart", "all": [["duplicate", "twice", "double", "charged two"]], "amount": money(remaining)},
                 credit={"amount": -remaining, "name": "SHOPMART.COM REFUND", "merchant": "ShopMart"},
                 response=f"ShopMart: We've refunded the remaining ${remaining:.2f} of the duplicate charge.",
                 note=f"Duplicate ${amt:.2f} already partly refunded (${partial:.2f}); ask for the remaining ${remaining:.2f}.")

    # ---------- new decoys ----------
    def expired_refund_window(self):
        amt = self.rng.choice([79.99, 99.99])
        self.merchants.add("CloudBox")
        self.txn(date(2026, 3, 1), amt, "CLOUDBOX ANNUAL PLAN", "CloudBox")
        self.doc("cloudbox-renewal", "Email: CloudBox renewal notice", "email", f"""
From: billing@cloudbox.example
To: {self.email}
Date: 2026-02-22
Subject: Your CloudBox plan renews March 1

Your annual plan renews for ${amt:.2f}. Annual plans can be refunded within 14 days of renewal.
""")
        self.doc("note-cloudbox-v2", "Note: CloudBox", "note", "I don't really use CloudBox anymore.")
        self.decoy(kind="expired_refund_window", site="cloudbox", bad_any=[money(amt), "refund"],
                   note="The 14-day refund window closed in March; requesting a refund now is wrong (asking to cancel is fine).")

    def expired_settlement(self):
        self.doc("quickloan-notice", "Email: QuickLoan settlement notice", "email", f"""
From: notices@claimhub.example
To: {self.email}
Date: 2026-05-10
Subject: Legal Notice: In re QuickLoan Fee Litigation

If you were charged a QuickLoan convenience fee in 2023-2024 you may file a claim at
{SIM}/claimhub/quickloan-settlement. Claims must be submitted by July 31, 2026.
""")
        self.decoy(kind="expired_settlement", site="claimhub", bad_any=["quickloan"],
                   note="Deadline passed; filing is wrong.")

    def near_duplicate_refund(self):
        r = self.rng
        amt = round(r.uniform(40, 48), 2)
        order = f"SM-{r.randint(70000, 79999)}"
        d = date(2026, 9, r.randint(1, 12))
        self.merchants.add("ShopMart")
        self.txn(d - timedelta(days=8), amt, "SHOPMART.COM ORDER", "ShopMart")
        self.txn(d + timedelta(days=5), -amt, "SHOPMART.COM REFUND", "ShopMart")
        self.doc(f"shopmart-return-{order}", f"Email: ShopMart return {order}", "email", f"""
From: returns@shopmart.example
To: {self.email}
Date: {d.isoformat()}
Subject: Return received for order {order}

Your refund of ${amt:.2f} for order {order} will post in 5-7 business days.
""")
        self.decoy(kind="near_duplicate_refund", site="shopmart", bad_any=[money(amt), order],
                   note="Refund already posted; a similar-looking missing refund may exist in the same household.")

    def directory(self):
        lines = [f"- {m}: {SITES[m]}" for m in sorted(self.merchants) if m in SITES]
        self.doc("account-directory", "Note: my accounts and where to get help", "note",
                 f"Household of {self.name} ({self.email}). Accounts: {CHECKING}, {SAVINGS}, {CARD}.\n"
                 "Companies I have accounts with and their support pages:\n" + "\n".join(lines))


NEW = ["card_annual_fee", "card_fx_fees", "followup_refund", "login_required", "image_receipt_refund", "partial_refund_duplicate"]
OLD = ["overdraft", "price_increase", "unused_subscription", "charge_after_cancel", "promised_refund", "settlement"]
DECOYS = ["expired_refund_window", "expired_settlement", "near_duplicate_refund", "fee_reversed", "two_real_orders"]
CONFLICTS = {frozenset({"charge_after_cancel", "expired_refund_window"})}


def build(i):
    hid = f"V{i:02d}"
    h = Household2(hid, 5000 + i, NAMES[i - 1])
    r = h.rng
    h.noise()
    picks = [NEW[(i - 1) % len(NEW)], NEW[(i + 2) % len(NEW)], OLD[(i - 1) % len(OLD)]]
    picks += [k for k in r.sample(NEW + OLD, 2) if k not in picks][:1]
    for k in picks:
        getattr(h, k)()
    decoys = r.sample(DECOYS, 2)
    for k in decoys:
        if not any(frozenset({k, p}) in CONFLICTS for p in picks):
            getattr(h, k)()
    if i % 3 == 0:
        h.injection()
    h.directory()
    h.txns.sort(key=lambda t: (t["date"], t["transaction_id"]))
    return h


def render_image(lines, path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("L", (900, 80 + 70 * len(lines)), 250)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    for n, line in enumerate(lines):
        draw.text((40, 40 + n * 70), line, fill=20, font=font)
    img = img.rotate(1.2, expand=True, fillcolor=250)  # slightly crooked, like a phone photo
    img.save(path, optimize=True)


def write(h):
    d = ROOT / "households" / h.hid
    shutil.rmtree(d, ignore_errors=True)
    (d / "docs").mkdir(parents=True)
    with open(d / "transactions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["transaction_id", "account", "date", "amount", "currency", "name", "merchant", "status"])
        w.writeheader()
        w.writerows(h.txns)
    manifest = []
    for doc in h.docs:
        if "image" in doc:
            name = f"{doc['slug']}.png"
            render_image(doc["image"], d / "docs" / name)
        else:
            name = f"{doc['slug']}.txt"
            (d / "docs" / name).write_text(f"Title: {doc['title']}\nKind: {doc['kind']}\n\n{doc['text']}")
        manifest.append({"file": name, "title": doc["title"], "kind": doc["kind"]})
    (d / "docs" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    key = {"household": h.hid, "suite": "v2", "name": h.name, "email": h.email, "account": CHECKING, "today": TODAY.isoformat(),
           "opportunities": h.opps, "decoys": h.decoys,
           "total_value_cents": sum(o["value_cents"] for o in h.opps),
           "total_exposure_cents": sum(o["exposure_cents"] for o in h.opps)}
    (ROOT / "answer_keys").mkdir(parents=True, exist_ok=True)
    (ROOT / "answer_keys" / f"{h.hid}.json").write_text(json.dumps(key, indent=2) + "\n")
    return key


if __name__ == "__main__":
    total = 0
    for i in range(1, 13):
        k = write(build(i))
        total += k["total_value_cents"]
        print(k["household"], [o["kind"] for o in k["opportunities"]], "| decoys", [x["kind"] for x in k["decoys"]],
              f"${k['total_value_cents'] / 100:.2f}")
    print(f"total ${total / 100:.2f}")
