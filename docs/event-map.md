# re:invent 2026 event map

coordination page for the hackathon team. built from the live events api catalog, pulled at build time. regenerate by re-pulling the catalog; session times and rooms move until the event

## ground rules

- home base: venetian
- strip cluster: venetian, wynn/encore, caesars palace, caesars forum. 30 minutes between venues inside the cluster
- assumption: caesars forum treated as part of the cluster (behind the linq, walkable from caesars palace). flag if that is wrong
- mgm grand sits at the south end of the strip. planner wants 60+ minutes to cross between mgm and the cluster, so mgm sessions group into mgm blocks
- priority: reserved seats wall to wall. reservable sessions weigh 2x walk-ups, title matches weigh 1.4x abstract-only matches, favorites 1.5x, 300/400 level 1.1x
- amazon bedrock out except nova; frontier and proprietary third-party model sessions out; open weight and open source models preferred and tracked as the topic "open-weight models"
- repeats (-R, -R1) scheduled once, on whichever day fits the plan best
- reservations: seating opened 6 oct and full reserve/cancel write access 8 oct per the hackathon page. verify with a live reserve call before relying on it
- times as listed in the catalog (las vegas local)

## venue map

```
north
  wynn / encore
      |   ~10-15 min walk
  venetian / palazzo  (home base)
      |   ~10-15 min walk
  caesars forum (behind the linq)
      |   ~10 min walk
  caesars palace
      |
      |   ~2 miles, monorail / shuttle / rideshare: 30-45 min door to door
      |
  mgm grand
south
```

walk times are rough planning numbers, not measured. the official re:invent shuttle map will be authoritative once published

## topics tracked

self-managed agents, amazon braket, databricks, lambda microvms + web functions, video games, amazon leo, nvidia, nfl / sports, amazon nova, netflix, amazon.com / amazon retail, open-weight models

## build order

- step 1: pin every amazon leo session as an anchor (marked ANCHOR in the seat column), plus bryan-approved pins
- step 2: fill open time around the anchors, ranked by topic weight

## anchors

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NET337 | mon 11-30 | 15:00-16:00 | MGM Grand | Chalk talk | 300 | ANCHOR, reserve | amazon leo | Extending your cloud network with Amazon Leo satellite connectivity |
| NET335 | mon 11-30 | 16:00-17:00 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | nfl / sports | Building searchable live sports with AWS Elemental and Amazon CloudFront |
| IND105-S | tue 12-01 | 10:30-10:50 | Venetian | Lightning talk | 100 | ANCHOR, walk-up | amazon leo | Amazon Leo: Connectivity Beyond the Reach of Existing Networks (sponsored by Amazon Leo) |
| CMP308 | tue 12-01 | 16:00-17:00 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | (amazon leo), (amazon.com / amazon retail) | Modernizing HPC on AWS: Migration at scale with PCS |
| IND3351 | wed 12-02 | 08:30-09:30 | Caesars Forum | Breakout session | 300 | ANCHOR, walk-up | amazon leo | AT&T Expands Connectivity with AWS Interconnect and Amazon Leo |
| NET341 | wed 12-02 | 15:30-15:50 | Venetian | Lightning talk | 300 | ANCHOR, walk-up | amazon leo, (amazon.com / amazon retail) | Building hybrid satellite and cloud networks with Amazon Leo |
| ARC322 | thu 12-03 | 10:30-11:30 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | amazon leo | Resilience patterns for the disconnected edge with Amazon Leo |


## schedule

### mon 11-30

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AIM401-R | mon 11-30 | 08:30-09:30 | MGM Grand | Builders' session | 400 | reserve | (self-managed agents), (video games) | Agents that train themselves: autonomous reinforcement learning on AWS |
| AIM346-R | mon 11-30 | 10:00-11:00 | MGM Grand | Chalk talk | 300 | reserve | self-managed agents, (nvidia), (open-weight models) | Deploy, scale, and tune AI model serving with self-managed agents |
| CMP328-R | mon 11-30 | 12:00-13:00 | MGM Grand | Chalk talk | 300 | reserve | self-managed agents | Deploy AI agent sandboxes on EC2 |
| AIM312-R | mon 11-30 | 13:00-14:00 | MGM Grand | Chalk talk | 300 | reserve | open-weight models | Beyond fine-tuning: RL for reasoning agents with AWS Trainium |
| NET337 | mon 11-30 | 15:00-16:00 | MGM Grand | Chalk talk | 300 | ANCHOR, reserve | amazon leo | Extending your cloud network with Amazon Leo satellite connectivity |
| NET335 | mon 11-30 | 16:00-17:00 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | nfl / sports | Building searchable live sports with AWS Elemental and Amazon CloudFront |
| COM344 | mon 11-30 | 18:00-18:20 | Venetian | Lightning talk | 300 | walk-up | (video games) | Now serverless has servers. What now? |

### tue 12-01

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IND105-S | tue 12-01 | 10:30-10:50 | Venetian | Lightning talk | 100 | ANCHOR, walk-up | amazon leo | Amazon Leo: Connectivity Beyond the Reach of Existing Networks (sponsored by Amazon Leo) |
| BIZ111-S | tue 12-01 | 11:00-11:20 | Venetian | Lightning talk | 100 | walk-up | (video games) | Build the Agentic Workplace: What's New on the Slack Developer Platform (sponsored by Salesforce) | frontier abstract |
| HMC403-R1 | tue 12-01 | 12:30-14:30 | MGM Grand | Workshop | 400 | reserve | self-managed agents | Self-managed agentic AI at the hybrid edge |
| OPN406-R1 | tue 12-01 | 14:30-15:30 | MGM Grand | Code talk | 400 | reserve | self-managed agents | Cut token costs by 50%: Building context efficient agents with Strands |
| CMP308 | tue 12-01 | 16:00-17:00 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | (amazon leo), (amazon.com / amazon retail) | Modernizing HPC on AWS: Migration at scale with PCS |

### wed 12-02

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IND3351 | wed 12-02 | 08:30-09:30 | Caesars Forum | Breakout session | 300 | ANCHOR, walk-up | amazon leo | AT&T Expands Connectivity with AWS Interconnect and Amazon Leo |
| IND304 | wed 12-02 | 10:00-11:00 | Caesars Forum | Breakout session | 300 | walk-up | netflix | How Netflix auto-selects the right storage for every ML training workload |
| CMP349 | wed 12-02 | 12:00-13:00 | MGM Grand | Chalk talk | 300 | reserve | amazon braket | Your next Quantum developer might be an AI agent | frontier abstract |
| AIM407-R1 | wed 12-02 | 13:30-14:30 | MGM Grand | Builders' session | 400 | reserve | self-managed agents | Build a production multi-Agent Systems with Strands |
| NET341 | wed 12-02 | 15:30-15:50 | Venetian | Lightning talk | 300 | ANCHOR, walk-up | amazon leo, (amazon.com / amazon retail) | Building hybrid satellite and cloud networks with Amazon Leo |
| AIM393 | wed 12-02 | 17:30-17:50 | Venetian | Lightning talk | 300 | walk-up | open-weight models | Open weights to production: How Salesforce built and served Koa models |

### thu 12-03

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AIM402 | thu 12-03 | 08:00-10:00 | MGM Grand | Workshop | 400 | reserve | open-weight models | From dataset to a deployed fine-tuned LLM in hours on SageMaker AI |
| ARC322 | thu 12-03 | 10:30-11:30 | MGM Grand | Breakout session | 300 | ANCHOR, walk-up | amazon leo | Resilience patterns for the disconnected edge with Amazon Leo |
| AIM405 | thu 12-03 | 11:30-12:30 | MGM Grand | Chalk talk | 400 | reserve | open-weight models | Build agents on OSS models with blazing fast inference on SageMaker AI | frontier abstract |
| CMP321-R1 | thu 12-03 | 13:00-14:00 | MGM Grand | Workshop | 300 | reserve | open-weight models | Build an agentic AI system on Amazon EKS with CPU-only inference |
| OPN312 | thu 12-03 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | open-weight models | Hugging Face on AWS: AI Model Deployment at Scale |
| SVS332-R | thu 12-03 | 16:00-17:00 | Caesars Forum | Chalk talk | 300 | reserve | lambda microvms + web functions | Lambda Managed Instances: Always-on Serverless Compute |

### fri 12-04

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CMP318-R1 | fri 12-04 | 08:00-10:00 | Wynn/Encore | Workshop | 300 | reserve | self-managed agents | Build your iOS CI/CD pipeline with AI agents on EC2 Mac |
| CMP348-R1 | fri 12-04 | 11:30-12:30 | Wynn/Encore | Chalk talk | 300 | reserve | amazon braket | Building better quantum computers with digital twins |

totals: 26 sessions, 19h00 reserved-seat time, 6h40 walk-up time

## would love to attend but not conducive to logistics

every topic session that did not fit, so teammates can see the interest and cover it or flag a swap

### self-managed agents

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZ202-R | mon 11-30 | 08:30-10:30 | Caesars Forum | Workshop | 200 | reserve | (self-managed agents) | Turn a Bee wearable into your re:Invent notetaking companion |
| OPN408 | mon 11-30 | 10:00-11:00 | Wynn/Encore | Code talk | 400 | reserve | (self-managed agents) | Connect agents across frameworks live using the A2A open protocol |
| OPN406-R | mon 11-30 | 10:30-11:30 | Caesars Forum | Code talk | 400 | reserve | self-managed agents | Cut token costs by 50%: Building context efficient agents with Strands |
| AIM407-R | mon 11-30 | 12:00-13:00 | MGM Grand | Builders' session | 400 | reserve | self-managed agents | Build a production multi-Agent Systems with Strands |
| AIM449 | mon 11-30 | 12:00-13:00 | MGM Grand | Chalk talk | 400 | reserve | self-managed agents | One agent, any robot: building physical AI with Strands Robots |
| SEC427 | mon 11-30 | 12:00-13:00 | Wynn/Encore | Code talk | 400 | reserve | (self-managed agents) | Threat modeling the agentic SDLC: from user story to deployment |
| AMZ202-R1 | mon 11-30 | 12:30-14:30 | Caesars Forum | Workshop | 200 | reserve | (self-managed agents) | Turn a Bee wearable into your re:Invent notetaking companion |
| CON338 | mon 11-30 | 15:00-16:00 | MGM Grand | Code talk | 300 | reserve | (self-managed agents) | The golden path for agentic workloads: safe by default on Amazon EKS |
| OPN401-R | tue 12-01 | 11:30-12:30 | Caesars Forum | Builders' session | 400 | reserve | (self-managed agents) | Powertools for agent DevOps: Debug reasoning, not just exceptions |
| CON402-R | tue 12-01 | 13:00-14:00 | Caesars Forum | Chalk talk | 400 | reserve | (self-managed agents), (amazon.com / amazon retail) | Amazon EKS: Infrastructure as code, GitOps, or CI/CD |
| AIM2208-S | tue 12-01 | 13:00-13:20 | Venetian | Lightning talk | 200 | walk-up | (self-managed agents) | AI Governance: The Framework, The Pitfalls, The Playbook (sponsored by Vanta) |
| IND406-R1 | tue 12-01 | 16:00-17:00 | Caesars Forum | Chalk talk | 400 | reserve | (self-managed agents), (amazon nova) | The agentic restaurant: AI agents that run your kitchen |
| AIM3301 | tue 12-01 | 16:30-17:30 | MGM Grand | Breakout session | 300 | walk-up | (self-managed agents), (nvidia) | Make every GPU count: Maximizing GPU efficiency for inference at scale | frontier abstract |
| COM329 | tue 12-01 | 16:30-17:30 | Caesars Forum | Code talk | 300 | reserve | self-managed agents, (lambda microvms + web functions) | Sandboxing AI Agents on EKS: Isolation That Scales |
| OPN401-R1 | wed 12-02 | 09:00-10:00 | MGM Grand | Builders' session | 400 | reserve | (self-managed agents) | Powertools for agent DevOps: Debug reasoning, not just exceptions |
| OPN304-R | wed 12-02 | 12:30-14:30 | Caesars Forum | Workshop | 300 | reserve | self-managed agents | Observability for AI agents: Strands, OpenTelemetry, and Langfuse |
| OPN307-R | wed 12-02 | 12:30-14:30 | Caesars Forum | Workshop | 300 | reserve | self-managed agents | Build multi-agent workflows with Strands Agents SDK on AWS |
| ANT419-R1 | wed 12-02 | 12:30-14:30 | Wynn/Encore | Workshop | 400 | reserve | (self-managed agents) | Power streaming analytics on AWS with AI-driven insights |
| AIM401-R1 | wed 12-02 | 13:30-14:30 | Wynn/Encore | Builders' session | 400 | reserve | (self-managed agents), (video games) | Agents that train themselves: autonomous reinforcement learning on AWS |
| AIM346-R1 | wed 12-02 | 14:30-15:30 | Wynn/Encore | Chalk talk | 300 | reserve | self-managed agents, (nvidia), (open-weight models) | Deploy, scale, and tune AI model serving with self-managed agents |
| AIM446-R1 | wed 12-02 | 14:30-15:30 | Wynn/Encore | Code talk | 400 | reserve | self-managed agents | Beyond Prompt Engineering: Optimize the Agent Harness |
| CON402-R1 | wed 12-02 | 16:00-17:00 | Caesars Palace | Chalk talk | 400 | reserve | (self-managed agents), (amazon.com / amazon retail) | Amazon EKS: Infrastructure as code, GitOps, or CI/CD |
| SEC220-S | wed 12-02 | 17:30-17:50 | Venetian | Lightning talk | 200 | walk-up | (self-managed agents) | Move AI agents from prototype to production with 1Password (sponsored by 1Password) |
| AIM341 | thu 12-03 | 08:30-09:30 | Caesars Palace | Breakout session | 300 | walk-up | self-managed agents | Migrating a Managed Assistant API to Strands Agents SDK |
| HMC403-R | thu 12-03 | 08:30-10:30 | MGM Grand | Workshop | 400 | reserve | self-managed agents | Self-managed agentic AI at the hybrid edge |
| SVS307 | thu 12-03 | 10:00-11:00 | Caesars Forum | Builders' session | 300 | reserve | self-managed agents, lambda microvms + web functions | Running untrusted code in sandboxes with AWS Lambda MicroVMs |
| AIM446-R | thu 12-03 | 10:00-11:00 | MGM Grand | Code talk | 400 | reserve | self-managed agents | Beyond Prompt Engineering: Optimize the Agent Harness |
| IND406-R | thu 12-03 | 10:30-11:30 | Caesars Forum | Chalk talk | 400 | reserve | (self-managed agents), (amazon nova) | The agentic restaurant: AI agents that run your kitchen |
| CMP328-R1 | thu 12-03 | 13:30-14:30 | MGM Grand | Chalk talk | 300 | reserve | self-managed agents | Deploy AI agent sandboxes on EC2 |
| ANT419-R | thu 12-03 | 15:00-17:00 | MGM Grand | Workshop | 400 | reserve | (self-managed agents) | Power streaming analytics on AWS with AI-driven insights |
| CMP318-R | thu 12-03 | 15:00-17:00 | MGM Grand | Workshop | 300 | reserve | self-managed agents | Build your iOS CI/CD pipeline with AI agents on EC2 Mac |
| OPN304-R1 | thu 12-03 | 15:00-17:00 | Wynn/Encore | Workshop | 300 | reserve | self-managed agents | Observability for AI agents: Strands, OpenTelemetry, and Langfuse |
| OPN307-R1 | thu 12-03 | 15:00-17:00 | MGM Grand | Workshop | 300 | reserve | self-managed agents | Build multi-agent workflows with Strands Agents SDK on AWS |
| AIM3315 | fri 12-04 | 12:00-12:20 | Wynn/Encore | Lightning talk | 300 | walk-up | (self-managed agents), (nvidia) | Optimize agentic AI costs with EC2 Capacity Blocks and Spot Instances |

### amazon braket

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CMP252 | mon 11-30 | 12:00-13:00 | Caesars Forum | Chalk talk | 200 | reserve | amazon braket | Running larger, higher-fidelity quantum experiments on Amazon Braket |
| CMP340 | mon 11-30 | 13:00-14:00 | MGM Grand | Chalk talk | 300 | reserve | amazon braket | Drug discovery and materials use cases with Amazon Braket and Q-CTRL |
| INV529 | tue 12-01 | 12:00-13:00 | MGM Grand | Chalk talk | 500 | reserve | (amazon braket) | Beyond RSA: Post-quantum data encryption using ML-KEM in AWS KMS |
| GHJ203-R | tue 12-01 | 12:00-14:00 | Wynn/Encore | Gamified learning | 200 | reserve | (amazon braket) | Post-quantum cryptography tabletop experience |
| INV518 | wed 12-02 | 08:30-09:30 | MGM Grand | Chalk talk | 500 | reserve | amazon braket | Quantum Error Correction - Progress, Hardware, and What's Next |
| CMP402 | thu 12-03 | 08:30-10:30 | MGM Grand | Workshop | 400 | reserve | amazon braket | Build hybrid quantum-classical solutions for science and engineering on Amazon Braket |
| CMP348-R | thu 12-03 | 11:30-12:30 | MGM Grand | Chalk talk | 300 | reserve | amazon braket | Building better quantum computers with digital twins |
| CMP310 | thu 12-03 | 11:30-12:30 | MGM Grand | Builders' session | 300 | reserve | amazon braket | Beyond the simulator: Quantum chemistry workflows on real hardware |
| CMP306 | thu 12-03 | 12:00-13:00 | Caesars Palace | Breakout session | 300 | walk-up | amazon braket | Delivering next-generation quantum hardware on Amazon Braket |
| GHJ203-R1 | thu 12-03 | 15:00-17:00 | Wynn/Encore | Gamified learning | 200 | reserve | (amazon braket) | Post-quantum cryptography tabletop experience |

### databricks

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HMC303 | mon 11-30 | 09:00-10:00 | MGM Grand | Breakout session | 300 | walk-up | (databricks), (nvidia) | Choosing the right hybrid deployment for your AI workloads |
| ANT418 | mon 11-30 | 15:00-17:00 | MGM Grand | Workshop | 400 | reserve | (databricks) | Experience catalog federation on AWS: build a multi-cloud open data lakehouse |
| MAM215-S | tue 12-01 | 15:00-16:00 | Caesars Forum | Breakout session | 200 | walk-up | databricks | Conversational AI at Scale: S&P Global Energy's 30+ Genie Agents (sponsored by Databricks) |
| CMP204-S | wed 12-02 | 16:00-17:00 | Wynn/Encore | Breakout session | 200 | walk-up | (databricks) | Agentic AI on AWS with Intel® Xeon® 6 (sponsored by Intel) |
| SEC359 | thu 12-03 | 09:00-10:00 | Wynn/Encore | Breakout session | 300 | walk-up | (databricks) | From static to dynamic - modernizing bidirectional federation | frontier abstract |

### lambda microvms + web functions

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SVS347-R | mon 11-30 | 09:00-10:00 | Caesars Forum | Code talk | 300 | reserve | lambda microvms + web functions | Building and scaling low latency web applications with AWS Lambda Web Functions |
| API316 | mon 11-30 | 10:00-11:00 | Caesars Palace | Code talk | 300 | reserve | lambda microvms + web functions | Coding an AI agent from scratch with AWS Lambda durable functions |
| API313 | mon 11-30 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Reliable data processing with AWS serverless services |
| SVS203-R | mon 11-30 | 15:00-16:00 | Caesars Forum | Builders' session | 200 | reserve | lambda microvms + web functions | Building interactive web applications on AWS Lambda Web Functions |
| COM326 | mon 11-30 | 15:00-16:00 | Caesars Forum | Code talk | 300 | reserve | lambda microvms + web functions | Observable Agents with Lambda Durable Functions and OpenTelemetry |
| COP405-R1 | mon 11-30 | 15:00-16:00 | Wynn/Encore | Code talk | 400 | reserve | (lambda microvms + web functions) | When agents run code: sandboxes for reliable DevOps |
| API319 | mon 11-30 | 16:00-17:00 | Caesars Forum | Breakout session | 300 | walk-up | (lambda microvms + web functions) | Orchestrating AI agents with AWS serverless services |
| SVS336 | tue 12-01 | 11:30-12:30 | Caesars Forum | Breakout session | 300 | walk-up | (lambda microvms + web functions) | Building production AI agents on AWS: compute, security, state, and cost |
| SVS351 | tue 12-01 | 12:00-13:00 | MGM Grand | Breakout session | 300 | walk-up | lambda microvms + web functions | Lambda Managed Instances: EC2 Power with Serverless Simplicity |
| SVS325-R | tue 12-01 | 12:00-13:00 | Caesars Forum | Builders' session | 300 | reserve | lambda microvms + web functions | Distributed transactions with Step Functions and durable functions |
| API302-R | tue 12-01 | 12:00-14:00 | Caesars Palace | Workshop | 300 | reserve | (lambda microvms + web functions) | Serverlesspresso: Build an event-driven app from the ground up |
| SVS207 | tue 12-01 | 13:30-14:30 | MGM Grand | Breakout session | 200 | walk-up | (lambda microvms + web functions) | Modernizing your compute stack with Lambda's new execution models |
| API318 | tue 12-01 | 13:30-13:50 | Wynn/Encore | Lightning talk | 300 | walk-up | (lambda microvms + web functions) | Composing the right orchestration for serverless workflows |
| SVS315 | tue 12-01 | 14:30-15:30 | Caesars Forum | Builders' session | 300 | reserve | (lambda microvms + web functions) | Reducing Lambda cost with Graviton and managed instances |
| SVS333-R1 | tue 12-01 | 16:30-17:30 | Wynn/Encore | Chalk talk | 300 | reserve | lambda microvms + web functions | Lambda MicroVMs: Secure stateful sandboxes for code execution |
| SVS341-R1 | tue 12-01 | 16:30-17:30 | Caesars Palace | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Lambda performance tuning and cost optimization |
| SVS332-R1 | tue 12-01 | 16:30-17:30 | Caesars Palace | Chalk talk | 300 | reserve | lambda microvms + web functions | Lambda Managed Instances: Always-on Serverless Compute |
| SVS325-R1 | wed 12-02 | 08:30-09:30 | Caesars Palace | Builders' session | 300 | reserve | lambda microvms + web functions | Distributed transactions with Step Functions and durable functions |
| SVS330-R1 | wed 12-02 | 09:00-10:00 | Caesars Palace | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Operating Lambda at scale: Choosing the right execution model |
| SVS331-R1 | wed 12-02 | 09:00-10:00 | Wynn/Encore | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Serverless Java in 2026 |
| API315-R | wed 12-02 | 10:30-11:30 | Caesars Forum | Code talk | 300 | reserve | lambda microvms + web functions | Coding high-throughput data pipelines with AWS Lambda durable functions |
| API310 | wed 12-02 | 12:00-13:00 | Caesars Forum | Builders' session | 300 | reserve | (lambda microvms + web functions) | Build GenAI-Powered Workflows with AWS Serverless and AWS AI Services |
| API314-R1 | wed 12-02 | 12:00-13:00 | Wynn/Encore | Chalk talk | 300 | reserve | lambda microvms + web functions | A closer look at AWS Lambda durable functions |
| API302-R1 | wed 12-02 | 12:30-14:30 | Wynn/Encore | Workshop | 300 | reserve | (lambda microvms + web functions) | Serverlesspresso: Build an event-driven app from the ground up |
| COM303 | wed 12-02 | 13:00-14:00 | Caesars Forum | Breakout session | 300 | walk-up | (lambda microvms + web functions) | Lambda for every scale and workload shape |
| SVS350 | wed 12-02 | 13:30-14:30 | Caesars Palace | Breakout session | 300 | walk-up | lambda microvms + web functions | Lambda Web Functions: From Event Handlers to Standard HTTP on Lambda |
| SVS333-R | wed 12-02 | 13:30-14:30 | Caesars Forum | Chalk talk | 300 | reserve | lambda microvms + web functions | Lambda MicroVMs: Secure stateful sandboxes for code execution |
| SVS208 | wed 12-02 | 16:00-16:20 | Wynn/Encore | Lightning talk | 200 | walk-up | lambda microvms + web functions, (self-managed agents) | How AI-native startups run untrusted agent code on Lambda MicroVMs |
| API315-R1 | thu 12-03 | 08:30-09:30 | Caesars Palace | Code talk | 300 | reserve | lambda microvms + web functions | Coding high-throughput data pipelines with AWS Lambda durable functions |
| SVS401-R | thu 12-03 | 12:00-14:00 | Caesars Forum | Workshop | 400 | reserve | lambda microvms + web functions | Orchestrating agentic applications with Lambda durable functions |
| SVS341-R | thu 12-03 | 13:00-14:00 | Caesars Forum | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Lambda performance tuning and cost optimization |
| SVS347-R1 | thu 12-03 | 13:00-14:00 | Caesars Palace | Code talk | 300 | reserve | lambda microvms + web functions | Building and scaling low latency web applications with AWS Lambda Web Functions |
| SVS337 | thu 12-03 | 13:30-14:30 | Caesars Palace | Breakout session | 300 | walk-up | lambda microvms + web functions, (self-managed agents) | AWS Lambda MicroVMs: Strong isolation for agents & beyond |
| API314-R | thu 12-03 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | lambda microvms + web functions | A closer look at AWS Lambda durable functions |
| SVS330-R | thu 12-03 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Operating Lambda at scale: Choosing the right execution model |
| COP405-R | thu 12-03 | 15:00-16:00 | Wynn/Encore | Code talk | 400 | reserve | (lambda microvms + web functions) | When agents run code: sandboxes for reliable DevOps |
| SVS348 | thu 12-03 | 16:00-17:00 | MGM Grand | Breakout session | 300 | walk-up | lambda microvms + web functions | Serverless compute built for the web |
| SVS331-R | thu 12-03 | 16:00-17:00 | Caesars Forum | Chalk talk | 300 | reserve | (lambda microvms + web functions) | Serverless Java in 2026 |
| SVS401-R1 | fri 12-04 | 10:30-12:30 | Wynn/Encore | Workshop | 400 | reserve | lambda microvms + web functions | Orchestrating agentic applications with Lambda durable functions |

### video games

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IND382 | mon 11-30 | 08:30-09:30 | Caesars Forum | Chalk talk | 300 | reserve | (video games), (amazon.com / amazon retail) | Enterprise-Ready: How NetEase Governs AI at Scale |
| TNC214-R | mon 11-30 | 12:00-14:00 | Caesars Palace | Exam prep | 200 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified Cloud Practitioner |
| AIM343 | mon 11-30 | 13:00-14:00 | MGM Grand | Breakout session | 300 | walk-up | video games, (amazon.com / amazon retail) | Data Prep to Deployment: How Tencent Games Scaled to 1,000 GPUs on SageMaker HyperPod |
| NET326 | mon 11-30 | 13:00-14:00 | Caesars Forum | Breakout session | 300 | walk-up | (video games) | Deep dive into Elastic Load Balancing for modern workloads |
| GHJ318-R | mon 11-30 | 15:30-17:30 | Wynn/Encore | Gamified learning | 300 | reserve | (video games) | re:Architecture Rodeo: Designing Agentic AI Applications |
| AIM323 | mon 11-30 | 16:00-17:00 | MGM Grand | Code talk | 300 | reserve | (video games) | Serving world models on AWS Trainium with native PyTorch |
| TNC306-R | tue 12-01 | 08:30-11:30 | Caesars Palace | Exam prep | 300 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified Solutions Architect - Associate |
| AIM304-R1 | tue 12-01 | 11:30-12:30 | MGM Grand | Builders' session | 300 | reserve | (video games), (open-weight models) | Deploy and optimize world models with agentic AI workflows |
| AMZ304 | tue 12-01 | 12:00-13:00 | Caesars Forum | Chalk talk | 300 | reserve | video games | Instant Play Demos on Twitch – Increasing Player Engagement |
| IND316-R1 | tue 12-01 | 13:00-14:00 | Caesars Forum | Chalk talk | 300 | reserve | video games | Best Practices for Successful Multiplayer Game Launches |
| DVT342-S | tue 12-01 | 14:30-15:30 | Caesars Palace | Breakout session | 300 | walk-up | (video games) | Building 10x Organizations - Using Modern Productivity Metrics (sponsored by Atlassian) |
| COP341 | tue 12-01 | 15:00-15:20 | Wynn/Encore | Lightning talk | 300 | walk-up | (video games) | Learnings from resilience testing in AWS |
| DVT313 | tue 12-01 | 15:30-17:30 | Caesars Forum | Workshop | 300 | reserve | (video games) | Build real-time applications with AWS Amplify |
| IND363 | tue 12-01 | 15:30-17:30 | Caesars Forum | Workshop | 300 | reserve | (video games), (amazon nova) | Defeat Player Evasion: AI Moderation at Scale on Amazon Bedrock. |
| TNC214-R1 | wed 12-02 | 08:00-10:00 | Caesars Palace | Exam prep | 200 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified Cloud Practitioner |
| IND383 | wed 12-02 | 10:00-11:00 | Caesars Forum | Breakout session | 300 | walk-up | video games | An Epic Tale: Hyperscale Storage & Compute for the Fortnite Ecosystem |
| CMP337 | wed 12-02 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | video games | Choosing a game server instance without guessing |
| KEY004 | wed 12-02 | 15:00-16:00 | Venetian | Keynote |  | walk-up | (video games) | Partner Keynote |
| GHJ318-R1 | wed 12-02 | 15:30-17:30 | Wynn/Encore | Gamified learning | 300 | reserve | (video games) | re:Architecture Rodeo: Designing Agentic AI Applications |
| TNC306-R1 | thu 12-03 | 08:00-11:00 | Caesars Palace | Exam prep | 300 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified Solutions Architect - Associate |
| IND316-R | thu 12-03 | 10:00-11:00 | Caesars Forum | Chalk talk | 300 | reserve | video games | Best Practices for Successful Multiplayer Game Launches |
| SEC401 | thu 12-03 | 12:00-14:00 | Wynn/Encore | Workshop | 400 | reserve | video games | Winning the DDoS Game: defend your app under real-time attack |
| MAM406 | thu 12-03 | 12:30-14:30 | Caesars Palace | Workshop | 400 | reserve | (video games) | Modernize Windows to Linux and SQL to PostgreSQL with agentic AI |
| AIM304-R | thu 12-03 | 13:30-14:30 | MGM Grand | Builders' session | 300 | reserve | (video games), (open-weight models) | Deploy and optimize world models with agentic AI workflows |

### nvidia

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AIM344 | mon 11-30 | 13:00-14:00 | MGM Grand | Builders' session | 300 | reserve | (nvidia) | GPU cluster failure patterns on AWS: observe, diagnose, recover |
| CMP408 | mon 11-30 | 13:30-14:30 | MGM Grand | Chalk talk | 400 | reserve | nvidia | The cloud holodeck: Stream NVIDIA Omniverse, scale headless sim on AWS |
| HMC401-R1 | mon 11-30 | 14:30-15:30 | Wynn/Encore | Code talk | 400 | reserve | nvidia, (open-weight models) | GPU orchestration using NVIDIA Run:ai across the edge |
| DAT318-S | mon 11-30 | 15:00-16:00 | Caesars Palace | Breakout session | 300 | walk-up | nvidia | 10x Faster Vector Indexes: GPU Acceleration in Amazon OpenSearch with NVIDIA cuVS (sponsored by NVIDIA) |
| IND389 | mon 11-30 | 15:00-16:00 | Wynn/Encore | Chalk talk | 300 | reserve | (nvidia) | Physical AI for MedTech: From Intelligent Devices to Business Impact |
| AIM392 | mon 11-30 | 16:30-17:30 | MGM Grand | Chalk talk | 300 | reserve | (nvidia), (open-weight models) | Expand your GPU playbook: Amazon EC2 G7e/G7 for inference and training |
| AIM347-R | tue 12-01 | 12:00-14:00 | MGM Grand | Workshop | 300 | reserve | (nvidia) | AI Systems Performance Engineering on AWS: A practitioner's deep dive |
| AIM3316-S | tue 12-01 | 13:30-14:30 | Venetian | Breakout session | 300 | walk-up | nvidia, open-weight models | Koa: NVIDIA Nemotron-Powered CRM Reasoning Inside Salesforce’s AWS Trust Boundary (sponsored by NVIDIA) |
| IND102-S | tue 12-01 | 15:00-16:00 | Venetian | Breakout session | 100 | walk-up | nvidia | Accelerating with NVIDIA Omniverse: VW’s Battery Manufacturing Digital Twin (sponsored by NVIDIA) |
| CMP327-R | tue 12-01 | 15:00-16:00 | MGM Grand | Chalk talk | 300 | reserve | (nvidia) | Optimize AI inference costs: Compare token economics on AWS silicon |
| AIM345 | wed 12-02 | 08:30-09:30 | MGM Grand | Builders' session | 300 | reserve | (nvidia) | Disaggregated inference at scale: when to split prefill from decode |
| AIM3312 | wed 12-02 | 10:30-11:30 | Caesars Forum | Breakout session | 300 | walk-up | (nvidia), (amazon.com / amazon retail) | Accelerate analytics with GPUs at lower cost: Spark, DuckDB, and more |
| ANT203-S | wed 12-02 | 11:00-11:20 | Venetian | Lightning talk | 200 | walk-up | nvidia | Accelerating Data Processing: GPU Accelerated Amazon EMR at the Enterprise Scale (sponsored by NVIDIA) |
| AIM458-S | wed 12-02 | 12:30-14:30 | MGM Grand | Workshop | 400 | reserve | nvidia | The Physical AI Blueprint: A Full-Stack Solution with AWS and NVIDIA (sponsored by NVIDIA) |
| AIM2210 | wed 12-02 | 13:30-14:30 | MGM Grand | Breakout session | 200 | walk-up | nvidia | What's new with NVIDIA GPUs in Amazon EC2 |
| AIM389-S | wed 12-02 | 15:00-17:00 | MGM Grand | Workshop | 300 | reserve | nvidia, open-weight models | Fine-tune and evaluate NVIDIA Open models on Amazon SageMaker (sponsored by NVIDIA) |
| HMC401-R | wed 12-02 | 16:00-17:00 | MGM Grand | Code talk | 400 | reserve | nvidia, (open-weight models) | GPU orchestration using NVIDIA Run:ai across the edge |
| IND3339 | wed 12-02 | 17:30-17:50 | Venetian | Lightning talk | 300 | walk-up | (nvidia) | Agentic advertising with privacy-enhanced data collaboration |
| AIM347-R1 | thu 12-03 | 12:00-14:00 | Wynn/Encore | Workshop | 300 | reserve | (nvidia) | AI Systems Performance Engineering on AWS: A practitioner's deep dive |
| CMP327-R1 | thu 12-03 | 13:30-14:30 | Caesars Palace | Chalk talk | 300 | reserve | (nvidia) | Optimize AI inference costs: Compare token economics on AWS silicon |
| CON313 | thu 12-03 | 15:30-17:30 | MGM Grand | Workshop | 300 | reserve | (nvidia), (open-weight models) | Building and scaling inference workloads on Amazon EKS |

### nfl / sports

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GHJ213 | wed 12-02 | 16:00-17:30 | MGM Grand | Breakout session | 200 | walk-up | nfl / sports, (self-managed agents) | AWS AI League Championship Grand Finale: Agentic Football Cup |

### amazon nova

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TNC318-R | mon 11-30 | 15:30-17:00 | Caesars Palace | Lab | 300 | reserve | (amazon nova) | Orchestrating AI Agents with AgentCore Runtime |
| AIM218 | tue 12-01 | 12:00-13:00 | MGM Grand | Chalk talk | 200 | reserve | amazon nova | Building conversational AI with Amazon Nova 2.5 Sonic |
| AIM357 | tue 12-01 | 15:00-17:00 | MGM Grand | Workshop | 300 | reserve | amazon nova | Cross-modal search with Amazon Nova Multimodal Embeddings |
| MAM322-R1 | tue 12-01 | 15:00-17:00 | Wynn/Encore | Workshop | 300 | reserve | (amazon nova) | Build an AI testing safety net before you modernize |
| AIM354 | tue 12-01 | 16:00-17:00 | MGM Grand | Chalk talk | 300 | reserve | amazon nova, (amazon.com / amazon retail) | Designing  AI Agents with Amazon Nova Multimodal Embeddings and Voice AI |
| TNC317 | wed 12-02 | 08:00-09:30 | Caesars Palace | Lab | 300 | reserve | (amazon nova) | Building Context-Aware Agents with AgentCore Memory |
| AIM398 | wed 12-02 | 08:30-09:30 | MGM Grand | Breakout session | 300 | walk-up | (amazon nova) | Customer paths to production grade domain-specific AI with Forge |
| TNC318-R1 | wed 12-02 | 12:00-13:30 | Caesars Palace | Lab | 300 | reserve | (amazon nova) | Orchestrating AI Agents with AgentCore Runtime |
| AIM352 | wed 12-02 | 16:00-17:00 | Caesars Forum | Builders' session | 300 | reserve | amazon nova, (self-managed agents) | Build and deploy a voice agent with Amazon Nova 2.5 Sonic |
| MAM322-R | thu 12-03 | 12:00-14:00 | Caesars Palace | Workshop | 300 | reserve | (amazon nova) | Build an AI testing safety net before you modernize |
| AIM2211 | thu 12-03 | 14:30-14:50 | Venetian | Lightning talk | 200 | walk-up | amazon nova | From Cost to Compliance: Scaling Scalable GenAI with Amazon Nova |

### netflix

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HMC307 | mon 11-30 | 12:30-12:50 | Wynn/Encore | Lightning talk | 300 | walk-up | netflix, (nvidia) | Scaling interactive generative AI at Netflix with AWS Local Zones |
| IND379 | mon 11-30 | 16:00-17:00 | Caesars Forum | Breakout session | 300 | walk-up | netflix | Scaling Multi-Account IAM at Netflix: Access, Visibility and Credentials |
| DAT451 | thu 12-03 | 12:00-13:00 | MGM Grand | Breakout session | 400 | walk-up | netflix | Netflix on Aurora PostgreSQL: Operating 40TB+ after fleet migration |

### amazon.com / amazon retail

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BIZ109 | mon 11-30 | 08:30-09:30 | Caesars Forum | Breakout session | 100 | walk-up | (amazon.com / amazon retail) | Citizens Bank: Building AI-Native CX from Vision to Production |
| STG363 | mon 11-30 | 08:30-09:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Modernizing VMware workloads with Amazon FSx for NetApp ONTAP |
| ANT314 | mon 11-30 | 09:00-10:00 | Caesars Palace | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Accelerating data analytics on Apache Iceberg with Amazon S3 Tables |
| IND366 | mon 11-30 | 09:00-10:00 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Zero-Shot Demand Forecasting with Chronos 2, SMUS, and Quick Suite |
| BIZ325 | mon 11-30 | 10:00-11:00 | Caesars Palace | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Fix Data Gaps Fast: Agentic Onboarding with Amazon Connect Decisions |
| SNR304 | mon 11-30 | 10:30-11:30 | Venetian | Mainstage | 300 | walk-up | (amazon.com / amazon retail) | A leader's guide to how AI is changing Amazon’s ways of working |
| ANT339 | mon 11-30 | 11:30-12:30 | Caesars Palace | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Build scalable streaming and messaging applications with Amazon Kinesis and AmazonMSK |
| IND332 | mon 11-30 | 13:00-14:00 | Wynn/Encore | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Unifying fragmented data: A lakehouse for the agentic AI era |
| BIZ404 | mon 11-30 | 13:30-14:30 | Caesars Palace | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Teaching Quick to Remember and Connect with Memory and Knowledge Graphs |
| STG357-R | mon 11-30 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Accelerate database protection and testing with EBS Snapshots and clones |
| CON307-R | mon 11-30 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Demystifying the shared security model on Amazon ECS |
| CON411 | mon 11-30 | 15:00-16:00 | Caesars Forum | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Scale, optimize and deploy inference with Karpenter and EKS Auto Mode |
| API301 | mon 11-30 | 16:00-17:00 | Caesars Palace | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Operationalize enterprise event routing with Amazon EventBridge |
| BIZ201-R | mon 11-30 | 16:00-17:00 | Caesars Palace | Chalk talk | 200 | reserve | (amazon.com / amazon retail) | Agentic Integration: How AI Agents Replace Static CRM Connectors |
| STG361 | mon 11-30 | 16:00-17:00 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Break free from on-premises NAS: Migrating to AWS |
| ANT349 | mon 11-30 | 16:30-17:30 | MGM Grand | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Cost-effective serverless data integrations and workflows for AI-ready data |
| SNR308 | mon 11-30 | 16:30-17:30 | Venetian | Mainstage | 300 | walk-up | amazon.com / amazon retail | A leader's guide to how Amazon built its data foundation for agents |
| BIZ324 | mon 11-30 | 16:30-17:30 | Caesars Palace | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Self-Tuning Demand Forecasts: How Agentic AI Puts Business Users in the Driver's Seat |
| CON332 | mon 11-30 | 16:30-17:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Strategies for agentic-ready architectures on Amazon EKS |
| IND330-R | mon 11-30 | 16:30-17:30 | Wynn/Encore | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Patterns for mitigating AI-powered security threats in financial services |
| COP335 | tue 12-01 | 11:30-12:30 | Wynn/Encore | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Evolve your observability for the agentic era |
| MAM348-R | tue 12-01 | 11:30-12:30 | MGM Grand | Builders' session | 300 | reserve | (amazon.com / amazon retail) | Provision Desktops for Builders Faster with WorkSpaces |
| ANT428-R | tue 12-01 | 13:00-14:00 | MGM Grand | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Best practices for operating an Apache Iceberg lakehouse at scale |
| BIZ202-S | tue 12-01 | 13:00-13:20 | Venetian | Lightning talk | 200 | walk-up | (amazon.com / amazon retail) | Trust at Scale: Unlocking Enterprise Agentic AI (sponsored by Qlik) |
| DVT320 | tue 12-01 | 13:30-14:30 | Caesars Forum | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | How Kiro learns: an AI coding agent that improves with every session |
| IND330-R1 | tue 12-01 | 13:30-14:30 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Patterns for mitigating AI-powered security threats in financial services |
| MAM347 | tue 12-01 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Meet Your AI Teammate for WorkSpaces Administration |
| CON337-R1 | tue 12-01 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Decouple and scale Amazon ECS workloads with event-driven patterns |
| AMZ401-R | tue 12-01 | 15:00-16:00 | Caesars Forum | Code talk | 400 | reserve | amazon.com / amazon retail | How Amazon Ads Built a Service Mesh Without a Control Plane Service |
| NET319-R1 | tue 12-01 | 15:00-16:00 | Caesars Palace | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Practical applications of edge compute in Amazon CloudFront |
| STG357-R1 | tue 12-01 | 16:00-17:00 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Accelerate database protection and testing with EBS Snapshots and clones |
| STG348-R1 | tue 12-01 | 16:30-17:30 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Designing performant and cost-effective data lakes on Amazon S3 Tables |
| DAT420-R1 | wed 12-02 | 08:30-09:30 | Caesars Palace | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Dive deep into Amazon DynamoDB using design puzzles |
| NET319-R | wed 12-02 | 09:00-10:00 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Practical applications of edge compute in Amazon CloudFront |
| ANT346 | wed 12-02 | 10:00-11:00 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | What's new with Amazon Kinesis Data Streams |
| STG360 | wed 12-02 | 10:00-11:00 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Ransomware resilience with Amazon FSx for NetApp ONTAP |
| AMZ301 | wed 12-02 | 11:30-12:30 | Caesars Forum | Breakout session | 300 | walk-up | amazon.com / amazon retail | The Art of the Impossible: How Amazon Builds on AWS |
| STG348-R | wed 12-02 | 11:30-12:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Designing performant and cost-effective data lakes on Amazon S3 Tables |
| CON345 | wed 12-02 | 11:30-12:30 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Eliminate wasted compute capacity with Amazon ECS |
| AMZ201 | wed 12-02 | 13:00-14:00 | Caesars Forum | Breakout session | 200 | walk-up | (amazon.com / amazon retail) | Lessons in Scale and Innovation Through the Deployment of AI Agents |
| AIM231-S | wed 12-02 | 13:00-14:00 | Wynn/Encore | Breakout session | 200 | walk-up | (amazon.com / amazon retail) | AI That Answers: Customer Experiences Reimagined with Amazon Connect (sponsored by PwC) |
| API305-R | wed 12-02 | 13:00-14:00 | Caesars Forum | Builders' session | 300 | reserve | (amazon.com / amazon retail) | Building enterprise-scale event buses with Amazon EventBridge |
| ANT428-R1 | wed 12-02 | 13:00-14:00 | Caesars Palace | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Best practices for operating an Apache Iceberg lakehouse at scale |
| AIM217 | wed 12-02 | 13:30-14:30 | MGM Grand | Breakout session | 200 | walk-up | (amazon.com / amazon retail) | Build Voice AI experiences with Amazon Polly and Transcribe |
| AMZ401-R1 | wed 12-02 | 13:30-14:30 | Wynn/Encore | Code talk | 400 | reserve | amazon.com / amazon retail | How Amazon Ads Built a Service Mesh Without a Control Plane Service |
| BIZ201-R1 | wed 12-02 | 13:30-14:30 | Caesars Palace | Chalk talk | 200 | reserve | (amazon.com / amazon retail) | Agentic Integration: How AI Agents Replace Static CRM Connectors |
| CON337-R | wed 12-02 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Decouple and scale Amazon ECS workloads with event-driven patterns |
| AIM342 | thu 12-03 | 08:30-09:30 | MGM Grand | Breakout session | 300 | walk-up | (amazon.com / amazon retail), (open-weight models) | One Service, Every Workload: Build, Customize, and Deploy with SageMaker AI |
| HMC406 | thu 12-03 | 08:30-09:30 | MGM Grand | Code talk | 400 | reserve | amazon.com / amazon retail | How Amazon Robotics runs AWS Outposts across hundreds of fulfillment centers |
| DAT420-R | thu 12-03 | 10:00-11:00 | MGM Grand | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Dive deep into Amazon DynamoDB using design puzzles |
| DVT326 | thu 12-03 | 10:30-11:30 | Caesars Forum | Code talk | 300 | reserve | (amazon.com / amazon retail) | Learn faster: Experimentation in an AI world |
| STG356 | thu 12-03 | 11:30-12:30 | MGM Grand | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | From CSV to Iceberg: Understanding open data formats on Amazon S3 |
| CON307-R1 | thu 12-03 | 11:30-12:30 | Caesars Palace | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Demystifying the shared security model on Amazon ECS |
| API305-R1 | thu 12-03 | 12:00-13:00 | MGM Grand | Builders' session | 300 | reserve | (amazon.com / amazon retail) | Building enterprise-scale event buses with Amazon EventBridge |
| ANT337 | thu 12-03 | 13:00-14:00 | MGM Grand | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | From human search to agent retrieval on OpenSearch Service |
| AIM214 | thu 12-03 | 14:30-15:30 | MGM Grand | Breakout session | 200 | walk-up | (amazon.com / amazon retail) | How Vanguard uses SageMaker HyperPod from training to inference for custom LLMs |
| STG343 | thu 12-03 | 15:00-16:00 | Venetian | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | Beyond the GPU: Optimizing AI performance with storage architecture |
| DAT420-R2 | thu 12-03 | 16:00-17:00 | MGM Grand | Chalk talk | 400 | reserve | (amazon.com / amazon retail) | Dive deep into Amazon DynamoDB using design puzzles |
| IND345 | fri 12-04 | 08:30-09:30 | Wynn/Encore | Breakout session | 300 | walk-up | amazon.com / amazon retail, (amazon nova) | Human+AI Collaboration: How Amazon Deploys Autonomous Operations on AWS |

### open-weight models

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AIM310 | mon 11-30 | 08:30-09:30 | Caesars Forum | Breakout session | 300 | walk-up | (open-weight models) | Making foundation models performant on AWS Trainium3 |
| CMP321-R | mon 11-30 | 08:30-10:30 | MGM Grand | Workshop | 300 | reserve | open-weight models | Build an agentic AI system on Amazon EKS with CPU-only inference |
| AIM325 | mon 11-30 | 13:00-14:00 | MGM Grand | Chalk talk | 300 | reserve | open-weight models, (self-managed agents) | Fine-Tune Agents That Reason: Multi-Turn RL on SageMaker AI |
| AIM361 | mon 11-30 | 14:30-15:30 | MGM Grand | Breakout session | 300 | walk-up | open-weight models | Customize open-weight models for accuracy, cost, and latency on SageMaker AI |
| AIM2202-S | mon 11-30 | 14:30-15:30 | Venetian | Breakout session | 200 | walk-up | (open-weight models) | Building Proprietary Multi-Agentic AI Workflows for Low Latency and High Reliability (sponsored by Capital One) |
| CMP405 | mon 11-30 | 15:30-17:30 | MGM Grand | Workshop | 400 | reserve | (open-weight models) | Hands-on: Harden your AI agents with Nitro Confidential Computing |
| AIM362 | tue 12-01 | 14:30-15:30 | MGM Grand | Chalk talk | 300 | reserve | open-weight models | Which customization compute? A decision approach for model fine-tuning |
| INV521-R | wed 12-02 | 13:00-14:00 | Wynn/Encore | Chalk talk | 500 | reserve | (open-weight models) | Teaching Telemetry to Think: From Raw Signals to Root Cause |
| AIM435 | wed 12-02 | 13:00-14:00 | MGM Grand | Code talk | 400 | reserve | open-weight models | On-Policy Distillation on HyperPod EKS: Train Smarter Small Models |
| AIM349 | wed 12-02 | 13:30-14:30 | MGM Grand | Chalk talk | 300 | reserve | open-weight models | Build production AI assistant with Hugging Face Libraries and models |
| AIM338-R1 | wed 12-02 | 14:30-15:30 | Caesars Palace | Chalk talk | 300 | reserve | open-weight models | Open-weights at work: Scaling AI without scaling the bill |
| AIM3304 | wed 12-02 | 15:00-17:00 | MGM Grand | Workshop | 300 | reserve | (open-weight models) | Evaluate, select, optimize your AI model |
| AIM338-R | thu 12-03 | 08:30-09:30 | MGM Grand | Chalk talk | 300 | reserve | open-weight models | Open-weights at work: Scaling AI without scaling the bill |
| AIM3307 | thu 12-03 | 09:00-10:00 | MGM Grand | Breakout session | 300 | walk-up | (open-weight models) | What's next in SageMaker AI, how to make data your differentiator for AI. |
| INV521-R1 | thu 12-03 | 10:30-11:30 | MGM Grand | Chalk talk | 500 | reserve | (open-weight models) | Teaching Telemetry to Think: From Raw Signals to Root Cause |
| AIM3317 | thu 12-03 | 15:00-16:00 | Wynn/Encore | Breakout session | 300 | walk-up | (open-weight models) | How Datadog optimizes cost per token for GenAI at scale |
| AIM312-R1 | thu 12-03 | 15:00-16:00 | Wynn/Encore | Chalk talk | 300 | reserve | open-weight models | Beyond fine-tuning: RL for reasoning agents with AWS Trainium |

### favorite

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CON326 | wed 12-02 | 09:00-10:00 | Caesars Forum | Breakout session | 300 | walk-up | favorite | What's new and what's next for Amazon ECS |

## not yet timed (watch list)

| code | day | time | venue | type | level | seat | topics | title |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACT055-S | tue 12-01 | 18:00-20:00 | tbd | Featured experience | No | walk-up | nvidia | Networking Reception at Delmonico, sponsored by NVIDIA |

## excluded: bedrock and frontier models

kept for the record so nothing gets lost. not planned

| code | day | time | venue | type | level | seat | topics | title | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AIM212 | wed 12-02 | 15:00-16:00 | MGM Grand | Breakout session | 200 | walk-up | (lambda microvms + web functions) | Best practices for production agents on AgentCore, with Nasdaq | bedrock |
| AIM307 | wed 12-02 | 16:30-17:30 | MGM Grand | Breakout session | 300 | walk-up | (lambda microvms + web functions) | Turn your coding agent into an always-on dev team with AgentCore | bedrock |
| AIM206 | thu 12-03 | 10:30-11:30 | Venetian | Breakout session | 200 | walk-up | (nvidia) | AWS AI Factories: Bring production scale AI to your data center | bedrock |
| AIM370 | mon 11-30 | 14:30-15:30 | MGM Grand | Breakout session | 300 | walk-up | (lambda microvms + web functions) | Trusting agents in production: end-to-end security with AgentCore | bedrock |
| AIM368 | mon 11-30 | 11:30-12:30 | MGM Grand | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | How ISVs ship agent products faster: Twilio and Typeform on AgentCore | bedrock |
| COM313 | thu 12-03 | 16:00-17:00 | MGM Grand | Breakout session | 300 | walk-up | (self-managed agents) | Agentic commerce in production: multi-agent orchestration on AgentCore | bedrock |
| COM308 | wed 12-02 | 14:30-15:30 | Caesars Forum | Breakout session | 300 | walk-up | (self-managed agents) | What Building an SRE Agent Taught Us About Agents at Scale | bedrock |
| DAT317 | mon 11-30 | 15:00-16:00 | Caesars Palace | Breakout session | 300 | walk-up | (amazon.com / amazon retail) | A practitioner’s guide to data for agentic AI | bedrock |
| DVT206 | mon 11-30 | 08:30-09:30 | Caesars Forum | Breakout session | 200 | walk-up | amazon.com / amazon retail | 10x or bust: How Amazon's Frontier teams ship with Kiro | frontier |
| IND3348 | thu 12-03 | 10:30-11:30 | Caesars Forum | Breakout session | 300 | walk-up | video games | A Context Gap, Not a Data Gap: Riot Games Rethinks Incident Learning | bedrock |
| IND3302 | mon 11-30 | 14:30-15:30 | Caesars Forum | Breakout session | 300 | walk-up | amazon.com / amazon retail, (self-managed agents) | How Prime Video Built an AI-assisted Creative Suite on AWS | bedrock |
| IND392 | thu 12-03 | 16:00-17:00 | Caesars Forum | Breakout session | 300 | walk-up | video games | From Millions of Gamers to AI at Scale: Roblox's Hybrid AWS Architecture Unleashed | bedrock |
| IND210-S | wed 12-02 | 14:30-15:30 | Wynn/Encore | Breakout session | 200 | walk-up | nvidia | Molecule to Market: Bayer & Capgemini Accelerate Drug Discovery with NVIDIA BioNeMo (sponsored by NVIDIA) | frontier |
| AIM278-S | tue 12-01 | 15:00-16:00 | MGM Grand | Breakout session | 200 | walk-up | (amazon.com / amazon retail) | Open source agent observability and evals with AgentCore and Langfuse (sponsored by ClickHouse) | bedrock |
| AIM251-S | wed 12-02 | 16:00-17:00 | Venetian | Breakout session | 200 | walk-up | databricks, (self-managed agents) | How YipitData Builds AI-Native Analytics with AWS, Databricks, and OpenAI (sponsored by Databricks) | frontier |
| AIM385-S | mon 11-30 | 13:30-14:30 | Wynn/Encore | Breakout session | 300 | walk-up | open-weight models | Small Language Models, Total Control: Sovereign AI Agents, Lower Cost (sponsored by Boomi) | bedrock |
| AIM2209-S | mon 11-30 | 13:30-14:30 | MGM Grand | Breakout session | 200 | walk-up | (self-managed agents) | How Philips accelerated sales quoting with Agentic AI (sponsored by EPAM) | bedrock |
| AIM386-S | mon 11-30 | 12:00-13:00 | Caesars Palace | Breakout session | 300 | walk-up | (self-managed agents), (amazon.com / amazon retail) | Build durable AI agents with AgentCore and Temporal (sponsored by Temporal) | bedrock |
| IND315-R | thu 12-03 | 13:00-14:00 | Caesars Forum | Chalk talk | 300 | reserve | (self-managed agents) | Multi-Agent Operations for Broadcast & Streaming | bedrock |
| AMZ303-R | mon 11-30 | 14:30-15:30 | Caesars Forum | Chalk talk | 300 | reserve | amazon.com / amazon retail | Prime Video Financial Systems on the Road to 10x Velocity with Kiro | bedrock |
| GHJ212 | tue 12-01 | 12:00-14:00 | Caesars Forum | Gamified learning | 200 | reserve | nfl / sports, (self-managed agents) | AWS AI League: Build agents with AgentCore (Agentic Football Cup) | bedrock |
| GHJ308-S-R | mon 11-30 | 14:00-17:00 | Caesars Palace | Gamified learning | 300 | reserve | nvidia | Agentic AI Jam - sponsored by Nvidia | bedrock |
| DAT410-R | wed 12-02 | 13:30-14:30 | MGM Grand | Builders' session | 400 | reserve | (self-managed agents) | Build agentic hybrid retrieval with Amazon Aurora PostgreSQL | bedrock |
| IND401-R | tue 12-01 | 16:00-17:00 | Wynn/Encore | Builders' session | 400 | reserve | (nvidia) | Build, simulate, and validate physical AI-driven robotic systems | bedrock |
| IND303 | tue 12-01 | 12:00-13:00 | Wynn/Encore | Builders' session | 300 | reserve | (self-managed agents) | Build multi-agent warranty and repair intelligence for automotive | bedrock |
| IND352-R | mon 11-30 | 11:30-12:30 | Wynn/Encore | Builders' session | 300 | reserve | (self-managed agents) | Gotta detect 'em all: finding rogue devices with Amazon Bedrock | bedrock |
| IND351 | mon 11-30 | 11:30-12:30 | Caesars Forum | Builders' session | 300 | reserve | video games | Breathing Life into Game Worlds with Amazon Neptune & GraphRAG | bedrock |
| IND420-R | mon 11-30 | 10:00-11:00 | Caesars Forum | Builders' session | 400 | reserve | (self-managed agents) | Build Agentic Video Streaming Observability Using Kiro and Bedrock | bedrock |
| OPN309 | tue 12-01 | 14:30-15:30 | Caesars Forum | Builders' session | 300 | reserve | self-managed agents | Defense in depth for Strands AI agents with Cedar, AgentCore, and Rex | bedrock |
| ARC324 | mon 11-30 | 15:00-16:00 | MGM Grand | Chalk talk | 300 | reserve | favorite | Ambient accessibility: Architecting real-time ASL on a Wearable | bedrock |
| ARC204 | mon 11-30 | 13:30-14:30 | Wynn/Encore | Chalk talk | 200 | reserve | (amazon.com / amazon retail) | Architectural patterns for predictable multi-agent costs at scale | bedrock |
| AIM436-R | mon 11-30 | 10:00-11:00 | MGM Grand | Chalk talk | 400 | reserve | (lambda microvms + web functions) | Scale production agents reliably with AgentCore | bedrock |
| AIM364-R | tue 12-01 | 13:30-14:30 | MGM Grand | Chalk talk | 300 | reserve | (open-weight models) | Architect for production AI: A decision framework that scales | bedrock |
| AIM451 | wed 12-02 | 12:00-13:00 | MGM Grand | Chalk talk | 400 | reserve | (self-managed agents) | Automated Reasoning as Agent Guardrails | bedrock |
| COM321-R | mon 11-30 | 15:00-16:00 | Caesars Forum | Chalk talk | 300 | reserve | self-managed agents, (lambda microvms + web functions) | The Agent Harness You Own on AWS for Regulated Industries | bedrock |
| DAT307-R | wed 12-02 | 11:30-12:30 | MGM Grand | Chalk talk | 300 | reserve | (self-managed agents) | Build stateful agentic AI workflows with Aurora, MCP, and AgentCore | bedrock |
| IND356-R | thu 12-03 | 08:30-09:30 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents), (amazon.com / amazon retail) | From static to self-improving agents with Amazon Bedrock AgentCore | bedrock |
| IND362-R | thu 12-03 | 09:00-10:00 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Agentic commerce: shopping assistants to agent-ready infrastructure | bedrock |
| IND3338 | mon 11-30 | 10:00-11:00 | Wynn/Encore | Chalk talk | 300 | reserve | nvidia | Accelerate Physical AI development with NVIDIA on AWS | bedrock |
| IND3317 | mon 11-30 | 08:30-09:30 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents) | Ontology-Powered AI Agents: Verifiable Decisions Across Manufacturing | bedrock |
| IND375 | thu 12-03 | 11:30-12:30 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents) | Emerging multi-agent patterns for complex financial workflows | bedrock |
| MAM301 | mon 11-30 | 16:30-17:30 | Caesars Palace | Chalk talk | 300 | reserve | (databricks) | From SAP to Agentic AI: Building a unified data strategy on AWS | bedrock |
| PEX304-R | tue 12-01 | 15:00-16:00 | Caesars Forum | Builders' session | 300 | reserve | (self-managed agents) | How to Build Autonomous Enterprise Agents with SOPs using Kiro and Bedrock AgentCore | bedrock |
| SVS323-R | mon 11-30 | 12:00-13:00 | Caesars Forum | Chalk talk | 300 | reserve | lambda microvms + web functions | Orchestrating agentic workflows: Step Functions & durable functions | bedrock |
| AIM333-R | thu 12-03 | 09:00-10:00 | MGM Grand | Code talk | 300 | reserve | self-managed agents, (lambda microvms + web functions) | The Agent Harness: Unifying Fragmented Tools for Mission AI Advisors | bedrock |
| COP401-R | mon 11-30 | 16:30-17:30 | Caesars Forum | Code talk | 400 | reserve | (self-managed agents) | Building eval-driven observability for AI agents | bedrock |
| COP404 | fri 12-04 | 10:30-11:30 | Wynn/Encore | Code talk | 400 | reserve | self-managed agents | Go headless: managed harness to custom DevOps orchestration | bedrock |
| COM317-R | thu 12-03 | 12:00-13:00 | Caesars Forum | Code talk | 300 | reserve | self-managed agents | Ship Reliable AI Agents with Strands Evaluation and AgentCore Evaluations | bedrock |
| COM324-R | wed 12-02 | 15:00-16:00 | Caesars Forum | Code talk | 300 | reserve | (self-managed agents) | Pit Crew AI: Building Multi-Agent Cloud Operations on AWS | bedrock |
| COM325-R | thu 12-03 | 15:00-16:00 | Caesars Forum | Code talk | 300 | reserve | (lambda microvms + web functions) | The agent orchestration spectrum: Agents, Step Functions, or Lambda? | bedrock |
| MAM412 | mon 11-30 | 16:00-17:00 | Caesars Palace | Code talk | 400 | reserve | (self-managed agents) | Secure and modernize code simultaneously with agentic AI | bedrock |
| SEC382 | thu 12-03 | 11:30-12:30 | Wynn/Encore | Code talk | 300 | reserve | (open-weight models) | Mitigating prompt injection with structured outputs in Amazon Bedrock | bedrock |
| GHJ308-S-R1 | wed 12-02 | 09:00-12:00 | Caesars Palace | Gamified learning | 300 | reserve | nvidia | Agentic AI Jam - sponsored by Nvidia | bedrock |
| COM339 | tue 12-01 | 17:00-17:20 | Venetian | Lightning talk | 300 | walk-up | (self-managed agents) | Cocktails to Code Building AI Bartenders with Amazon Bedrock | bedrock |
| COM340 | wed 12-02 | 12:30-12:50 | Wynn/Encore | Lightning talk | 300 | walk-up | lambda microvms + web functions, (self-managed agents) | Lambda MicroVMs: The Missing Serverless Primitive for Multi-Tenant Agents | bedrock |
| NET219 | mon 11-30 | 13:30-13:50 | Wynn/Encore | Lightning talk | 200 | walk-up | (amazon.com / amazon retail) | Private AI agent egress: VPC Lattice meets AgentCore Gateway | bedrock |
| DVT215-S | tue 12-01 | 13:00-13:20 | Venetian | Lightning talk | 200 | walk-up | (amazon.com / amazon retail) | The Best Engineer in the Room Doesn’t Write Code (sponsored by Anaconda) | bedrock |
| IND104-S | thu 12-03 | 12:00-12:20 | Venetian | Lightning talk | 100 | walk-up | (amazon.com / amazon retail) | Building the Construction Cloud: How Procore AI &Amazon Bedrock Power the Built World (sponsored by Procore) | bedrock |
| AIM2206-S | wed 12-02 | 12:00-12:20 | Venetian | Lightning talk | 200 | walk-up | (amazon.com / amazon retail) | Beyond the Build: Scaling and Governing AI Agents with Dataiku and Amazon Bedrock (sponsored by Dataiku) | bedrock |
| AIM284-S | thu 12-03 | 14:00-14:20 | Venetian | Lightning talk | 200 | walk-up | (open-weight models) | Tokenomics for AI on AWS: Local inference plus Amazon Bedrock (sponsored by Spectro Cloud) | bedrock |
| AIM388-S | tue 12-01 | 12:00-12:20 | Venetian | Lightning talk | 300 | walk-up | (self-managed agents), (amazon.com / amazon retail) | AWSome Automation: From Project Brief Prompt to Landing Page (sponsored by Storyblok) | bedrock |
| BIZ328-S | tue 12-01 | 11:00-11:20 | Venetian | Lightning talk | 300 | walk-up | nvidia | Build It, Govern It, Ship It: CI/CD for AI Agents with the NVIDIA Agent Toolkit (sponsored by NVIDIA) | bedrock |
| AIM439-R | mon 11-30 | 08:30-10:30 | MGM Grand | Workshop | 400 | reserve | (self-managed agents) | Getting Started with AgentCore: ship an agent to production in 2 hours | bedrock |
| AIM416-R | thu 12-03 | 12:30-14:30 | MGM Grand | Workshop | 400 | reserve | (lambda microvms + web functions) | Scale your coding agents beyond the laptop with AgentCore | bedrock |
| AIM419-R | thu 12-03 | 12:30-14:30 | MGM Grand | Workshop | 400 | reserve | (self-managed agents), (lambda microvms + web functions) | Build and deploy agents to Lambda and EKS with Amazon Bedrock | bedrock |
| CON320-R | wed 12-02 | 15:30-17:30 | Caesars Forum | Workshop | 300 | reserve | self-managed agents | Building and securing AI agents on Amazon EKS | bedrock |
| DAT416-R | mon 11-30 | 08:00-10:00 | MGM Grand | Workshop | 400 | reserve | (self-managed agents) | Build governed agentic AI search with Aurora, RDS, & Bedrock AgentCore | bedrock |
| HMC402-R | thu 12-03 | 15:00-17:00 | Caesars Palace | Workshop | 400 | reserve | (self-managed agents) | Implementing agentic AI solutions on-premises and at the edge | bedrock |
| IND403 | thu 12-03 | 08:00-10:00 | Caesars Forum | Workshop | 400 | reserve | self-managed agents | Build a Video Semantic Layer for Media Agent and Agent Harness on AWS | bedrock |
| IND321 | mon 11-30 | 12:30-14:30 | Caesars Forum | Workshop | 300 | reserve | (self-managed agents) | Telecom NOC operations: Automating incident response with AI agents | bedrock |
| IND327-R | mon 11-30 | 08:00-10:00 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Build self-healing agents from diagnosis to disaster recovery | bedrock |
| IND329-R | thu 12-03 | 08:30-10:30 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Build a multi-agent system for hyper-personalized customer journeys | bedrock |
| IND370 | thu 12-03 | 08:30-10:30 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Production Agentic Trading: Build the pipeline Moeve runs on AgentCore | bedrock |
| MAM333 | mon 11-30 | 12:00-14:00 | Caesars Palace | Workshop | 300 | reserve | (databricks) | Unlocking SAP Data with AI: From Zero-ETL to Agentic Automation | bedrock |
| SEC362 | thu 12-03 | 08:00-10:00 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Authentication, authorization, and audit for agentic AI on AWS | bedrock |
| BIZ329-S | tue 12-01 | 12:00-14:00 | MGM Grand | Workshop | 300 | reserve | nvidia, (self-managed agents) | Build, Govern, Optimize: Trustworthy, Cost-Aware Agents with the NVIDIA Agent Toolkit (sponsored by NVIDIA) | bedrock |
| TNC304 | tue 12-01 | 13:00-15:00 | Caesars Palace | Bootcamp | 300 | reserve | (lambda microvms + web functions) | AWS Partner: Build AI workflows that laugh in the face of disruption | bedrock |
| TNC326-R | tue 12-01 | 08:30-12:30 | Caesars Palace | Bootcamp | 300 | reserve | (self-managed agents) | AWS Partner: Ship an AI agent without crossing your fingers | bedrock |
| TNC326-R1 | thu 12-03 | 08:30-12:30 | Caesars Palace | Bootcamp | 300 | reserve | (self-managed agents) | AWS Partner: Ship an AI agent without crossing your fingers | bedrock |
| TNC213-R | mon 11-30 | 08:00-10:00 | Caesars Palace | Exam prep | 200 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified AI Practitioner | bedrock |
| TNC216 | tue 12-01 | 13:30-15:00 | Caesars Palace | Lab | 200 | reserve | (self-managed agents) | Building an AI Travel Assistant with AgentCore Gateway | bedrock |
| TNC323-R | tue 12-01 | 15:30-17:30 | Caesars Palace | Lab | 300 | reserve | (self-managed agents) | Deploying a Fitness App from Specs with Kiro and AgentCore | bedrock |
| TNC220-R | mon 11-30 | 10:30-11:30 | Caesars Palace | Lab | 200 | reserve | (self-managed agents) | Go from Code to Deployed Agent with AgentCore CLI | bedrock |
| TNC220-R1 | wed 12-02 | 12:00-13:00 | Caesars Palace | Lab | 200 | reserve | (self-managed agents) | Go from Code to Deployed Agent with AgentCore CLI | bedrock |
| TNC323-R1 | thu 12-03 | 15:00-17:00 | Caesars Palace | Lab | 300 | reserve | (self-managed agents) | Deploying a Fitness App from Specs with Kiro and AgentCore | bedrock |
| DVT337-R | thu 12-03 | 11:30-12:30 | Caesars Forum | Builders' session | 300 | reserve | self-managed agents | Build a SaaS control plane with Kiro specs and Strands multi-tenant constructs | bedrock |
| AIM456 | mon 11-30 | 15:00-17:00 | MGM Grand | Workshop | 400 | reserve | (open-weight models) | Foundational Model Ops with Amazon SageMaker AI and Amazon Bedrock | bedrock |
| TNC213-R1 | wed 12-02 | 12:00-14:00 | Caesars Palace | Exam prep | 200 | reserve | (video games) | AWS Escape Room: Exam Prep for AWS Certified AI Practitioner | bedrock |
| DAT416-R1 | wed 12-02 | 08:00-10:00 | MGM Grand | Workshop | 400 | reserve | (self-managed agents) | Build governed agentic AI search with Aurora, RDS, & Bedrock AgentCore | bedrock |
| COM321-R1 | thu 12-03 | 14:30-15:30 | Wynn/Encore | Chalk talk | 300 | reserve | self-managed agents, (lambda microvms + web functions) | The Agent Harness You Own on AWS for Regulated Industries | bedrock |
| DAT307-R1 | tue 12-01 | 11:30-12:30 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents) | Build stateful agentic AI workflows with Aurora, MCP, and AgentCore | bedrock |
| AMZ303-R1 | wed 12-02 | 15:00-16:00 | Caesars Palace | Chalk talk | 300 | reserve | amazon.com / amazon retail | Prime Video Financial Systems on the Road to 10x Velocity with Kiro | bedrock |
| DAT307-R2 | mon 11-30 | 12:00-13:00 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents) | Build stateful agentic AI workflows with Aurora, MCP, and AgentCore | bedrock |
| DVT337-R1 | mon 11-30 | 13:30-14:30 | MGM Grand | Builders' session | 300 | reserve | self-managed agents | Build a SaaS control plane with Kiro specs and Strands multi-tenant constructs | bedrock |
| IND362-R1 | tue 12-01 | 13:30-14:30 | Caesars Forum | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Agentic commerce: shopping assistants to agent-ready infrastructure | bedrock |
| SVS323-R1 | wed 12-02 | 10:00-11:00 | Caesars Forum | Chalk talk | 300 | reserve | lambda microvms + web functions | Orchestrating agentic workflows: Step Functions & durable functions | bedrock |
| AIM436-R1 | wed 12-02 | 15:00-16:00 | Wynn/Encore | Chalk talk | 400 | reserve | (lambda microvms + web functions) | Scale production agents reliably with AgentCore | bedrock |
| AIM439-R1 | wed 12-02 | 08:00-10:00 | Wynn/Encore | Workshop | 400 | reserve | (self-managed agents) | Getting Started with AgentCore: ship an agent to production in 2 hours | bedrock |
| CON320-R1 | thu 12-03 | 15:30-17:30 | MGM Grand | Workshop | 300 | reserve | self-managed agents | Building and securing AI agents on Amazon EKS | bedrock |
| COM317-R1 | tue 12-01 | 13:00-14:00 | Wynn/Encore | Code talk | 300 | reserve | self-managed agents | Ship Reliable AI Agents with Strands Evaluation and AgentCore Evaluations | bedrock |
| IND420-R1 | wed 12-02 | 15:00-16:00 | Caesars Forum | Builders' session | 400 | reserve | (self-managed agents) | Build Agentic Video Streaming Observability Using Kiro and Bedrock | bedrock |
| AIM333-R1 | wed 12-02 | 11:30-12:30 | Caesars Palace | Code talk | 300 | reserve | self-managed agents, (lambda microvms + web functions) | The Agent Harness: Unifying Fragmented Tools for Mission AI Advisors | bedrock |
| IND327-R1 | tue 12-01 | 12:00-14:00 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Build self-healing agents from diagnosis to disaster recovery | bedrock |
| HMC402-R1 | wed 12-02 | 15:30-17:30 | Wynn/Encore | Workshop | 400 | reserve | (self-managed agents) | Implementing agentic AI solutions on-premises and at the edge | bedrock |
| PEX304-R1 | wed 12-02 | 09:00-10:00 | MGM Grand | Builders' session | 300 | reserve | (self-managed agents) | How to Build Autonomous Enterprise Agents with SOPs using Kiro and Bedrock AgentCore | bedrock |
| COM325-R1 | wed 12-02 | 11:30-12:30 | Wynn/Encore | Code talk | 300 | reserve | (lambda microvms + web functions) | The agent orchestration spectrum: Agents, Step Functions, or Lambda? | bedrock |
| IND356-R1 | mon 11-30 | 16:00-17:00 | Wynn/Encore | Chalk talk | 300 | reserve | (self-managed agents), (amazon.com / amazon retail) | From static to self-improving agents with Amazon Bedrock AgentCore | bedrock |
| AIM416-R1 | wed 12-02 | 15:30-17:30 | MGM Grand | Workshop | 400 | reserve | (lambda microvms + web functions) | Scale your coding agents beyond the laptop with AgentCore | bedrock |
| COM324-R1 | thu 12-03 | 11:30-12:30 | Caesars Palace | Code talk | 300 | reserve | (self-managed agents) | Pit Crew AI: Building Multi-Agent Cloud Operations on AWS | bedrock |
| IND401-R1 | wed 12-02 | 09:00-10:00 | Wynn/Encore | Builders' session | 400 | reserve | (nvidia) | Build, simulate, and validate physical AI-driven robotic systems | bedrock |
| AIM419-R1 | wed 12-02 | 15:30-17:30 | MGM Grand | Workshop | 400 | reserve | (self-managed agents), (lambda microvms + web functions) | Build and deploy agents to Lambda and EKS with Amazon Bedrock | bedrock |
| IND329-R1 | mon 11-30 | 08:30-10:30 | Wynn/Encore | Workshop | 300 | reserve | (self-managed agents) | Build a multi-agent system for hyper-personalized customer journeys | bedrock |
| DAT410-R1 | mon 11-30 | 16:00-17:00 | MGM Grand | Builders' session | 400 | reserve | (self-managed agents) | Build agentic hybrid retrieval with Amazon Aurora PostgreSQL | bedrock |
| COP401-R1 | wed 12-02 | 15:00-16:00 | Wynn/Encore | Code talk | 400 | reserve | (self-managed agents) | Building eval-driven observability for AI agents | bedrock |
| IND315-R1 | tue 12-01 | 12:00-13:00 | Caesars Forum | Chalk talk | 300 | reserve | (self-managed agents) | Multi-Agent Operations for Broadcast & Streaming | bedrock |
| IND3354 | tue 12-01 | 16:00-17:00 | Wynn/Encore | Chalk talk | 300 | reserve | (amazon.com / amazon retail) | Lives on the Line: Modernizing National Weather Forecasting on AWS | bedrock |
