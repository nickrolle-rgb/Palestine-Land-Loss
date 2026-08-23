# Gaza Maps / Databases for Palestine — request for API access

**Status:** source **enabled** and in use as at 2026-08-23. The note below is a
courtesy, not a permission request — their API documentation is public and
states its own terms.

**The basis.** `gazamaps.com/api-docs` says plainly: *"Our API endpoint is a GET
request and returns json. No authentication is required."* It opens with *"Thank
you for considering building with our API. Our mission is to facilitate memory
and accountability, and we hope our API helps you, as you work towards the same
goals."* and closes by inviting people to ask for custom endpoints. That is a
published invitation to build, which is a different thing from an absent licence.

I earlier recorded this API as returning 403 and therefore access-controlled.
That was wrong: the 403 was on the bare `/api/` path, not the documented
`/api/v1/displacement` endpoint, which returns 200 without authentication.

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

Subject: Using your displacement-orders API — Palestinian Land Loss

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

We are now using `/api/v1/displacement` on the basis of your published
documentation, and I wanted to tell you rather than simply take it. All 154
orders are carried with attribution to Gaza Maps and Databases for Palestine, a
link back to your page for each, and the retrieval date. We do not present your
work as an official demarcation, and we will remove or correct anything on
request.

One thing we deliberately do **not** do: total the order areas. They sum to
about 3,056 km² against a Strip of roughly 365, because orders overlap and are
reissued, and the map says so where the figures appear. If that framing is not
how you would put it, I would welcome the correction.

If the Yellow Blocks positions are ever available through the API, we would
carry those too.

One thing I would want to represent correctly if we carry it: BBC Verify found
the physical blocks sitting up to 520 metres from the line on the IDF's own map.
If your data distinguishes the two, that distinction matters more than either
line alone, and I would want to show it rather than flatten it.

Happy to answer anything about how the map handles sourcing.

With thanks and solidarity,

Nick Olle
0433321011
Nick.r.olle@gmail.com
