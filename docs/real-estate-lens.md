# real-estate lens: what a realtor.com-class team gets from re:Invent 2026

a product-owner point of view, not a survey. the question driving this doc:
if you run a large residential real-estate marketplace or a proptech
platform, which re:Invent 2026 sessions move your roadmap, and why. grounded
in a 2025-2026 landscape scan (sources at the end).

## the setup: where the industry actually is

the marketplaces already ship AI in production. this is not a greenfield
pitch, it is a catch-up-or-lead posture.

- zillow runs a neural Zestimate over 100M+ homes, reacts to market moves
  multiple times a week, and processes 3M+ listing images a day on AWS
  (keyspaces, s3, cloudfront). confidence: high
- realtor.com launched RealAssist AI (jun 2026) on google cloud / gemini,
  not aws. redfin shipped conversational search (nov 2025) with a reported
  47% lift in tour requests. zillow shipped an AI mode (mar 2026).
  confidence: high
- offerup improved local results 54% and relevance recall 27% with
  multimodal search on Amazon Bedrock + OpenSearch. this is the clearest
  aws-native marketplace-search proof point. confidence: high
- corelogic/cotality runs araya/CoreAI over 155M properties, 4.5B records.
  confidence: high

the hard problems that map cleanly to cloud+AI: listing data quality and
MLS normalization, duplicate and fraudulent listings (FTC: 65k rental scams,
$65M losses 2020-mid-2025), computer-vision at millions of images a day,
geospatial/location intelligence, document processing for leases and
disclosures, and multimodal intake from non-technical users (the LockHouse
voice-studio idea).

## my POV: the four moves that matter

1. retrieval and knowledge layer is the real battleground. every marketplace
   is converging on the same shape: a governed semantic layer (embeddings +
   knowledge graph + memory) that every agent reads from. the differentiator
   is not the model, it is the property/listing knowledge layer underneath.

2. computer vision is quiet infrastructure now, not a feature. condition
   scoring from photos, room detection, virtual staging at $29/room vs
   thousands for physical. the team that industrializes CV over the image
   firehose wins listing quality.

3. fraud and listing integrity is an unglamorous moat. duplicate/relist
   detection, network-layer identity, multimodal fake-ad detection (91.5%
   accuracy in research). this is where trust compounds.

4. telemetry becomes a valuation signal. smart-home IoT (Chamberlain myQ at
   15M devices, Daikin HVAC) turns a property into a data stream. the
   LockHouse "utility truth scorecard" is the consumer-facing version of a
   pattern the big builders are already industrializing.

## catalog map: sessions to the four moves

| move                        | sessions in catalog                          | why it lands                                             |
| --------------------------- | -------------------------------------------- | -------------------------------------------------------- |
| retrieval / knowledge layer | IND367-R/R1, ANT423, DAT413-R, DAT318-S      | semantic layer, AWS Context governed graph, Neptune+MCP, gpu vector build at billion scale |
| computer vision             | (watch-list gap, see below)                  | no strong CV-for-listings session captured yet           |
| fraud / integrity           | NET334-R                                     | agent-crawler identity, WAF bot control, rate + monetize |
| telemetry / valuation       | IND344                                        | Chamberlain/Daikin connected-product telemetry at scale  |
| production proof / journey  | AIM247-S, IND329-R1, NET319-R                | Lennar 80k-homes Bedrock in prod; home-buying multi-agent journey; edge personalization |

## the shortlist i would actually walk into

ranked by signal for a marketplace/proptech platform team:

- AIM247-S (Lennar, Bedrock + Coralogix, 80k home deliveries) — the only
  end-to-end production homebuilder AI story in the set. land acquisition to
  sale, with cost/adoption observability. Wed Dec 2, 4:30 PM, Venetian.
- IND329-R1 (multi-agent hyper-personalized journeys) — home-buying is the
  worked example; AgentCore + Strands + MCP; shared memory and coordinated
  decisioning. hands-on workshop, laptop required. Mon Nov 30, 8:30 AM,
  Wynn/Encore.
- IND367-R / R1 (semantic intelligence layer for agents) — the knowledge-
  layer pattern that becomes a property/listing graph. two slots: Mon Nov 30
  11:30 AM and Tue Dec 1 3:00 PM, Caesars Forum.
- DAT318-S (NVIDIA cuVS gpu vector acceleration) — listing/property vector
  search at marketplace scale, 10x faster index builds at a quarter cost.
  Mon Nov 30, 3:00 PM, Caesars Palace.
- IND344 (Chamberlain + Daikin smart-product telemetry) — property-as-data-
  stream, valuation and truth signal. Fri Dec 4, 9:00 AM, Wynn/Encore.
- AIM216 (Textract intelligent document processing) — leases, disclosures,
  appraisals. Wed Dec 2, 4:00 PM, MGM Grand.
- NET334-R (identify/rate-limit/monetize AI crawlers) — how a listings site
  treats the new agent-visitor traffic. Thu Dec 3, 10:30 AM, MGM Grand.

## watch-list gaps to fill as more sessions come in

- computer vision for listings: room detection, condition scoring, photo
  quality, virtual staging. nothing strong captured yet — feed me a CV /
  Rekognition / image-understanding session and it slots straight into the
  cv move above.
- geospatial / Amazon Location Service: location intelligence for
  neighborhood scoring, commute, flood/utility overlays.
- fraud detection deep-dive beyond crawler traffic: duplicate-listing and
  synthetic-identity detection.

## honest note on the aws angle

realtor.com's own flagship AI (RealAssist) runs on google cloud, and
homes.com/costar uses azure openai. the aws-native marketplace proof points
are offerup (search) and the builder/manufacturer side (Lennar, Chamberlain).
so the pitch to a realtor.com-class team is not "aws already runs your AI" —
it is "here is the aws pattern set for the four moves, and here are the peers
already proving it in production." that framing is more honest and more
useful than pretending the incumbents are all aws shops.

## sources

- zillow neural zestimate: https://www.zillow.com/tech/building-the-neural-zestimate/
- zillow image processing on aws: https://www.zillow.com/tech/image-processing-in-aws/
- zillow knowledge graphs: https://www.zillow.com/tech/leveraging-knowledge-graphs-in-real-estate-search/
- realtor.com RealAssist (google cloud): https://mediaroom.realtor.com/2026-06-02-Realtor-com-R-Launches-RealAssist-TM-AI-A-Completely-Reimagined-Way-to-Find-A-Home
- offerup bedrock + opensearch multimodal: https://aws.amazon.com/blogs/machine-learning/offerup-improved-local-results-by-54-and-relevance-recall-by-27-with-multimodal-search-on-amazon-bedrock-and-amazon-opensearch-service/
- corelogic/cotality CoreAI: https://www.corelogic.com/product-articles/better-data-lifecycle-coreai/
- ftc rental fraud: https://www.realestatenews.com/2026/08/03/fraudsters-finding-new-ways-to-evade-rental-listing-safety-checks
- mckinsey agentic ai in real estate: https://www.mckinsey.com/industries/real-estate/our-insights/how-agentic-ai-can-reshape-real-estates-operating-model
- nvidia cuvs on aws: https://blogs.nvidia.com/blog/2026/06/23/nvidia-aws-ai-production/

research methodology and confidence levels: docs/research/real-estate-ai-brief.md
