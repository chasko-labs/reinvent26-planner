# drop review 2026-11-04: questionable holds and same-window alternatives

live seats checked 2026-11-04 ~22:40 UTC. read-only: nothing was
reserved, cancelled, or favorited to produce this list. "full" below
means the API returned no bookable seat band at check time; seats move,
so recheck with `fill --dry-run` before acting on any line here.

method: all 14 held seats were tagged against the tracked topics in
`data/reinvent2026/map-config.json`. holds with no core topic are
listed. for each, the catalog was searched for same-day overlapping
sessions, repeats of held seats excluded, bedrock and frontier models
excluded, and live seats read. `FAV` means you already favorited it.

## monday 11-30

### held STG363, 08:30-09:30, vmware on FSx. no core topic

- FAV CMP321-R, 08:30-10:30, MGM, agents on EKS. seat: full.
- SVS347-R, 09:00-10:00, Forum, lambda web apps. seat: full.
- AIM404-R, 08:30-10:30, MGM, inference endpoints. seat: full.
- AIM406, 08:30-10:30, MGM, more SageMaker pipelines. seat: full.
- verdict: nothing open. the agent-flavored backup is already favorited.

### held INV530-R1, 11:30-12:30, EC2 control plane. no core topic

- FAV AIM407-R, 12:00-13:00, MGM, multi-agent with Strands. seat: full.
- FAV CMP328-R, 12:00-13:00, MGM, agent sandboxes on EC2. seat: full.
- AIM449, 12:00-13:00, MGM, physical AI with Strands. seat: full.
- ARC307, 12:00-14:00, Wynn, resilience assessment. seat: full.
- verdict: nothing open. two agent backups already favorited.

### held CMP340, 13:00-14:00, braket drug discovery. core: braket

on-lens. not questionable; listed so the day reads complete.
backup already favorited: AIM312-R (RL reasoning agents). seat: full.

### held AIM318, 15:00-17:00, SageMaker HyperPod VLM training. no core topic

- FAV NET337, 15:00-16:00, MGM, Leo satellite. seat: full.
- SVS203-R, 15:00-16:00, Forum, lambda web apps. seat: full.
- COM326, 15:00-16:00, Forum, observable agents. seat: full.
- HMC401-R1, 14:30-15:30, Wynn, GPU orchestration. seat: full.
- verdict: nothing open. this is the weakest Monday hold and there
  is nowhere to move today.

## tuesday 12-01

### held IND359-R1, 12:00-13:00, seismic HPC on AWS Brazil. no core topic

- FAV HMC403-R1, 12:30-14:30, MGM, self-managed agents. seat: full.
- SVS325-R, 12:00-13:00, Forum, step functions. seat: full.
- AIM218, 12:00-13:00, MGM, Nova Sonic. seat: full.
- AMZ304, 12:00-13:00, Forum, twitch demos. seat: full.
- verdict: nothing open. the agent backup is already favorited.

### held IND322-R, 15:00-16:00, physical AI telecom. no core topic

- FAV OPN406-R1, 14:30-15:30, MGM, Strands cost cutting. seat: full.
- AIM357, 15:00-17:00, MGM, Nova embeddings. seat: full.
- SVS203-R1, 14:30-15:30, MGM, lambda web apps. seat: full.
- AIM362, 14:30-15:30, MGM, customization compute. seat: full.
- verdict: nothing open.

### held IND3304-R1, 16:30-17:30, KNFSD file cache. no core topic

- COM329, 16:30-17:30, Forum, sandboxing agents on EKS. seat: full.
- SVS333-R1, 16:30-17:30, Wynn, lambda microvms. seat: full.
- AIM357, 15:00-17:00, MGM, Nova embeddings. seat: full.
- AIM354, 16:00-17:00, MGM, Nova voice agents. seat: full.
- verdict: nothing open. COM329 is the on-brand swap to watch.

## wednesday 12-02

### held ANT402-R, 08:00-10:00, Redshift data sharing. no core topic

- INV518, 08:30-09:30, MGM, quantum error correction. seat: full.
- FAV IND3351, 08:30-09:30, Forum, Leo (seat field missing).
- DAT429, 08:00-10:00, MGM, agentic AI on Aurora/DynamoDB. seat: full.
- SVS325-R1, 08:30-09:30, Caesars Palace, step functions. seat: full.
- verdict: nothing open.

### held INV537, 13:30-14:30, humanoid robots. no core topic

- OPN304-R, 12:30-14:30, Forum, agent observability. seat: full.
- OPN307-R, 12:30-14:30, Forum, Strands multi-agent. seat: full.
- FAV AIM407-R1, 13:30-14:30, MGM, Strands multi-agent. seat: full.
- AIM458-S, 12:30-14:30, MGM, physical AI blueprint. seat: full.
- verdict: nothing open. two Strands backups already favorited.

### held AIM434-R1, 15:30-17:30, SageMaker dataset prep. no core topic

- AIM389-S, 15:00-17:00, MGM, NVIDIA open models on SageMaker. seat: full.
- AIM352, 16:00-17:00, Forum, Nova voice agent. seat: full.
- HMC401-R, 16:00-17:00, MGM, GPU orchestration. seat: full.
- GHJ213, 16:00-17:30, MGM, AI League finale (seat field missing).
- verdict: nothing open. the second SageMaker hold with no exit today.

## thursday 12-03

### held STG412, 08:00-10:00, self-managed OLTP on EC2/EBS. tagger: no core topic, human: on-brand

keep. the tagger matches keywords, and "self-managed OLTP" is not an
agent session — but it is your lens minute for minute.

- FAV HMC403-R, 08:30-10:30, MGM, self-managed agents. seat: full.
- FAV AIM402, 08:00-10:00, MGM, SageMaker fine-tuning. seat: full.
- CMP402, 08:30-10:30, MGM, hybrid quantum. seat: full.
- AIM338-R, 08:30-09:30, MGM, open weights. seat: full.
- verdict: keep the hold. the SageMaker favorite is the clash noise
  from yesterday; drop it or keep it as a no-cost backup.

### held SEC401, 12:00-14:00, DDoS defense. tagger says video games; really security, off-lens

- FAV CMP321-R1, 13:00-14:00, MGM, agentic AI on EKS. seat: full.
- SVS401-R, 12:00-14:00, Forum, durable-function agents. seat: full.
- FAV CMP328-R1, 13:30-14:30, MGM, agent sandboxes. seat: full.
- CMP310, 11:30-12:30, MGM, quantum chemistry. seat: full.
- verdict: nothing open. agent backups already favorited on both sides.

### held MAM416, 15:30-17:30, .NET licensing. no core topic

- OPN304-R1, 15:00-17:00, Wynn, agent observability. seat: full.
- OPN307-R1, 15:00-17:00, MGM, Strands multi-agent. seat: full.
- FAV OPN312, 15:00-16:00, Forum, Hugging Face at scale. seat: full.
- FAV CMP318-R, 15:00-17:00, MGM, agent CI/CD on EC2 Mac. seat: full.
- verdict: nothing open. the most off-brand hold on the week, and
  the two best swaps are already favorited.

## friday 12-04

### held BIZ321-R1, 08:00-10:00, Connect chat/voice/video. no core topic

- FAV CMP318-R1, 08:00-10:00, Wynn, agent CI/CD. seat: full.
- CMP314-R1, 08:00-10:00, Wynn, EKS performance. seat: full.
- BIZ322-R1, 08:00-10:00, Wynn, self-healing frameworks. seat: full.
- CON301-R1, 08:00-10:00, Wynn, EKS auto mode. seat: full.
- verdict: nothing open. same-venue agent backup already favorited.

## bottom line

13 of 14 holds carry no core topic; the 14th is braket. the tagger
is keyword-narrow (it misses self-managed OLTP), so human judgment
keeps STG412 aggressively. everywhere else the story is the same:
the on-brand swap is either already favorited or full. no held seat
has a bookable exit right now. recheck with `fill --dry-run`; the
morning watcher report flags the moment that changes.
