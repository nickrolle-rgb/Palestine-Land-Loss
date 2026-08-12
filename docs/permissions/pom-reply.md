# Draft reply — Palestine Open Maps

**Status:** not sent
**To:** admin@visualizingpalestine.org (cc data@visualizingpalestine.org)
**Subject:** Re: New submission from Contact Us

**Note before sending:** this is where the preview request gets answered
honestly. They asked to see the platform before publication; the site went live
before that happened. Say so plainly in the second paragraph rather than letting
them discover it.

---

Dear VP team,

Thank you — that's generous, and clearer than I'd hoped for. All three conditions
are in place, and I've built them so they can't quietly lapse:

- Historical tiles are attributed **"Survey of Palestine / Palestine Open Maps"**,
  the wording you suggested.
- The accuracy note is published alongside the data: that Palestine Open Maps do
  not guarantee it is 100% accurate, and that it is republished with permission
  together with its sources.
- All seven underlying sources are acknowledged — Palestine Remembered, the
  Institute for Palestine Studies, Palestine Lands Society, PCBS, Israeli CBS,
  Zochrot and B'Tselem.

The attribution isn't only in the interface; there's an automated test that fails
the build if the accuracy note or any of the seven credits stops being published.
It seemed better to make the conditions structural than to rely on my future
carefulness.

Thank you also for the OpenStreetMap clarification. That answered a question I
couldn't resolve from the outside, and it means no share-alike obligation flows
through to this project from the locality data.

**On seeing it before publication — I owe you a straight answer.** The site went
live before I'd sorted that out. It's here:

https://palestine-land-loss.vercel.app/

It is public but unannounced: no launch, nothing shared, no promotion anywhere.
I'd very much like your comments before it goes any further, and I'll hold off
mentioning it publicly until you've had a chance to look. If anything about how
your work appears is wrong or unwelcome, tell me and I'll change or remove it.

**Two things in your data you may want to look at.** Both are handled here by
withholding rather than guessing, but they're probably worth a fix upstream:

1. **al-Zaytouneh** carries the exact coordinates of **Abu Shukheidim**
   (35.17215, 31.96491) — while your own Abu Shukheidim record sits about 200 m
   away. Two villages, one position between them.
2. **Aqada** and **al-Bayada** (ids 11770 and 11772) share identical coordinates.
   Adjacent ids, so it looks like a copied row.

Sixteen records in total are withheld from the map for this reason — sitting on
the exact coordinates of a differently-named locality — rather than being drawn
somewhere I can't stand behind. Most of the remainder are Bedouin communities
recorded at a neighbouring village's position, which may be deliberate on your
part rather than an error.

**One thing your data does better than the alternative.** Where your coordinate
and OCHA's differ, yours is the 1945 village and OCHA's the present-day
administrative centre. At Beituniya they're 1,175 m apart. The map now keeps both
and switches to yours whenever a historical survey is showing, so places sit
where they belong on your sheets instead of drifting off them.

**And your `raw-data/poha` index turned out to be a find.** It let me link 726
Palestinian Oral History Archive interviews across 133 villages to the localities
they belong to — joined on your slug, so it's exact rather than name-matched.
Metadata and links only, given the CC BY-NC-ND terms; the recordings stay with
AUB.

Thanks again. The map wouldn't have a "before" without your work.

Cheers,

Nick Olle
0433321011
Nick.r.olle@gmail.com
