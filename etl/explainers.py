"""Mechanism explainers — why land is unreachable, not just which land.

Extent without mechanism reads as sad geography. A reader who sees that 13% of
East Jerusalem is zoned for Palestinian construction learns a statistic; a
reader who sees *how* the zoning, permit and demolition regime interlocks
learns a cause.

The rule that governs every other layer governs these: **every claim carries a
citation with the document's own date and the date we read it.** A sentence
without evidence is a bug, and `tests/test_invariants.py` fails the build for
one. Where a figure is widely repeated but we could not confirm it against a
source we can name, it goes in `unverified` and is displayed as an open
question rather than quietly dropped or quietly asserted — the `alleged` tier
from docs/from-report-to-evidence.md, applied to prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import Evidence

#: Read on this date. Explainer sources are pages rather than downloads, so
#: they have no fetch-manifest entry to take a retrieval date from.
READ_ON = "2026-08-21"

_OCHA_EJ = Evidence(
    source_id="ocha_opt",
    title="High numbers of demolitions: the ongoing threats of demolition for "
          "Palestinian residents of East Jerusalem",
    url="https://www.ochaopt.org/content/high-numbers-demolitions-ongoing-"
        "threats-demolition-palestinian-residents-east-jerusalem",
    document_date="2018-01-15",
    retrieved=READ_ON,
)


@dataclass
class Claim:
    text: str
    evidence: list[Evidence]
    quote: bool = False   # the wording is the source's own, not ours


@dataclass
class Explainer:
    id: str
    title: str
    question: str
    summary: str
    claims: list[Claim]
    #: Named instruments. A resolution or statute identifies itself, so these
    #: are citations in their own right and are not fetched.
    legal_basis: list[str] = field(default_factory=list)
    #: Oslo class or layer id this attaches to, so the UI can offer it in place.
    attaches_to: str | None = None
    #: Widely repeated figures we could not confirm against a nameable source.
    unverified: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "question": self.question,
            "summary": self.summary,
            "legal_basis": self.legal_basis,
            "attaches_to": self.attaches_to,
            "unverified": self.unverified,
            "claims": [
                {
                    "text": c.text,
                    "quote": c.quote,
                    "evidence": [e.to_dict() for e in c.evidence],
                }
                for c in self.claims
            ],
        }


EXPLAINERS: list[Explainer] = [
    Explainer(
        id="ej_permit_regime",
        title="The permit regime in East Jerusalem",
        question="Why can't Palestinians in East Jerusalem simply build homes?",
        summary=(
            "Building is not forbidden outright. It is made unobtainable by "
            "zoning, then punished by demolition — which produces the same "
            "result while remaining, on paper, a planning matter."
        ),
        attaches_to="Israeli Declared East Jerusalem",
        legal_basis=[
            "Basic Law: Jerusalem, Capital of Israel (1980) — Israel's "
            "unilateral annexation of East Jerusalem",
            "UN Security Council Resolution 478 (20 August 1980) — held the "
            "annexation null and void and called on states not to recognise it",
        ],
        claims=[
            Claim(
                "Only 13 per cent of East Jerusalem is zoned for Palestinian "
                "construction.",
                [_OCHA_EJ], quote=True,
            ),
            Claim(
                "The planning regime makes it virtually impossible for "
                "Palestinians to obtain the requisite Israeli building permits.",
                [_OCHA_EJ], quote=True,
            ),
            Claim(
                "At least a third of all Palestinian homes in East Jerusalem "
                "lack an Israeli-issued building permit.",
                [_OCHA_EJ], quote=True,
            ),
            Claim(
                "In 2017, 142 structures were demolished in East Jerusalem — "
                "142 of 423 demolitions across the whole West Bank — displacing "
                "233 people, including 133 children.",
                [_OCHA_EJ],
            ),
        ],
        unverified=[
            "That roughly 35% of East Jerusalem has been expropriated for "
            "Israeli settlements. Widely repeated, and it does not appear in "
            "the OCHA page cited above. Not stated here until it is sourced.",
            "That permits are granted in practice on about 1% of the area. "
            "Same position — repeated often, not found in a source we can name.",
            "B'Tselem's planning-policy analysis, which would corroborate or "
            "correct the above. Their site returned HTTP 429 when read on "
            + READ_ON + "; retry rather than assume.",
        ],
    ),
]


def build() -> list[dict[str, Any]]:
    return [e.to_dict() for e in EXPLAINERS]
