# real-estate angle

the realtor.com lens. reading the LockHouse hackathon entry (direct
landlord rental intelligence, nigeria) got me thinking about how a big
listings-marketplace team benefits from re:Invent.

LockHouse's moves, worth stealing at scale:

- voice studio: older landlords speak naturally, bedrock extracts
  structured listing metadata. zero-form intake for non-technical users.
- utility truth scorecard: guaranteed transparency on power hours, solar
  backup, prepaid metering, water. this is property-as-data-stream.
- computer vision hardware audit: inspect uploaded photos, detect physical
  hardware (meters, inverters, gates). condition scoring by another name.
- statutory agreement generator with sha-256 verification hash. document
  processing plus trust.
- cloudfront edge with a lagos POP for sub-100ms west african response.
  low-latency global browsing.

the four moves i keep coming back to:

1. retrieval / knowledge layer is the battleground, not the model
2. computer vision is quiet infrastructure now
3. fraud and listing integrity is an unglamorous moat
4. telemetry becomes a valuation signal

production peers already proving aws patterns: offerup (bedrock + opensearch
multimodal search), lennar (80k homes on bedrock, AIM247-S), chamberlain
myQ + daikin (smart-home telemetry, IND344). honest catch: realtor.com's
own realassist runs on google cloud/gemini, homes.com on azure openai. so
the pitch is peer-proof patterns, not "aws already runs your stack".

top sessions to walk into: AIM247-S, IND329-R1, IND367-R, DAT318-S,
IND344, AIM216, NET334-R.

open gap: still want a strong computer-vision-for-listings session and an
Amazon Location Service geospatial session. feed those when i find them.
