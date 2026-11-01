"""Deterministic synthetic customer-feedback corpus for a fictional mobile banking app.

Records are generated from 12 latent themes with a skewed frequency distribution and varied wording,
so that the "true" theme of every record is known (used only for sanity checks, never shown to the
model). The paper used real customer feedback of 100-5,000 records; this stands in for it."""
from __future__ import annotations

import json
import random

THEMES = [
    ("login_failures", 0.17, [
        "I can't log in since the update, it keeps saying my password is wrong even though it isn't.",
        "Login loops back to the start screen every time. Two days now without access to my account.",
        "Face ID stopped working for sign-in and the fallback PIN is rejected.",
        "App logs me out every few minutes and makes me sign in again with the SMS code.",
        "The verification code never arrives so I cannot get past the login screen.",
    ]),
    ("app_crashes", 0.14, [
        "The app crashes as soon as I open the transfers tab.",
        "Constant crashes on Android 15 after the latest version, unusable.",
        "It freezes on the loading spinner and then closes itself.",
        "Crashed three times while I was trying to pay a bill.",
        "Since yesterday the app closes immediately after the splash screen.",
    ]),
    ("transfer_delays", 0.12, [
        "My transfer to another bank has been pending for four days with no explanation.",
        "Instant transfer took 9 hours. Not instant.",
        "Sent money on Friday, it still shows as processing on Monday.",
        "Scheduled payment went out two days late and I got a late fee from my landlord.",
        "Transfers between my own accounts take ages to reflect in the balance.",
    ]),
    ("fees_and_charges", 0.10, [
        "I was charged a foreign transaction fee on a purchase in my own currency.",
        "Monthly fee appeared out of nowhere, nobody told me about a pricing change.",
        "Why is there a fee for withdrawing cash at your own ATM?",
        "Hidden charges on international transfers, the quoted amount was not what was taken.",
        "Got charged twice for the same card payment and the fee is not refunded.",
    ]),
    ("customer_support", 0.10, [
        "Waited 45 minutes in chat and then the agent disconnected.",
        "Support keeps sending canned replies that do not address my question.",
        "No phone number anywhere, only a bot that cannot understand my issue.",
        "Opened a ticket two weeks ago, still no human response.",
        "The agent was polite but could not do anything and told me to wait.",
    ]),
    ("notifications", 0.08, [
        "Push notifications for payments arrive hours late or not at all.",
        "I get a notification for every tiny thing but not for the large withdrawal I did not make.",
        "Notifications cannot be turned off for marketing, only for transactions. Backwards.",
        "Balance alerts stopped working after I changed my phone.",
        "Duplicate notifications for a single transaction, three or four each time.",
    ]),
    ("ui_navigation", 0.07, [
        "The new layout hides the statements menu three levels deep.",
        "Buttons are too small and the font is grey on grey, hard to read.",
        "Why did you move the pay button? Took me ten minutes to find it.",
        "Dark mode is half implemented, some screens are blinding white.",
        "Too many taps to do a simple transfer compared to the old version.",
    ]),
    ("card_issues", 0.06, [
        "My new card arrived but activation in the app fails with an unknown error.",
        "Card got declined abroad even though I set the travel notice.",
        "Virtual card number changes every time I open it, merchants reject it.",
        "Lost card freeze did not work, a payment went through after I froze it.",
        "Apple Pay removal happened by itself and I cannot re-add the card.",
    ]),
    ("statements_export", 0.05, [
        "PDF statements are missing the last week of the month.",
        "CSV export has the wrong date format and my accounting software rejects it.",
        "Cannot download statements older than six months anymore.",
        "The statement does not show merchant names, just codes.",
        "Export button does nothing on iPad.",
    ]),
    ("security_concerns", 0.04, [
        "I got a text asking for my PIN that looked like it came from you. Is this phishing?",
        "A device I do not recognise is listed under trusted devices and I cannot remove it.",
        "Two-factor can be disabled without any confirmation, that seems unsafe.",
        "The app shows my full card number on the home screen without asking.",
        "Session stays open on a shared tablet even after closing the app.",
    ]),
    ("positive_feedback", 0.04, [
        "Love the new budgeting view, finally I can see where my money goes.",
        "Fast and simple, the best banking app I have used.",
        "Great job on the savings pots feature, very handy.",
        "Support solved my issue in five minutes, thank you.",
        "The spending insights are genuinely useful.",
    ]),
    ("feature_requests", 0.03, [
        "Please add the ability to split a bill with friends in the app.",
        "It would be great to have joint accounts.",
        "Can you add a widget for the balance on the home screen?",
        "Recurring transfers should allow custom intervals like every 3 weeks.",
        "Would love multi-currency accounts.",
    ]),
]
PREFIXES = ["", "", "", "Honestly, ", "Update: ", "Second time writing about this. ", "Not happy. ", "Quick note: ", "FYI ", "As a long-time customer, "]
SUFFIXES = ["", "", "", " Please fix.", " Very frustrating.", " Anyone else?", " Fix this.", " Thanks.", " Rating 1 star until resolved.", " Using the latest version."]


def generate(n: int, seed: int = 0) -> list[dict]:
    rnd = random.Random(seed)
    names = [t[0] for t in THEMES]
    weights = [t[1] for t in THEMES]
    out = []
    for i in range(n):
        name = rnd.choices(names, weights=weights)[0]
        templates = next(t[2] for t in THEMES if t[0] == name)
        text = rnd.choice(PREFIXES) + rnd.choice(templates) + rnd.choice(SUFFIXES)
        out.append({"id": i + 1, "text": text.strip(), "_theme": name})
    return out


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    recs = generate(n)
    from collections import Counter
    print(json.dumps(Counter(r["_theme"] for r in recs).most_common(), indent=0))
