# Kalaxy3 Cost Model Architecture and FinOps Analysis

## Document purpose

This research document defines what Kalaxy3 should be able to accomplish by
building a cost model around its Kubecost installation, how that model should
work, what data it requires, how it should compare Kalaxy3 with AWS, and how it
can show the impact of individual projects on the cost and capacity of the
cluster.

It combines:

- the verified Kalaxy3 architecture and Kubecost deployment;
- the OpenCost cost-allocation model used by Kubecost;
- the AWS Well-Architected Framework;
- the AWS Cloud Adoption Framework;
- AWS cost-allocation and pricing practices;
- software-architecture and FinOps principles;
- a nontechnical explanation for readers who do not operate Kubernetes.

This is a research and design document. It does not assert that the current
Kubecost installation already contains every cost required for a complete
Kalaxy3 total-cost-of-ownership model.

## Table of contents

- [Executive summary](#executive-summary)
- [Research basis](#research-basis)
- [Current Kalaxy3 cost architecture](#current-kalaxy3-cost-architecture)
  - [Relevant Kalaxy3 components](#relevant-kalaxy3-components)
  - [What Kubecost currently provides](#what-kubecost-currently-provides)
  - [What Kubecost does not provide by itself](#what-kubecost-does-not-provide-by-itself)
- [What the Kalaxy3 cost model should accomplish](#what-the-kalaxy3-cost-model-should-accomplish)
  - [Measure total cost of ownership](#measure-total-cost-of-ownership)
  - [Measure project and workload impact](#measure-project-and-workload-impact)
  - [Compare Kalaxy3 with AWS](#compare-kalaxy3-with-aws)
  - [Support capacity and investment decisions](#support-capacity-and-investment-decisions)
  - [Support showback and chargeback](#support-showback-and-chargeback)
  - [Measure unit economics](#measure-unit-economics)
  - [Identify waste and optimization opportunities](#identify-waste-and-optimization-opportunities)
  - [Quantify business and engineering value](#quantify-business-and-engineering-value)
- [Cost model principles](#cost-model-principles)
  - [Separate cost from price](#separate-cost-from-price)
  - [Separate fixed variable direct shared idle and overhead costs](#separate-fixed-variable-direct-shared-idle-and-overhead-costs)
  - [Maintain actual forecast and comparison views](#maintain-actual-forecast-and-comparison-views)
  - [Compare equivalent outcomes rather than isolated resources](#compare-equivalent-outcomes-rather-than-isolated-resources)
  - [Preserve traceability](#preserve-traceability)
- [Proposed Kalaxy3 cost taxonomy](#proposed-kalaxy3-cost-taxonomy)
  - [Compute](#compute)
  - [GPU and accelerated computing](#gpu-and-accelerated-computing)
  - [Longhorn block storage](#longhorn-block-storage)
  - [NFS shared storage](#nfs-shared-storage)
  - [MinIO object storage](#minio-object-storage)
  - [Network and ingress](#network-and-ingress)
  - [Control plane and shared platform services](#control-plane-and-shared-platform-services)
  - [Power cooling UPS and facilities](#power-cooling-ups-and-facilities)
  - [Operations labor and engineering effort](#operations-labor-and-engineering-effort)
  - [Maintenance replacement backup and risk](#maintenance-replacement-backup-and-risk)
- [Project allocation architecture](#project-allocation-architecture)
  - [Required Kubernetes metadata](#required-kubernetes-metadata)
  - [Recommended label dictionary](#recommended-label-dictionary)
  - [Namespace policy](#namespace-policy)
  - [Direct cost allocation](#direct-cost-allocation)
  - [Shared platform cost allocation](#shared-platform-cost-allocation)
  - [Idle cost policy](#idle-cost-policy)
  - [Storage replication policy](#storage-replication-policy)
  - [Project lifecycle policy](#project-lifecycle-policy)
- [Data required for the Kalaxy3 model](#data-required-for-the-kalaxy3-model)
  - [Kubecost and Kubernetes allocation data](#kubecost-and-kubernetes-allocation-data)
  - [Prometheus operational telemetry](#prometheus-operational-telemetry)
  - [Hardware inventory and purchase data](#hardware-inventory-and-purchase-data)
  - [Power and electricity data](#power-and-electricity-data)
  - [Storage data](#storage-data)
  - [Network data](#network-data)
  - [Operations and labor data](#operations-and-labor-data)
  - [Project and business metadata](#project-and-business-metadata)
  - [AWS comparison data](#aws-comparison-data)
- [Proposed analytical data model](#proposed-analytical-data-model)
  - [Core dimensions](#core-dimensions)
  - [Core fact tables](#core-fact-tables)
  - [Data retention and granularity](#data-retention-and-granularity)
  - [Data flow](#data-flow)
- [Cost formulas](#cost-formulas)
  - [Hardware depreciation](#hardware-depreciation)
  - [Power](#power)
  - [Node cost](#node-cost)
  - [CPU memory and GPU rates](#cpu-memory-and-gpu-rates)
  - [Storage](#storage)
  - [Project cost](#project-cost)
  - [Marginal cost](#marginal-cost)
  - [Avoided AWS cost](#avoided-aws-cost)
- [AWS comparison methodology](#aws-comparison-methodology)
  - [Comparison scenarios](#comparison-scenarios)
  - [Kalaxy3 to AWS service mapping](#kalaxy3-to-aws-service-mapping)
  - [AWS cost inputs](#aws-cost-inputs)
  - [Normalize nonprice differences](#normalize-nonprice-differences)
  - [AWS break-even analysis](#aws-break-even-analysis)
  - [Hybrid placement decisions](#hybrid-placement-decisions)
- [AWS Well-Architected alignment](#aws-well-architected-alignment)
  - [Operational excellence](#operational-excellence)
  - [Security](#security)
  - [Reliability](#reliability)
  - [Performance efficiency](#performance-efficiency)
  - [Cost optimization](#cost-optimization)
  - [Sustainability](#sustainability)
- [AWS Cloud Adoption Framework alignment](#aws-cloud-adoption-framework-alignment)
  - [Business perspective](#business-perspective)
  - [People perspective](#people-perspective)
  - [Governance perspective](#governance-perspective)
  - [Platform perspective](#platform-perspective)
  - [Security perspective](#security-perspective)
  - [Operations perspective](#operations-perspective)
- [Recommended reports and dashboards](#recommended-reports-and-dashboards)
  - [Executive cost dashboard](#executive-cost-dashboard)
  - [Project cost dashboard](#project-cost-dashboard)
  - [Capacity and efficiency dashboard](#capacity-and-efficiency-dashboard)
  - [AWS comparison dashboard](#aws-comparison-dashboard)
  - [Storage economics dashboard](#storage-economics-dashboard)
  - [LLM and AI economics dashboard](#llm-and-ai-economics-dashboard)
  - [FinOps control dashboard](#finops-control-dashboard)
- [Implementation roadmap](#implementation-roadmap)
  - [Phase 0 governance and definitions](#phase-0-governance-and-definitions)
  - [Phase 1 metadata and measurement](#phase-1-metadata-and-measurement)
  - [Phase 2 Kalaxy3 rate model](#phase-2-kalaxy3-rate-model)
  - [Phase 3 project allocation and reporting](#phase-3-project-allocation-and-reporting)
  - [Phase 4 AWS comparison engine](#phase-4-aws-comparison-engine)
  - [Phase 5 automation and optimization](#phase-5-automation-and-optimization)
- [Validation and control framework](#validation-and-control-framework)
  - [Cost reconciliation](#cost-reconciliation)
  - [Metadata coverage](#metadata-coverage)
  - [Model versioning](#model-versioning)
  - [Review cadence](#review-cadence)
  - [Acceptance criteria](#acceptance-criteria)
- [Risks limitations and cautions](#risks-limitations-and-cautions)
- [Recommended initial decisions](#recommended-initial-decisions)
- [Nontechnical explanation](#nontechnical-explanation)
  - [What we are building](#what-we-are-building)
  - [Why it matters](#why-it-matters)
  - [How it works](#how-it-works)
  - [What it will tell us](#what-it-will-tell-us)
  - [What it will not claim](#what-it-will-not-claim)
- [Conclusion](#conclusion)
- [Authoritative source basis](#authoritative-source-basis)

## Executive summary

Kalaxy3 now has the core technical foundation for a useful FinOps capability:
Kubecost is running on `amd64-02`, its persistent data is stored on Longhorn,
Prometheus supplies cluster telemetry, and the frontend is available through
MetalLB.

That installation is the beginning of a cost model, not the completed model.

Kubecost can allocate measured Kubernetes resources to containers, pods,
controllers, namespaces, labels, and other Kubernetes dimensions. It can
identify requested resources, used resources, persistent volumes, shared
resources, and idle capacity. This provides the workload-consumption layer of
the model.

A complete Kalaxy3 cost model must add the economic layer:

- hardware purchase and replacement cost;
- depreciation or amortization policy;
- electricity and measured power consumption;
- UPS, network, storage, backup, and maintenance cost;
- the economic cost of Longhorn replication;
- the cost of NFS and MinIO services outside a workload's immediate pod;
- platform engineering and operations effort;
- project ownership and business metadata;
- current AWS pricing and equivalent AWS architecture scenarios;
- differences in availability, durability, elasticity, support, and operational
  responsibility.

The finished model should answer questions such as:

1. What does Kalaxy3 cost per day, month, and year?
2. What is the fully loaded cost of each node, storage tier, and platform
   service?
3. Which projects consume the cluster's CPU, memory, GPU, storage, and network
   capacity?
4. What portion of the platform is idle, reserved, shared, or unavailable?
5. What does a specific project cost when direct and shared costs are included?
6. What is the marginal cost of adding one more workload to existing spare
   capacity?
7. When will a workload require another node, disk, GPU, switch, or UPS?
8. What would the same workload cost on AWS under on-demand, committed, Spot,
   managed-service, and elastic operating models?
9. Is Kalaxy3 cheaper because it is genuinely efficient, or because labor,
   availability, backup, and hardware replacement have not been counted?
10. Which workloads should remain on Kalaxy3, move to AWS, or operate in a
    hybrid model?

The most important architectural decision is to maintain at least three views:

- **Cash view:** actual money paid during the reporting period.
- **Economic view:** amortized hardware, power, labor, replacement, and shared
  platform cost.
- **AWS-equivalent view:** the cost of delivering a defined equivalent outcome
  on AWS.

These views should not be collapsed into a single number because they answer
different questions.

[Back to table of contents](#table-of-contents)

## Research basis

This analysis is based on the following verified Kalaxy3 state:

- Kubecost chart version `3.2.1`;
- Kubecost workloads scheduled on `amd64-02`;
- `amd64-01` preserved for the primary LLM workload;
- Kubecost aggregator, FinOps Agent, frontend, and local store running;
- Longhorn-backed Kubecost PVCs of `128Gi`, `32Gi`, and `1Gi`;
- Longhorn configured for two replicas;
- Kubecost frontend exposed through MetalLB at `192.168.2.26:9090`;
- Prometheus and Grafana installed in the observability platform phase;
- a known nonfatal LoadBalancer-pricing warning in the current on-premises
  FinOps Agent path;
- Ansible and Helm used as the reproducible installation mechanism.

The model also uses these external architectural principles:

- The OpenCost specification defines total cluster cost as asset cost plus
  cluster overhead and distinguishes allocation, usage, shared, and idle cost.
- OpenCost supports allocation by Kubernetes concepts including namespace,
  pod, controller, label, and annotation.
- The AWS Well-Architected Framework treats cost optimization as a continuous
  process and organizes it around financial management, expenditure awareness,
  cost-effective resources, demand and supply, and ongoing optimization.
- AWS CAF organizes transformation capabilities into Business, People,
  Governance, Platform, Security, and Operations perspectives.
- AWS cost allocation relies on a deliberate tagging dictionary and consistent
  cost categories.
- AWS Pricing Calculator and AWS billing data exports provide the basis for
  AWS estimates and actual-cloud comparisons.

No AWS prices should be permanently hard-coded into the Kalaxy3 model. AWS
prices, discounts, service features, and transfer rules change. Each comparison
run should record its source date, region, pricing model, and assumptions.

[Back to table of contents](#table-of-contents)

## Current Kalaxy3 cost architecture

### Relevant Kalaxy3 components

The current architecture includes cost-bearing resources in several layers.

| Layer | Kalaxy3 components | Cost relevance |
|---|---|---|
| Control plane | Three Raspberry Pi K3s server nodes | Hardware, power, boot storage, cluster overhead |
| General workers | Raspberry Pi and Intel K3s agents | CPU, RAM, disk, power, workload capacity |
| LLM compute | `amd64-01`, RTX 3090-class GPU resources | High capital cost, high power cost, scarce capacity |
| Secondary AMD64 compute | `amd64-02` | Kubecost, Longhorn, general x86 workload capacity |
| Distributed block storage | Longhorn on AMD64 disks | Media, replication, I/O, network, capacity overhead |
| Shared file storage | NFS server and exported SSD/HDD storage | Server, disks, power, network, backup |
| Object storage | MinIO on Raspberry Pi data disks | Disk capacity, replication, power, network |
| Networking | 2.5 GbE and 10 GbE switching, router, MetalLB, Traefik | Hardware, power, shared service, ingress |
| Observability | Prometheus, Grafana, Kubecost | Shared CPU, memory, storage, operational overhead |
| Resilience | UPS devices, backups, redundant storage | Hardware, battery replacement, energy loss, capacity |
| Automation | Ansible, Helm, GitHub, generated documentation | Engineering effort, risk reduction, rebuild efficiency |

### What Kubecost currently provides

Kubecost can serve as the allocation engine for in-cluster resources. It should
be able to provide or derive:

- CPU requested and consumed;
- memory requested and consumed;
- pod, container, controller, and namespace allocation;
- node attribution;
- persistent-volume capacity attribution;
- idle resources;
- shared cluster-resource allocation;
- time-windowed historical cost and usage;
- aggregation by Kubernetes labels and annotations;
- relative efficiency and rightsizing signals.

This is enough to identify which Kubernetes workloads consume capacity.

### What Kubecost does not provide by itself

The current installation does not automatically know:

- the purchase price of each Kalaxy3 machine;
- whether to value donated, reused, or previously depreciated equipment at
  historical cost, book value, or replacement cost;
- actual electricity rates;
- real-time watts consumed by each node and device;
- UPS losses and cooling overhead;
- hardware maintenance and expected failure rates;
- operator and engineering labor;
- the cost of internet service or shared network equipment;
- the full cost of NFS, MinIO, backup, and off-cluster services;
- the business owner and outcome of every workload;
- a current equivalent AWS architecture;
- AWS discounts, commitments, support, transfer, NAT, logging, and managed
  service charges;
- the business value produced by a project.

Kubecost should therefore be treated as one component of the Kalaxy3 FinOps
architecture, not as the complete accounting system.

[Back to table of contents](#table-of-contents)

## What the Kalaxy3 cost model should accomplish

### Measure total cost of ownership

The model should produce a complete Kalaxy3 TCO that includes:

- amortized hardware;
- power;
- storage media;
- networking;
- UPS and battery replacement;
- backup;
- software and support where applicable;
- operations labor;
- expected maintenance and replacement;
- shared cluster overhead.

It should report both monthly and annual cost and retain the assumptions used.

### Measure project and workload impact

Each project should receive a view of:

- direct CPU, memory, GPU, storage, and network consumption;
- reserved resources;
- actual usage;
- project-attributable persistent volumes;
- direct external services;
- its portion of shared platform services;
- its portion of idle capacity under the selected policy;
- the capacity threshold it is moving Kalaxy3 toward.

The model should distinguish a project that merely uses otherwise-idle capacity
from a project that triggers the purchase of another GPU, disk, node, switch,
or UPS.

### Compare Kalaxy3 with AWS

The model should generate AWS-equivalent scenarios using the same measured
workload demand and service objectives.

The comparison should include:

- an EKS-based Kubernetes rehost;
- an AWS-managed-services alternative;
- an elastic AWS design that shuts down or scales down when unused;
- on-demand pricing;
- commitment-adjusted pricing;
- Spot pricing for interruptible work;
- storage, backup, monitoring, support, load-balancing, public IPv4, and data
  transfer;
- labor and operational responsibility differences.

The comparison should show a range rather than a single false-precision number.

### Support capacity and investment decisions

The model should forecast:

- when CPU, RAM, GPU, storage, network, or power becomes constrained;
- the incremental cost of the next capacity addition;
- which project is driving the threshold;
- whether it is cheaper to add local capacity or burst to AWS;
- whether replacing old hardware reduces power and support cost;
- whether a Raspberry Pi, general x86 node, GPU node, or managed AWS service is
  the best fit.

### Support showback and chargeback

**Showback** reports the cost associated with a project, owner, or service
without requiring actual money transfer.

**Chargeback** assigns or recovers that cost from the responsible budget.

Kalaxy3 should begin with showback. Chargeback should only be considered after
the allocation model is stable, accepted, and reconciled.

### Measure unit economics

A strong cost model should move beyond infrastructure totals and calculate
cost per useful outcome.

Potential Kalaxy3 units include:

- cost per CI build;
- cost per deployment;
- cost per data-pipeline run;
- cost per document indexed;
- cost per gigabyte processed;
- cost per one million tokens generated;
- cost per LLM request;
- cost per GPU-hour;
- cost per training or fine-tuning run;
- cost per database transaction;
- cost per retained terabyte-month;
- cost per active development project.

Unit economics allow Kalaxy3 and AWS to be compared on outcomes rather than
hardware labels.

### Identify waste and optimization opportunities

The model should identify:

- excessive CPU or memory requests;
- low-utilization nodes;
- underused GPU capacity;
- stale PVCs;
- unnecessary data replication;
- retained data with no owner;
- projects that run continuously but could be scheduled;
- services using expensive storage tiers without need;
- duplicated observability or platform components;
- workloads suited to ARM instead of x86;
- workloads suited to AWS Spot or short-lived cloud execution.

### Quantify business and engineering value

Cost is only half of the decision.

The model should also record benefits such as:

- faster experimentation;
- privacy and local data control;
- reduced AWS data-egress exposure;
- practical Kubernetes learning;
- architecture validation before cloud deployment;
- offline availability;
- LLM data locality;
- reusable automation and documentation;
- reduced rebuild and recovery time;
- avoidance of cloud commitment before a project proves value.

[Back to table of contents](#table-of-contents)

## Cost model principles

### Separate cost from price

Kalaxy3 has costs even when no new invoice is generated.

A server purchased two years ago may have zero current cash expense but still
has:

- economic value;
- replacement cost;
- power cost;
- failure risk;
- capacity opportunity cost.

The model should maintain these distinct concepts:

| Concept | Meaning |
|---|---|
| Cash cost | Money paid during the period |
| Historical cost | Original purchase cost |
| Book cost | Remaining value under a depreciation policy |
| Replacement cost | Current cost to replace equivalent capability |
| Marginal cost | Additional cost caused by one more unit of work |
| Fully loaded cost | Direct plus shared plus overhead cost |
| Opportunity cost | Value of the best alternative use of scarce capacity |
| AWS-equivalent price | Estimated AWS charge for an equivalent outcome |

### Separate fixed variable direct shared idle and overhead costs

| Cost class | Kalaxy3 example |
|---|---|
| Fixed | Purchased server, switch, UPS |
| Variable | Electricity, replacement disks, cloud bursting |
| Direct | A project's dedicated GPU hours or PVC |
| Shared | Prometheus, Traefik, CoreDNS, control plane |
| Idle | Purchased CPU or RAM not assigned to useful work |
| Overhead | Platform engineering, backups, documentation |
| Step cost | Another node required after capacity threshold |
| Sunk cost | Historical expense that cannot be recovered |

The categories must remain visible so a decision-maker can choose the
appropriate view.

### Maintain actual forecast and comparison views

The model should preserve three separate datasets:

1. **Actual:** measured Kalaxy3 usage and incurred cost.
2. **Forecast:** projected Kalaxy3 usage and planned capacity cost.
3. **Comparison:** hypothetical AWS architecture and price.

Mixing them would make reconciliation and decision-making unreliable.

### Compare equivalent outcomes rather than isolated resources

A Raspberry Pi should not be compared directly with an arbitrary EC2 instance
solely because both have four cores.

The comparison must account for:

- architecture;
- CPU performance;
- memory;
- storage throughput;
- network throughput;
- GPU capability;
- availability;
- backup;
- support;
- elasticity;
- operating hours;
- operational labor;
- data locality.

Benchmark-equivalent service delivery is the correct comparison target.

### Preserve traceability

Every calculated number should be traceable to:

- a measured usage record;
- a cost-rate record;
- a project-allocation rule;
- an AWS price source;
- a model version;
- an effective date;
- an assumption owner.

[Back to table of contents](#table-of-contents)

## Proposed Kalaxy3 cost taxonomy

### Compute

Compute cost should include:

- chassis, motherboard, CPU, RAM, boot storage, NIC, and PSU;
- useful life;
- expected replacement cost;
- measured or estimated power;
- maintenance reserve;
- node-specific capacity;
- operating schedule;
- allocated and idle CPU/RAM.

ARM and x86 should have separate rate families because their performance,
power, and workload compatibility differ.

### GPU and accelerated computing

GPU cost should include:

- GPU purchase or replacement value;
- host-system share;
- incremental GPU power;
- cooling and UPS overhead;
- memory capacity;
- measured utilization;
- reserved versus active GPU time;
- driver and operational effort;
- scarce-capacity opportunity cost.

For the primary LLM node, the model should distinguish:

- base host cost;
- GPU cost;
- storage/cache cost;
- LLM service overhead;
- project-specific inference or training use;
- idle GPU time retained for responsiveness.

### Longhorn block storage

Longhorn cost must reflect physical replication rather than only logical PVC
size.

For a logical `100Gi` PVC with two replicas, the model should recognize
approximately `200Gi` of raw replica capacity before filesystem and operational
overhead.

Longhorn cost includes:

- disk depreciation;
- storage-node share;
- replication traffic;
- I/O;
- backup or snapshot storage;
- failed-replica rebuild overhead;
- reserved free-space policy;
- operational monitoring.

### NFS shared storage

NFS is outside the immediate Kubecost workload allocation path and requires a
separate service model.

NFS cost should include:

- NFS server depreciation;
- disk depreciation by tier;
- server and disk power;
- network equipment share;
- backup;
- filesystem administration;
- used capacity;
- reserved capacity;
- project directory ownership;
- read/write traffic where measurable.

NFS cost may be allocated by:

- owned bytes;
- average retained bytes over time;
- I/O volume;
- a blended capacity and activity formula.

Capacity should be the primary driver unless I/O materially affects hardware
or performance.

### MinIO object storage

MinIO should be treated as an internal object-storage service.

The model should include:

- raw disk capacity;
- erasure coding or replication overhead;
- Raspberry Pi host share;
- power;
- network;
- backup or secondary copy;
- retained object bytes;
- request volume if material;
- project bucket ownership.

For AWS comparison, MinIO should generally map to S3, but durability,
availability, request pricing, lifecycle tiers, and data-transfer rules must be
normalized.

### Network and ingress

Kalaxy3 network cost includes:

- switches;
- router share;
- NICs and optics;
- cabling;
- power;
- internet service share where appropriate;
- ingress services such as Traefik and MetalLB;
- monitoring and administration.

MetalLB does not create a separately billed cloud load balancer, but it is not
economically free. It consumes shared network and operational resources.

AWS comparisons must include:

- load-balancer hourly and capacity-unit charges;
- public IPv4;
- NAT where required;
- cross-AZ transfer;
- internet egress;
- private connectivity if included.

### Control plane and shared platform services

Shared platform services include:

- K3s control-plane nodes;
- etcd;
- CoreDNS;
- Traefik;
- MetalLB;
- Longhorn control components;
- Prometheus;
- Grafana;
- Kubecost;
- Headlamp;
- logging and backup components;
- GitOps and automation components.

These should normally be treated as shared cluster overhead and distributed
under an explicit policy.

### Power cooling UPS and facilities

Power cost should include:

- measured node watts;
- disk and switch watts;
- UPS conversion loss;
- battery charging and replacement;
- cooling overhead if material;
- local electricity rate;
- time-of-use pricing if applicable.

A simplified model can begin with average watts and a single electricity rate.
A mature model should use NUT/UPS measurements and device-specific telemetry.

### Operations labor and engineering effort

Ignoring labor creates a biased comparison with managed cloud services.

Track at least:

- cluster installation and upgrades;
- incident response;
- backup testing;
- hardware replacement;
- security patching;
- storage administration;
- network administration;
- observability maintenance;
- FinOps model maintenance;
- documentation and automation.

Two labor views are useful:

- **Cash labor:** actual paid or contracted labor.
- **Economic labor:** hours valued at an agreed internal rate, even when the
  work is performed as part of learning or personal development.

### Maintenance replacement backup and risk

The model should include policy reserves for:

- disk failures;
- UPS batteries;
- fans and power supplies;
- node replacement;
- backup media;
- disaster recovery;
- security incidents;
- downtime.

Risk cost should not be invented as false precision. It can be represented as
scenario ranges or expected-loss estimates.

[Back to table of contents](#table-of-contents)

## Project allocation architecture

### Required Kubernetes metadata

Project cost cannot be reliable unless workloads identify their owner and
purpose.

Every application namespace and workload should have enough metadata to answer:

- Who owns it?
- Which project or product does it support?
- Is it development, test, staging, production, research, or shared platform?
- What service does it provide?
- Is it temporary or permanent?
- What is its criticality?
- What cost center or budget applies?
- When should it expire?

### Recommended label dictionary

Use a common dictionary on namespaces and, where needed, workloads.

```yaml
metadata:
  labels:
    kalaxy3.io/project: project-name
    kalaxy3.io/product: product-name
    kalaxy3.io/service: service-name
    kalaxy3.io/owner: owner-name
    kalaxy3.io/team: team-name
    kalaxy3.io/environment: dev
    kalaxy3.io/cost-center: research
    kalaxy3.io/workload-class: batch
    kalaxy3.io/criticality: low
    kalaxy3.io/data-classification: internal
    kalaxy3.io/lifecycle: persistent
```

Useful optional annotations:

```yaml
metadata:
  annotations:
    kalaxy3.io/expires-on: "2026-12-31"
    kalaxy3.io/business-purpose: "Document RAG evaluation"
    kalaxy3.io/aws-comparison-profile: "eks-managed"
```

Do not place secrets or sensitive personal data in labels or annotations.

### Namespace policy

Preferred policy:

- one namespace per project and environment;
- shared services in clearly identified platform namespaces;
- project ownership inherited from namespace labels;
- workload overrides only when a namespace contains multiple cost owners;
- admission-policy enforcement after the label dictionary stabilizes.

### Direct cost allocation

Directly allocate:

- container CPU and memory;
- dedicated GPU use;
- project PVCs;
- project MinIO buckets;
- project NFS directories;
- dedicated load balancers or ingress resources;
- project-specific backup;
- project-specific AWS burst resources;
- project-specific software licenses.

### Shared platform cost allocation

Shared costs should be reported separately first, then optionally distributed.

Recommended default policies:

| Shared cost | Initial policy |
|---|---|
| K3s control plane | Proportionate to direct project cost |
| CoreDNS and CNI | Proportionate to pod CPU and network activity |
| Traefik and MetalLB | Proportionate to ingress traffic or service count |
| Prometheus and Grafana | Proportionate to monitored workload volume |
| Kubecost | Uniform platform overhead or proportionate to direct cost |
| Longhorn controllers | Proportionate to logical Longhorn storage |
| NFS server base cost | Proportionate to retained project capacity |
| Backup platform | Proportionate to protected data |
| Platform labor | Proportionate to direct cost or tracked service effort |

The report should always show the undistributed amount and the allocation rule.

### Idle cost policy

Idle cost is economically important and politically sensitive.

Maintain these views:

1. **Unallocated idle:** idle remains a platform cost.
2. **Proportional idle:** idle is distributed according to direct resource cost.
3. **Reserved idle:** idle capacity explicitly reserved for a project is charged
   to that project.
4. **Growth reserve:** strategic headroom remains a platform investment.

Do not use a single idle allocation policy for every decision.

### Storage replication policy

For project reporting, show both:

- logical project storage;
- physical storage consumed after replication and protection.

Example:

```text
Logical PVC:                 128 GiB
Longhorn replica count:     2
Raw replica capacity:       approximately 256 GiB
Additional overhead:        measured separately
```

This avoids presenting replicated storage as if only one copy exists.

### Project lifecycle policy

Each project should have:

- start date;
- owner;
- expected end or review date;
- minimum service requirement;
- namespace and storage ownership;
- archive and deletion policy;
- AWS comparison profile;
- monthly budget or capacity target.

Expired projects should be reviewed for workload shutdown and data retention.

[Back to table of contents](#table-of-contents)

## Data required for the Kalaxy3 model

### Kubecost and Kubernetes allocation data

Collect from Kubecost/OpenCost-compatible allocation and asset interfaces:

- timestamp and query window;
- cluster;
- node;
- namespace;
- controller and controller type;
- pod;
- container;
- labels and annotations;
- CPU request;
- CPU usage;
- memory request;
- memory usage;
- GPU request and usage where available;
- PVC allocation;
- network allocation where available;
- direct cost;
- shared cost;
- idle cost;
- efficiency.

Useful aggregation dimensions include:

- namespace;
- node;
- project label;
- owner label;
- environment label;
- service label;
- controller;
- pod;
- container.

### Prometheus operational telemetry

Collect or derive:

- node CPU usage;
- node load;
- memory use;
- filesystem capacity and use;
- disk I/O;
- network bytes;
- container CPU and memory;
- pod requests and limits;
- GPU utilization and memory;
- GPU power where exporters support it;
- Longhorn capacity, replicas, health, and traffic;
- NFS server capacity and I/O;
- MinIO capacity, requests, and traffic;
- UPS load and power;
- temperatures;
- availability and restarts.

Prometheus provides the operational measurements that support rate allocation,
capacity forecasting, and model validation.

### Hardware inventory and purchase data

Create a version-controlled inventory table with:

- asset ID;
- hostname;
- component;
- manufacturer and model;
- architecture;
- CPU;
- RAM;
- GPU;
- disk;
- NIC;
- acquisition date;
- purchase cost;
- tax and shipping;
- upgrade cost;
- current replacement cost;
- expected useful life;
- residual value;
- warranty expiration;
- expected retirement date;
- assigned platform role.

Track components separately when they have different useful lives, especially
GPUs, disks, UPS batteries, and network switches.

### Power and electricity data

Required data:

- electricity price per kWh;
- effective date;
- node idle watts;
- node typical watts;
- node peak watts;
- GPU incremental watts;
- disk and switch watts;
- NFS server watts;
- UPS input and output where available;
- cooling or power-usage-effectiveness factor if material;
- operating schedule.

Preferred source hierarchy:

1. measured UPS or smart-plug data;
2. device telemetry;
3. measured sample;
4. vendor specification;
5. documented estimate.

Record the source and confidence.

### Storage data

For every storage service and tier:

- physical device capacity;
- usable capacity;
- reserved free-space policy;
- logical allocated capacity;
- actual used capacity;
- replica or erasure-coding factor;
- snapshots;
- backups;
- read/write activity;
- retention;
- owner;
- media cost;
- expected media life;
- power;
- failure and replacement history.

### Network data

Collect:

- bytes by node;
- bytes by project where available;
- ingress and egress;
- LAN versus internet traffic;
- switch port utilization;
- cross-node Longhorn replication traffic;
- NFS and MinIO traffic;
- internet service cost;
- network hardware cost;
- public service count;
- MetalLB service count.

For AWS comparison, identify which traffic would become:

- same-AZ;
- cross-AZ;
- inter-region;
- internet egress;
- NAT-processed;
- load-balanced.

### Operations and labor data

Track monthly hours by category:

```text
platform-build
cluster-upgrade
security-patching
storage-administration
backup-and-recovery
incident-response
network-administration
observability
finops
documentation
project-support
```

Record:

- person or role;
- hours;
- activity category;
- project where direct;
- shared platform where indirect;
- cash rate or economic rate;
- incident or change reference.

### Project and business metadata

Required project data:

- project ID;
- name;
- owner;
- team;
- business purpose;
- environment;
- criticality;
- start date;
- expected end date;
- budget;
- service-level target;
- data classification;
- namespace;
- storage locations;
- Git repository;
- deployment name;
- expected growth;
- unit-of-work definition;
- AWS comparison profile.

### AWS comparison data

For each modeled AWS scenario, capture:

- pricing date;
- region;
- currency;
- operating hours;
- instance types;
- CPU architecture;
- GPU type;
- EKS mode and version support tier;
- EBS type, capacity, IOPS, and throughput;
- EFS capacity and activity;
- S3 storage classes, requests, and lifecycle;
- load balancer type and capacity units;
- public IPv4 count;
- NAT processing;
- data transfer;
- snapshots and backups;
- managed Prometheus and Grafana if selected;
- CloudWatch logs and metrics;
- support plan;
- commitment term;
- Savings Plan or Reserved Instance assumptions;
- Spot interruption assumptions;
- taxes where relevant.

Use AWS Pricing Calculator for modeled estimates and AWS Data Exports or CUR 2.0
for actual AWS usage when workloads are tested in AWS.

[Back to table of contents](#table-of-contents)

## Proposed analytical data model

### Core dimensions

| Dimension | Purpose |
|---|---|
| `dim_time` | Hour, day, month, fiscal period |
| `dim_asset` | Server, GPU, disk, switch, UPS |
| `dim_node` | Kubernetes node and hardware mapping |
| `dim_project` | Project ownership and business purpose |
| `dim_workload` | Namespace, controller, pod, container |
| `dim_storage` | PVC, Longhorn volume, NFS path, MinIO bucket |
| `dim_service` | Platform service such as Prometheus or Traefik |
| `dim_cost_rate` | Electricity, depreciation, labor, AWS price |
| `dim_scenario` | Actual Kalaxy3, forecast, AWS on-demand, AWS committed |
| `dim_model_version` | Assumptions and effective dates |

### Core fact tables

| Fact | Example measurements |
|---|---|
| `fact_resource_allocation` | Requested and used CPU, RAM, GPU |
| `fact_storage_allocation` | Logical bytes, physical bytes, replicas |
| `fact_network_usage` | Bytes by project, service, and traffic class |
| `fact_power_usage` | Watts and kWh by asset |
| `fact_asset_cost` | Depreciation, maintenance, power |
| `fact_labor_cost` | Hours and cost by activity and project |
| `fact_project_cost` | Direct, shared, idle, overhead |
| `fact_unit_economics` | Cost per token, build, job, or GB |
| `fact_aws_estimate` | AWS service quantities and estimated price |
| `fact_capacity_forecast` | Exhaustion date and next-step cost |

### Data retention and granularity

Recommended retention:

| Data | Granularity | Retention |
|---|---|---|
| Operational metrics | 1 to 5 minutes | Based on Prometheus capacity |
| Cost allocation | Hourly | At least 13 months |
| Daily project summary | Daily | Indefinite |
| Finance summary | Monthly | Indefinite |
| AWS scenario | Per model run | Indefinite |
| Assumption versions | Effective-dated | Indefinite |

Hourly cost data is usually sufficient for FinOps analysis while preserving
higher-frequency metrics for operational troubleshooting.

### Data flow

```text
Kubernetes metrics ───────┐
Kubecost allocations ─────┤
Prometheus telemetry ─────┤
Longhorn metrics ─────────┤
NFS and MinIO metrics ────┤
UPS and power data ───────┼──> Kalaxy3 cost data pipeline
Asset inventory ──────────┤            |
Purchase ledger ──────────┤            v
Labor records ────────────┤      normalized cost facts
Project metadata ─────────┤            |
AWS pricing inputs ───────┘            v
                                  reports and scenarios
                                         |
                  ┌──────────────────────┼──────────────────────┐
                  v                      v                      v
             Kalaxy3 actual        Project showback       AWS comparison
```

The data pipeline should be reproducible from code and preserve raw source
records before transformation.

[Back to table of contents](#table-of-contents)

## Cost formulas

### Hardware depreciation

A straightforward economic rate is:

```text
Depreciable value =
    purchase cost
  + acquisition cost
  + upgrades
  - residual value

Hourly depreciation =
  depreciable value / expected useful-life hours
```

For equipment that already exists, report both historical-cost and
replacement-cost views.

### Power

```text
Hourly power cost =
  average watts / 1000
  × electricity price per kWh
  × power overhead factor
```

The power overhead factor may include UPS loss and cooling.

### Node cost

```text
Node hourly cost =
    hourly depreciation
  + hourly power
  + maintenance reserve
  + network share
  + UPS share
  + software and support
  + operations share
```

### CPU memory and GPU rates

The node cost can be distributed among resources using a documented weighting
model.

Example:

```text
Allocatable node cost =
  CPU rate × allocatable cores
  + RAM rate × allocatable GiB
  + GPU rate × allocatable GPU units
```

Weights should reflect scarcity and replacement economics. The rates must
reconcile back to the fully loaded node cost.

### Storage

```text
Storage tier monthly cost =
    media depreciation
  + host share
  + power
  + network share
  + backup
  + operations
  + maintenance reserve
```

```text
Logical GB-month rate =
  storage tier monthly cost / billable logical GB
```

For Longhorn:

```text
Physical consumption =
  logical allocation × replica factor + measured overhead
```

### Project cost

```text
Project fully loaded cost =
    direct compute
  + direct GPU
  + direct storage
  + direct network
  + direct external services
  + allocated shared platform cost
  + allocated idle cost under selected policy
  + allocated operations overhead
```

### Marginal cost

The marginal cost of a project is not always its fully loaded cost.

```text
Marginal cost =
  additional power
  + consumables
  + external services
  + incremental labor
  + step cost triggered by capacity exhaustion
```

A project using spare capacity may have low short-term marginal cost but still
consume scarce capacity and bring forward the next purchase.

### Avoided AWS cost

```text
Avoided AWS cost =
  AWS equivalent cost
  - Kalaxy3 incremental cost
```

For strategic comparisons, also calculate:

```text
Net economic advantage =
  AWS equivalent cost
  - Kalaxy3 fully loaded economic cost
  - risk and service-level adjustment
```

Do not label the entire AWS estimate as savings when the Kalaxy3 cost basis
excludes labor, resilience, or replacement.

[Back to table of contents](#table-of-contents)

## AWS comparison methodology

### Comparison scenarios

Each significant project should be evaluated against at least these scenarios.

#### Scenario A Kalaxy3 actual

Measured Kalaxy3 usage with current cash cost.

#### Scenario B Kalaxy3 fully loaded

Measured usage with depreciation, replacement, power, labor, backup, and shared
cost.

#### Scenario C AWS Kubernetes rehost

A close functional rehost using:

- EKS;
- EC2 worker nodes;
- EBS;
- EFS where shared POSIX storage is required;
- S3 for object storage;
- ALB or NLB;
- AWS observability or self-managed equivalents;
- backups and transfer.

#### Scenario D AWS managed-service redesign

Replace self-managed components with appropriate managed services where that
changes cost or operational responsibility.

#### Scenario E AWS elastic execution

Use:

- autoscaling;
- schedule-based shutdown;
- Spot for interruptible work;
- serverless or managed batch where appropriate;
- object storage lifecycle;
- ephemeral environments.

#### Scenario F Hybrid

Keep data-intensive or continuously used workloads on Kalaxy3 and use AWS for:

- burst;
- disaster recovery;
- public delivery;
- globally distributed access;
- short-lived high-capacity jobs;
- services that benefit from managed operations.

### Kalaxy3 to AWS service mapping

| Kalaxy3 capability | AWS comparison candidates | Important normalization |
|---|---|---|
| K3s control plane | EKS standard control plane | Managed HA, support, version lifecycle |
| ARM worker nodes | Graviton EC2 | Benchmark equivalent, operating hours |
| x86 worker nodes | General-purpose or compute EC2 | CPU generation, RAM, local versus EBS |
| RTX GPU node | GPU EC2 family | GPU model, VRAM, availability, hourly use |
| Longhorn RWO storage | EBS plus snapshots | AZ scope, replica semantics, IOPS |
| NFS | EFS or self-managed NFS on EC2 | Throughput, storage class, HA |
| MinIO | S3 | Durability, request cost, lifecycle, egress |
| MetalLB | ALB or NLB | Hourly charge, capacity units, IPv4 |
| Traefik | ALB Controller or self-managed ingress | Managed versus self-managed responsibility |
| Prometheus | Amazon Managed Service for Prometheus or self-managed | Ingestion, retention, query charges |
| Grafana | Amazon Managed Grafana or self-managed | Users, workspace, operations |
| Local backups | EBS snapshots, S3, Glacier classes | Retention, retrieval, transfer |
| LAN network | VPC, AZ traffic, NAT, internet egress | Traffic classification |
| Home power and cooling | Included in AWS service price | No separate customer electricity charge |
| Hardware operations | AWS-managed infrastructure | Internal platform labor still remains |

No mapping is automatically correct. The project service objective determines
the appropriate AWS design.

### AWS cost inputs

The AWS model must include all material services, not only EC2:

- EKS cluster charge;
- EC2 compute;
- EBS storage, IOPS, and snapshots;
- EFS storage and activity;
- S3 storage, requests, replication, and retrieval;
- load balancers;
- public IPv4;
- NAT gateway;
- data transfer;
- CloudWatch;
- managed Prometheus and Grafana where used;
- backup;
- support;
- commitments;
- taxes where applicable.

### Normalize nonprice differences

The comparison must state differences in:

- availability;
- durability;
- backup and recovery;
- geographic resilience;
- elasticity;
- deployment speed;
- security controls;
- auditability;
- support;
- hardware access;
- data locality;
- privacy;
- internet dependency;
- operator effort;
- performance consistency.

An AWS solution may cost more while providing capabilities Kalaxy3 does not
currently provide. Kalaxy3 may cost less while providing local control and
predictable capacity.

### AWS break-even analysis

For each workload, calculate:

- minimum and maximum monthly AWS estimate;
- Kalaxy3 cash cost;
- Kalaxy3 fully loaded cost;
- utilization level where local hardware breaks even;
- operating hours where AWS elasticity becomes advantageous;
- date when another Kalaxy3 purchase is required;
- payback period for that purchase;
- sensitivity to electricity, hardware life, AWS discounts, and labor.

### Hybrid placement decisions

Good hybrid candidates include workloads with:

- low steady utilization but occasional high peaks;
- public internet delivery;
- disaster-recovery needs;
- short-lived large compute demand;
- data that can move economically;
- managed-service operational benefit.

Good Kalaxy3 candidates include workloads with:

- high continuous utilization;
- large local datasets;
- high cloud-egress exposure;
- privacy or local-control requirements;
- experimentation that would otherwise leave cloud resources running;
- available local capacity;
- tolerance for Kalaxy3's service level.

[Back to table of contents](#table-of-contents)

## AWS Well-Architected alignment

### Operational excellence

The cost model supports operational excellence by:

- making ownership explicit;
- versioning infrastructure and cost assumptions;
- automating collection and reports;
- measuring the operational cost of platform services;
- linking incidents and changes to cost;
- documenting rebuild procedures;
- establishing regular workload reviews.

### Security

The model should include the cost of security rather than treating it as free.

Measure:

- patching effort;
- secrets and identity services;
- vulnerability management;
- backup and recovery;
- audit and logging;
- segmentation;
- encryption;
- security incidents.

Project labels must not contain secrets or sensitive personal information.

### Reliability

Reliability has an economic cost.

The model should identify the cost of:

- three-node control plane;
- Longhorn replication;
- backups;
- spare capacity;
- UPS protection;
- replacement hardware;
- monitoring;
- recovery testing.

AWS comparisons must use the same availability and durability target rather
than comparing a resilient AWS design with an unprotected local workload, or
the reverse.

### Performance efficiency

The model supports performance efficiency through:

- rightsizing;
- ARM versus x86 placement;
- GPU utilization;
- storage tier selection;
- performance-per-watt;
- performance-per-dollar;
- workload scheduling;
- benchmark-based AWS instance selection.

### Cost optimization

The Kalaxy3 model directly implements the cost-optimization focus areas:

- financial ownership;
- expenditure and usage awareness;
- cost-effective resource selection;
- demand and supply management;
- continuous optimization.

The model should establish monthly reviews rather than act as a one-time
calculator.

### Sustainability

The model can add energy and carbon-oriented measures:

- kWh by asset;
- kWh by project;
- useful work per kWh;
- performance per watt;
- idle energy;
- equipment life extension;
- avoided hardware purchases;
- comparison with AWS sustainability data where available.

Sustainability should not be reduced to power alone. Hardware manufacture,
utilization, lifetime, and retirement also matter.

[Back to table of contents](#table-of-contents)

## AWS Cloud Adoption Framework alignment

### Business perspective

The model connects infrastructure decisions to outcomes by providing:

- project unit economics;
- investment cases;
- AWS-versus-Kalaxy3 comparisons;
- budget forecasts;
- capacity funding decisions;
- value and cost-avoidance reporting.

### People perspective

The model clarifies:

- ownership;
- FinOps responsibilities;
- platform skills;
- training value;
- operational effort;
- decision rights;
- collaboration between architecture, engineering, operations, and finance.

### Governance perspective

The model provides:

- cost policy;
- metadata standards;
- budget and forecast controls;
- model versioning;
- review cadence;
- exceptions;
- evidence for investment and architecture decisions;
- risk-aware cost reporting.

### Platform perspective

The model evaluates:

- node architecture;
- workload placement;
- storage tiers;
- standard platform services;
- automation;
- hybrid AWS integration;
- service catalogs;
- reusable deployment patterns.

### Security perspective

The model includes security as a required service quality and cost category.
It avoids choosing a cheaper architecture that fails the required security
outcome.

### Operations perspective

The model measures:

- service health;
- capacity;
- incidents;
- operational effort;
- reliability investment;
- backup and recovery;
- observability overhead;
- continuous improvement.

[Back to table of contents](#table-of-contents)

## Recommended reports and dashboards

### Executive cost dashboard

Show:

- monthly Kalaxy3 cash cost;
- monthly fully loaded cost;
- annual forecast;
- AWS-equivalent range;
- utilization;
- idle cost;
- largest projects;
- next capacity constraint;
- key assumptions and model version.

### Project cost dashboard

For each project:

- direct cost;
- shared cost;
- idle allocation;
- total cost;
- CPU, RAM, GPU, storage, and network;
- trend;
- budget;
- unit economics;
- AWS-equivalent range;
- owner;
- lifecycle date.

### Capacity and efficiency dashboard

Show:

- node CPU and memory saturation;
- GPU utilization;
- allocatable versus requested;
- physical versus logical storage;
- Longhorn replica overhead;
- NFS and MinIO growth;
- power;
- forecast exhaustion date;
- next purchase trigger.

### AWS comparison dashboard

Show:

- Kalaxy3 actual;
- Kalaxy3 fully loaded;
- AWS on-demand;
- AWS committed;
- AWS Spot or elastic;
- hybrid;
- service-level differences;
- sensitivity ranges;
- break-even utilization.

### Storage economics dashboard

Show:

- logical and physical bytes;
- Longhorn replica factor;
- NFS retained bytes;
- MinIO retained bytes;
- cost per GB-month;
- stale volumes and buckets;
- backup capacity;
- growth forecast.

### LLM and AI economics dashboard

Show:

- GPU hours;
- GPU utilization;
- GPU power;
- tokens;
- requests;
- latency;
- documents indexed;
- vector-store growth;
- cost per million tokens;
- cost per document indexed;
- AWS GPU comparison;
- break-even utilization.

### FinOps control dashboard

Show:

- percentage of workloads with required labels;
- unallocated cost;
- unknown owner cost;
- stale projects;
- model reconciliation difference;
- expired cost rates;
- AWS price-data age;
- missing power measurements;
- missing asset values.

[Back to table of contents](#table-of-contents)

## Implementation roadmap

### Phase 0 governance and definitions

Deliverables:

- cost-model charter;
- owner;
- cost taxonomy;
- showback policy;
- idle policy;
- shared-cost policy;
- useful-life policy;
- labor-rate policy;
- AWS comparison profiles;
- model versioning rules.

Decisions:

- historical versus replacement-cost primary view;
- monthly reporting date;
- electricity source;
- treatment of donated equipment;
- treatment of personal learning labor;
- minimum materiality threshold.

### Phase 1 metadata and measurement

Actions:

1. Apply the project label dictionary.
2. Establish one project-and-environment namespace pattern.
3. Measure label coverage.
4. Export Kubecost allocation and asset data.
5. Add GPU metrics.
6. Add NFS metrics.
7. Add MinIO metrics.
8. collect Longhorn physical capacity and replica data.
9. Collect UPS and power data.
10. Build the hardware inventory.
11. Record purchase and replacement values.

Exit criteria:

- at least 95 percent of nonplatform workload cost has an owner;
- all storage has an owner or is marked shared;
- all nodes have inventory and cost records;
- electricity and useful-life assumptions are versioned.

### Phase 2 Kalaxy3 rate model

Actions:

1. Calculate hourly depreciation by asset.
2. Calculate power rates.
3. Calculate node fully loaded hourly rates.
4. Define CPU, RAM, and GPU allocation weights.
5. Calculate Longhorn, NFS, and MinIO storage rates.
6. Calculate shared platform monthly cost.
7. Add labor and maintenance scenarios.
8. Reconcile rates to total Kalaxy3 cost.

Exit criteria:

- allocated plus shared plus idle cost reconciles to modeled total cost;
- every rate has an effective date and source;
- cash and economic views are separate.

### Phase 3 project allocation and reporting

Actions:

1. Aggregate Kubecost by project labels.
2. Join external NFS, MinIO, labor, and asset costs.
3. Implement shared and idle allocation policies.
4. Produce daily and monthly project reports.
5. Define initial unit economics.
6. Create Grafana or generated Markdown reports.
7. Review results with project owners.

Exit criteria:

- each project has direct and fully loaded cost;
- unknown ownership is below threshold;
- reports can be reproduced from source data.

### Phase 4 AWS comparison engine

Actions:

1. Define AWS region and service-level profiles.
2. Map Kalaxy3 resources to AWS services.
3. Benchmark representative workloads.
4. Create AWS Pricing Calculator estimates.
5. Store service quantities and assumptions.
6. Implement on-demand, committed, Spot, managed, and hybrid scenarios.
7. Include transfer, monitoring, backup, support, and IPv4.
8. Validate with an AWS pilot where practical.

Exit criteria:

- each comparison identifies date, region, pricing model, and architecture;
- comparisons normalize availability, durability, and operating hours;
- no comparison relies only on EC2 price.

### Phase 5 automation and optimization

Actions:

1. Schedule cost-data exports.
2. Add metadata-policy checks to CI or admission control.
3. Alert on missing ownership.
4. Alert on project budget or capacity thresholds.
5. Detect stale PVCs and namespaces.
6. Refresh AWS price assumptions.
7. Generate monthly FinOps reports.
8. Track optimization actions and realized savings.
9. Add capacity-purchase recommendations.
10. Add AWS burst recommendations.

Exit criteria:

- monthly reports require minimal manual work;
- optimization recommendations have owners and outcomes;
- the model is used in architecture and investment reviews.

[Back to table of contents](#table-of-contents)

## Validation and control framework

### Cost reconciliation

Every period should satisfy:

```text
Direct project cost
+ shared cost
+ idle cost
+ unallocated cost
+ overhead
= total modeled Kalaxy3 cost
```

Differences must be reported rather than silently discarded.

### Metadata coverage

Measure:

```text
Owned workload cost / total nonplatform workload cost
```

Target at least 95 percent before using chargeback.

### Model versioning

Each rate set should include:

- version;
- effective date;
- owner;
- source;
- method;
- confidence;
- replacement date.

Never overwrite historical rates used for closed periods.

### Review cadence

Recommended cadence:

| Review | Frequency |
|---|---|
| Data-quality check | Weekly |
| Project showback | Monthly |
| Capacity forecast | Monthly |
| Rate review | Quarterly |
| AWS price refresh | Quarterly or before major decisions |
| Hardware replacement values | Semiannually |
| Architecture review | Before major project or purchase |
| Full model policy review | Annually |

### Acceptance criteria

The model is ready for decision support when:

- total modeled cost reconciles;
- projects are consistently identified;
- shared and idle policies are documented;
- physical storage overhead is included;
- power and hardware rates have sources;
- AWS scenarios include all material services;
- results include uncertainty ranges;
- unit economics are defined for major workloads;
- reports identify model version and assumptions.

[Back to table of contents](#table-of-contents)

## Risks limitations and cautions

1. **Kubecost is not the full ledger.** It allocates Kubernetes resources but
   requires external cost and ownership data for complete TCO.
2. **The current LoadBalancer warning is nonfatal but informative.** MetalLB
   does not have native cloud-provider pricing, so load-balancer economics
   should be modeled separately.
3. **NFS and MinIO need explicit allocation.** Kubernetes pod metrics alone do
   not fully attribute their infrastructure cost.
4. **Longhorn logical capacity understates physical capacity.** Replication must
   be included.
5. **GPU cost can be distorted by low utilization.** Separate active,
   reserved, and idle GPU cost.
6. **Historical purchase cost may understate replacement economics.** Report
   both when material.
7. **Labor is difficult but cannot be ignored.** Use scenario rates when cash
   labor is not directly recorded.
8. **AWS price comparisons become stale.** Refresh before decisions.
9. **AWS service equivalence is architectural, not purely numerical.**
   Reliability and managed responsibility must be normalized.
10. **Sunk cost should not justify future waste.** Use marginal cost for
    short-term placement and replacement cost for strategic decisions.
11. **Chargeback can create bad incentives.** Begin with showback.
12. **False precision is dangerous.** Use ranges and confidence ratings.
13. **Local capacity can appear free until a threshold is crossed.** Step costs
    must be forecast.
14. **Unused resilience is not automatically waste.** Some idle capacity is
    intentional recovery or growth reserve.
15. **Cost optimization must not override safety, security, or reliability
    requirements.**

[Back to table of contents](#table-of-contents)

## Recommended initial decisions

Adopt these initial Kalaxy3 policies:

1. Use Kubecost as the Kubernetes workload-allocation engine.
2. Use a separate Kalaxy3 cost pipeline for hardware, power, labor, NFS,
   MinIO, and AWS scenarios.
3. Start with showback rather than chargeback.
4. Make `kalaxy3.io/project`, `kalaxy3.io/owner`, and
   `kalaxy3.io/environment` mandatory.
5. Keep shared and idle costs visible before distributing them.
6. Report both cash and fully loaded economic cost.
7. Use two-replica physical capacity for Longhorn economics.
8. Preserve `amd64-01` GPU and LLM capacity as a scarce resource with an
   explicit opportunity cost.
9. Compare AWS under at least rehost, managed, elastic, and hybrid scenarios.
10. Use benchmark-equivalent AWS resources.
11. Refresh AWS prices before major decisions.
12. Produce monthly project reports and quarterly architecture reviews.
13. Treat the nonfatal MetalLB pricing warning as a documented limitation,
    not as a reason to repeatedly patch the Helm-managed ConfigMap.
14. Defer detailed chargeback until ownership and reconciliation exceed the
    acceptance thresholds.
15. Define one or two unit-economic measures for each major project.

[Back to table of contents](#table-of-contents)

## Nontechnical explanation

### What we are building

We are building a fair and understandable way to answer:

> What does Kalaxy3 really cost, who is using it, what value are they getting,
> and would the same work be cheaper or better on AWS?

Kubecost is the meter inside Kubernetes. It observes which applications use
processor time, memory, storage, and other shared resources.

The complete Kalaxy3 cost model adds the bills and economic facts that the
meter cannot know, such as:

- what the computers cost;
- how much electricity they use;
- how long they are expected to last;
- how much storage protection uses;
- how much work is required to operate them;
- what equivalent AWS services would cost.

### Why it matters

Without a cost model, local hardware often looks free after it has been
purchased. AWS often looks expensive because every service appears on a bill.

That comparison is incomplete.

Kalaxy3 has costs that do not arrive as a monthly cloud invoice. AWS includes
services and responsibilities that Kalaxy3 may provide differently or may not
provide at the same level.

The model makes both sides visible so decisions are based on the same outcome.

### How it works

Each Kalaxy3 project will be given an identity.

The system will measure what that project uses:

- processor;
- memory;
- GPU;
- storage;
- network;
- shared platform services.

It will then assign a reasonable portion of shared costs such as monitoring,
the Kubernetes control plane, storage replication, backups, electricity, and
operations.

A separate calculation will describe what equivalent work would require on
AWS, including the parts that are easy to overlook, such as storage,
load balancers, monitoring, backup, public addresses, and data transfer.

### What it will tell us

The model should be able to say:

- Project A costs about this much per month.
- Project B is using very little but has reserved a large amount of memory.
- Project C will cause another disk or node purchase in three months.
- The LLM saves money locally only when the GPU is used above a certain level.
- A short, irregular job is cheaper on AWS because it can stop when finished.
- A continuous data-heavy service is cheaper on Kalaxy3 because the hardware
  is already available and cloud transfer would be expensive.
- Some spare capacity is intentional protection, while some is unnecessary
  waste.
- A proposed hardware purchase will pay for itself only under certain usage.
- A hybrid design is better than choosing only Kalaxy3 or only AWS.

### What it will not claim

The model will not claim that one platform is always cheaper.

It will not treat an old computer as economically free.

It will not claim that an AWS estimate provides the same reliability unless
the architecture actually does.

It will not pretend that every cost is known with perfect precision.

It will show assumptions, ranges, and confidence so the result can support a
decision rather than merely produce an impressive number.

[Back to table of contents](#table-of-contents)

## Conclusion

Kalaxy3 now has the technical basis for meaningful Kubernetes FinOps:
Kubecost, Prometheus, Longhorn-backed retention, project-capable Kubernetes
metadata, and reproducible Ansible deployment.

The next step is not another Kubecost installation change. It is the
construction of a governed economic model around the data Kubecost already
collects.

The resulting capability should provide:

- Kalaxy3 total cost of ownership;
- project showback;
- shared and idle cost visibility;
- capacity forecasts;
- storage and GPU economics;
- unit economics;
- AWS-equivalent scenarios;
- break-even analysis;
- hybrid-placement guidance;
- evidence-based hardware and architecture decisions.

The model will be most valuable when it is treated as a recurring operating
process rather than a one-time spreadsheet.

[Back to table of contents](#table-of-contents)

## Authoritative source basis

This document was informed by the following authoritative sources, reviewed in
July 2026:

- Kalaxy3 Kubecost installation and verification evidence.
- OpenCost Specification.
- OpenCost API documentation.
- OpenCost on-premises and Kubernetes documentation.
- AWS Well-Architected Framework.
- AWS Well-Architected Cost Optimization Pillar.
- AWS Cloud Adoption Framework overview and its Business, People, Governance,
  Platform, Security, and Operations perspectives.
- AWS Pricing Calculator documentation.
- AWS Data Exports and Cost and Usage Report 2.0 documentation.
- AWS cost-allocation tagging and Cost Categories guidance.
- Amazon EKS architecture and pricing documentation.
- Amazon EC2, EBS, EFS, S3, and Elastic Load Balancing pricing documentation.

AWS prices and product capabilities are time-sensitive. This document defines a
method for collecting them but intentionally does not make permanent cost
decisions from a static price list.
