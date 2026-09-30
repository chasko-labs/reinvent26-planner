# ai/cloud innovation in residential real estate: 2025-2026 brief

research backing docs/real-estate-lens.md. findings first, methodology
second, confidence per non-obvious claim, source urls required.
gathered by ghost-kerouac-research-analyst.

## production ai/ml at major marketplaces

automated valuation models (avm):

| company            | system             | confidence | notes                                                            |
| ------------------ | ------------------ | ---------- | ---------------------------------------------------------------- |
| zillow             | neural zestimate   | high       | 100M+ US homes, deep learning since 2021, ~1.74% median error on active listings |
| redfin             | asking price model | medium     | powers redfin estimate, conversational assistant integration     |
| corelogic/cotality | araya / CoreAI     | high       | 155M properties, 4.5B records                                    |
| housecanary        | avm                | medium     | 2.8% median error across 136M properties, 1,000+ data points/home |

computer vision listing enrichment:

- per-room detection/classification: room type, condition category, score,
  materials, visible issues. medium confidence
- condition scoring from photos improves predictive performance comparable
  to human labels; stronger for kitchens/bathrooms and lower-priced homes.
  medium confidence
- zillow processes 3M+ images daily on aws. high confidence
- vc-backed cv players: matterport, openspace, cape analytics, snappt,
  surfaceai. medium confidence

conversational search / assistants:

| company     | feature               | launch    | confidence | note                                  |
| ----------- | --------------------- | --------- | ---------- | ------------------------------------- |
| redfin      | ask redfin            | nov 2024  | high       |                                       |
| redfin      | conversational search | nov 2025  | high       | reported 47% lift in tour requests    |
| zillow      | ai mode               | mar 2026  | high       |                                       |
| realtor.com | realassist ai         | jun 2026  | high       | google cloud / gemini powered         |
| rightmove   | ai search             | 2025      | high       | google cloud / gemini                 |

generative listing content:

- 2026: 45%+ of active agents use at least one AI marketing tool (nar survey). medium
- virtual staging ~$29/room vs $2,000-5,000/property physical. medium

## hard problems mapping to cloud+ai

- listing data quality / MLS normalization: different formats, refresh
  schedules, cascade across search/cache/media. one audit found ~30% of
  records behaving like duplicate relists. medium
- duplicate/fraudulent listings: ftc 65,000 rental scams 2020-mid-2025,
  $65M losses, likely underreported. multimodal fake-ad detection ~91.5%
  accuracy in research. high on ftc figure, medium on detection accuracy
- geospatial/location intelligence: smart-meter + iot indoor signals improve
  energy analytics; map-based recommenders combine content, collaborative,
  location signals. medium
- document processing: textract for leases, disclosures, appraisals;
  unresolved multi-format, state-level disclosure variance. high on textract
  capability, medium on the unsolved gap

## emerging patterns 2025-2026

- agentic workflows: mckinsey frames agentic ai automating multistep
  workflows in core systems; realchat/lofty mcp servers (2026); 87% of
  brokerages/agents reported using AI tools (delta media 2026). medium
- mcp: introduced anthropic nov 2024, openai mar 2025, google apr 2025;
  10,000+ public servers by 2026; donated to linux foundation dec 2025;
  real-estate-mcp projects exist. high on adoption trend, medium on counts
- knowledge graph + retrieval: zillow knowledge graphs; graphrag combining
  vector search with graph relationship context. medium
- iot/telemetry: smart-home iot market $162.8B 2025 -> $887.4B 2033
  (projection); energy, security, predictive maintenance, dispute
  resolution via sensor data. low-medium on the projection, medium on uses

## aws-specific usage evidence

| company            | service                                    | confidence |
| ------------------ | ------------------------------------------ | ---------- |
| zillow             | keyspaces, s3, cloudfront, ec2; 100TB, 300M images | high |
| offerup            | bedrock + opensearch multimodal search     | high       |
| homes.com (costar) | azure openai (NOT aws)                     | high       |
| realtor.com        | google cloud (NOT aws) for realassist      | high       |

relevant aws building blocks: bedrock knowledge bases + opensearch vector
storage (mar 2025), neptune analytics (graph + vector in one query),
textract (documents), location service (geospatial).

## methodology

remote web search across each focus area, direct fetch of primary sources
(zillow tech blog, realtor.com press, mckinsey, aws case studies),
arxiv/academic for cv/imaging. confidence assessed: production deployment
evidence > announced partnerships > analyst coverage > hype. all sources
publicly accessible as of the research date (late 2026).
