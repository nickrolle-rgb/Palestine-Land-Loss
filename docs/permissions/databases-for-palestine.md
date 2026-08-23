# Gaza Maps / Databases for Palestine — request for API access

**Status:** drafted 2026-08-23, not sent. Source registered **disabled**.

## Why this one and not the other

Gaza Maps is a project of **Databases for Palestine**. Their published
methodology says they reconstruct the IDF's own "Swords of Iron" displacement
orders, compute the area of each population block in WGS84, and update the same
day an order is issued. They are explicit about what they are *not* doing —
mapping conditions on the ground — and about why their designated kill zone is
smaller than the UN's.

That is a derivation from a primary record with the method published. It is the
opposite of an aggregator, and it is the difference between this and the
alternatives considered: liveuamap sells the data and interprets it, and INSS is
a source we have deliberately chosen not to approach.

`gazamaps.com/api/` exists and returns 403, so access is a request rather than a
scrape.

## Draft

Subject: API access — Gaza Maps displacement orders and Yellow Blocks

Dear Databases for Palestine,

I maintain *Palestinian Land Loss* (https://palestine-land-loss.vercel.app), a
free, non-commercial, openly published evidence map. Every element on it resolves
to a dated document, unplaceable records are withheld and counted rather than
guessed at, and nothing is drawn that cannot be sourced. It already carries OCHA
base geography, B'Tselem settlement data, Palestine Open Maps historical sheets,
UNOSAT's Gaza damage assessment and Al-Haq's records, each under recorded terms.

Access restriction inside Gaza is the gap we have been unable to close. OCHA
describe the Yellow Line but publish no geometry; a search of all 254
Palestine-tagged datasets on the Humanitarian Data Exchange found none. We have
therefore documented the restriction in words and refused to draw a line, because
drawing one by eye would be exactly the guesswork the project exists to avoid.

Your methodology page is the clearest statement of derivation I have found
anywhere on this subject — reconstructing the IDF's own orders, stating the
projection, and saying plainly what you are not claiming. I would rather carry
your work with attribution than approximate it.

Would you consider granting access to `gazamaps.com/api/` for this use? I am
interested in the designated kill zone / displacement order geometry and the
Yellow Blocks positions. In return I can commit to attribution and a link on
every feature, publication of the document date and our retrieval date, removal
or correction on request, and never presenting your depiction as an official
demarcation.

One thing I would want to represent correctly if we carry it: BBC Verify found
the physical blocks sitting up to 520 metres from the line on the IDF's own map.
If your data distinguishes the two, that distinction matters more than either
line alone, and I would want to show it rather than flatten it.

Happy to answer anything about how the map handles sourcing.

With thanks and solidarity,

Nick Olle
0433321011
Nick.r.olle@gmail.com
