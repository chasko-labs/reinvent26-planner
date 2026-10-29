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
| ---- | --- | ---- | ----- | ---- | ----- | ---- | ------ | ----- |

## schedule

### mon 11-30

| code      | day       | time        | venue     | type       | level | seat     | topics                       | title                                                                |
| --------- | --------- | ----------- | --------- | ---------- | ----- | -------- | ---------------------------- | -------------------------------------------------------------------- |
| STG363    | mon 11-30 | 08:30-09:30 | MGM Grand | Chalk talk | 300   | RESERVED | (amazon.com / amazon retail) | Modernizing VMware workloads with Amazon FSx for NetApp ONTAP        |
| INV530-R1 | mon 11-30 | 11:30-12:30 | MGM Grand | Chalk talk | 500   | RESERVED |                              | EC2 at 20: Rebuilding the control plane while it is running          |
| CMP340    | mon 11-30 | 13:00-14:00 | MGM Grand | Chalk talk | 300   | RESERVED | amazon braket                | Drug discovery and materials use cases with Amazon Braket and Q-CTRL |
| AIM433    | mon 11-30 | 15:00-16:00 | MGM Grand | Chalk talk | 400   | RESERVED |                              | Maximize GPU utilization across training and inference on HyperPod   |
| STG338-R  | mon 11-30 | 16:30-17:30 | MGM Grand | Chalk talk | 300   | RESERVED |                              | Simplify secure file sharing with Transfer Family no-code web apps   |

### tue 12-01

| code       | day       | time        | venue         | type       | level | seat     | topics | title                                                        |
| ---------- | --------- | ----------- | ------------- | ---------- | ----- | -------- | ------ | ------------------------------------------------------------ |
| IND359-R1  | tue 12-01 | 12:00-13:00 | Wynn/Encore   | Chalk talk | 300   | RESERVED |        | In-Country HPC: How TGS Processes Seismic Data on AWS Brazil |
| IND322-R   | tue 12-01 | 15:00-16:00 | Caesars Forum | Chalk talk | 300   | RESERVED |        | Physical AI in Telecom: A Framework for Workload Placement   |
| IND3304-R1 | tue 12-01 | 16:30-17:30 | Caesars Forum | Chalk talk | 300   | RESERVED |        | KNFSD File Cache: Extending Your NFS Storage into the Cloud  |

### wed 12-02

| code      | day       | time        | venue         | type       | level | seat     | topics | title                                                                           |
| --------- | --------- | ----------- | ------------- | ---------- | ----- | -------- | ------ | ------------------------------------------------------------------------------- |
| ANT402-R  | wed 12-02 | 08:00-10:00 | MGM Grand     | Workshop   | 400   | RESERVED |        | Reduce spend and data movement with Amazon Redshift Data Sharing and Graviton   |
| INV537    | wed 12-02 | 13:30-14:30 | Caesars Forum | Chalk talk | 500   | RESERVED |        | No torque sensors, no problem: learning safe physical interaction for humanoids |
| AIM434-R1 | wed 12-02 | 15:30-17:30 | MGM Grand     | Workshop   | 400   | RESERVED |        | From raw data to custom model: Dataset prep with Amazon SageMaker AI            |

### thu 12-03

| code   | day       | time        | venue          | type     | level | seat     | topics      | title                                                                  |
| ------ | --------- | ----------- | -------------- | -------- | ----- | -------- | ----------- | ---------------------------------------------------------------------- |
| STG412 | thu 12-03 | 08:00-10:00 | MGM Grand      | Workshop | 400   | RESERVED |             | Find and fix storage bottlenecks for self-managed OLTP on EC2 with EBS |
| SEC401 | thu 12-03 | 12:00-14:00 | Wynn/Encore    | Workshop | 400   | RESERVED | video games | Winning the DDoS Game: defend your app under real-time attack          |
| MAM416 | thu 12-03 | 15:30-17:30 | Caesars Palace | Workshop | 400   | RESERVED |             | Free your .NET app from Windows licensing with AI-powered portability  |

### fri 12-04

| code      | day       | time        | venue       | type     | level | seat     | topics | title                                                                           |
| --------- | --------- | ----------- | ----------- | -------- | ----- | -------- | ------ | ------------------------------------------------------------------------------- |
| BIZ321-R1 | fri 12-04 | 08:00-10:00 | Wynn/Encore | Workshop | 300   | RESERVED |        | Never Start Over: Chat to Co-Browse, Voice and Video on Amazon Connect Customer |

totals: 15 sessions, 21h00 reserved-seat time, 0h00 walk-up time

## would love to attend but not conducive to logistics

every topic session that did not fit, so teammates can see the interest and cover it or flag a swap

### nvidia

| code   | day       | time        | venue     | type       | level | seat                   | topics | title                                                                  |
| ------ | --------- | ----------- | --------- | ---------- | ----- | ---------------------- | ------ | ---------------------------------------------------------------------- |
| CMP408 | mon 11-30 | 13:30-14:30 | MGM Grand | Chalk talk | 400   | reserve (very limited) | nvidia | The cloud holodeck: Stream NVIDIA Omniverse, scale headless sim on AWS |

### amazon.com / amazon retail

| code   | day       | time        | venue         | type       | level | seat                   | topics                       | title                                                              |
| ------ | --------- | ----------- | ------------- | ---------- | ----- | ---------------------- | ---------------------------- | ------------------------------------------------------------------ |
| IND366 | mon 11-30 | 09:00-10:00 | Caesars Forum | Chalk talk | 300   | reserve (very limited) | (amazon.com / amazon retail) | Zero-Shot Demand Forecasting with Chronos 2, SMUS, and Quick Suite |

### open-weight models

| code    | day       | time        | venue     | type     | level | seat                   | topics               | title                                    |
| ------- | --------- | ----------- | --------- | -------- | ----- | ---------------------- | -------------------- | ---------------------------------------- |
| AIM3304 | wed 12-02 | 15:00-17:00 | MGM Grand | Workshop | 300   | reserve (very limited) | (open-weight models) | Evaluate, select, optimize your AI model |

## excluded: bedrock and frontier models

kept for the record so nothing gets lost. not planned

| code | day | time | venue | type | level | seat | topics | title | reason |
| ---- | --- | ---- | ----- | ---- | ----- | ---- | ------ | ----- | ------ |
