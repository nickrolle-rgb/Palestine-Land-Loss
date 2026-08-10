# Naming policy

Every locality potentially has an Arabic name, a Hebrew name, a pre-1948 name
and an OCHA transliteration. Silently picking one scheme is the fastest way to
make the map look partisan regardless of how good the underlying data is.

## The policy

1. **Show the Palestinian/Arabic name and the current official name together**
   where both are known. The map label renders the transliteration with the
   Arabic beneath it.
2. **List every known variant** in the feature detail panel — Arabic, Hebrew,
   pre-1948, and alternative transliterations.
3. **Never silently normalise.** If a source spells it `Al 'Isawiya`, that
   spelling is preserved as the primary name from that source. Normalisation
   happens only inside the matcher (`etl/adapters/alhaq.py:normalise`), never in
   stored data.
4. **State the policy in the UI**, not just in the repository. It appears in the
   About panel.

## Implementation

`schema.Names` carries `primary`, `arabic`, `hebrew`, `pre_1948` and
`transliterations`. Only `primary` is required.

Current coverage is partial: OCHA's communities layer supplies Arabic names for
most localities but not all (several East Jerusalem entries have an empty
`NAME_ARB`). Settlement names come through in Latin transliteration only, with
no Hebrew or pre-1948 name attached — a gap, not a choice.

## Matching is lossy on purpose

The Al-Haq geocoder folds transliteration variance so that `Al-'Isawiya`,
`Isawiya` and `al Isawiyya` all collide. That fold is deliberately aggressive:
it strips the Arabic definite article in its assimilated forms (`al-`, `as-`,
`ash-`, `ad-`, `ar-`, `an-`…), removes diacritics and apostrophes, and collapses
doubled letters.

Aggressive folding produces false positives, which is why ambiguity is resolved
by **rejecting the record**, never by picking the most likely candidate. A
record matching two localities is withheld from the map and recorded as
`ambiguous`.

Names shorter than 5 normalised characters are excluded from the index entirely,
along with a stoplist (`gaza`, `jerusalem`, `west bank`…), because short generic
tokens match inside unrelated sentences.
