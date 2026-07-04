# Cloud-Native & Distributed Applications — Foundations & Baseline

The **conceptual companion** to `GUIDE.md`. Where the guide is hands-on ("do this, see that"), this
document is the mental model: **what** cloud-native and distributed systems are, the **principles**
behind them, the **architecture patterns**, and the **tool ecosystem** — so you always know *why* a
tool exists before you learn *how* to use it.

Everything here favors **open-source / free** technology, matching the lab's ground rule.

> **How to use this doc:** read it once for the big picture, then treat it as a reference. The final
> section maps every concept here to the specific lab (`v1` Kafka → `v2` microservices → `v3`
> observability) so the baseline connects to what you actually build.

---

## 1. Definitions — what are we even talking about?

**Distributed application** — an app whose parts run on **multiple machines/processes** and
coordinate over a **network** to act as one system. The defining trait: *the network is now part of
your program*, and networks are slow, unreliable, and partially fail.

**Cloud-native application** — an app **designed from the start** to run in dynamic, elastic cloud
environments: packaged in containers, deployed and scaled by an orchestrator, loosely coupled,
resilient to failure, and operated through automation. Most cloud-native apps are also distributed.

**The relationship:**
- *Distributed* describes the **topology** (many nodes, one system).
- *Cloud-native* describes the **design philosophy and operating model** (containers + orchestration
  + automation + resilience) that makes distributed systems manageable.

> The official CNCF definition, paraphrased: *cloud-native technologies empower organizations to
> build and run scalable applications in modern, dynamic environments — containers, service meshes,
> microservices, immutable infrastructure, and declarative APIs — that are resilient, manageable,
> and observable, combined with automation to make high-impact changes frequently and predictably.*

---

## 2. Why cloud-native? (The problems it solves)

| Problem with traditional apps | Cloud-native answer |
|---|---|
| "Works on my machine" | **Containers** package app + deps identically everywhere |
| Manual, risky deployments | **CI/CD + automation** make releases frequent and boring |
| One big app; scale all or nothing | **Microservices** scale independently |
| A crash takes everything down | **Resilience patterns** + orchestration self-heal |
| Hard to see what's happening | **Observability** (metrics/logs/traces) |
| Wasted, static capacity | **Elastic autoscaling** matches demand |
| Slow, coupled team delivery | **Loosely coupled services** = independent teams/releases |

The trade-off: you exchange the simplicity of a single process for **operational and architectural
complexity**. Cloud-native tooling exists to *manage* that complexity — that's the whole game.

---

## 3. Core principles (the baseline mindset)

1. **Containers as the unit of deployment** — package once, run anywhere; immutable images.
2. **Microservices / loose coupling** — small services owning one capability, independently
   deployable, communicating over well-defined APIs.
3. **Immutable infrastructure** — you never patch a running server; you replace it with a new image.
   No "snowflake" servers.
4. **Declarative APIs / desired state** — you declare *what* you want (e.g. "3 replicas"); the system
   continuously reconciles reality to match. (Kubernetes' core idea.)
5. **Automation everywhere** — build, test, deploy, scale, heal — all scripted, not manual.
6. **Design for failure (resilience)** — assume everything fails; degrade gracefully, retry, isolate.
7. **Observability by default** — you cannot fix what you cannot see; instrument from day one.
8. **Statelessness where possible** — push state to backing services (DBs, caches, brokers) so app
   instances are disposable and horizontally scalable.
9. **Elasticity** — scale out/in automatically with load.
10. **Everything as code** — infra, config, pipelines, policy — all versioned in git.

### The Twelve-Factor App (the classic checklist)
A widely-used baseline for building cloud-native services:
1. **Codebase** — one repo per app, tracked in version control.
2. **Dependencies** — declared explicitly (e.g. `requirements.txt`, `pom.xml`), never assumed.
3. **Config** — in the environment (env vars), not baked into code.
4. **Backing services** — treat DBs, brokers, caches as attached resources (swappable via config).
5. **Build, release, run** — strictly separate stages.
6. **Processes** — run as stateless, share-nothing processes.
7. **Port binding** — the app is self-contained and exposes itself via a port.
8. **Concurrency** — scale out by running more processes.
9. **Disposability** — fast startup, graceful shutdown; instances are cattle, not pets.
10. **Dev/prod parity** — keep environments as similar as possible.
11. **Logs** — treat as event streams (write to stdout; let the platform aggregate).
12. **Admin processes** — run one-off tasks (migrations) as identical short-lived processes.

---

## 4. Distributed systems fundamentals (the hard truths)

Cloud-native sits on top of distributed-systems reality. Know these before you design anything:

- **The 8 fallacies of distributed computing** — the false assumptions that break systems: the
  network is (1) reliable, (2) has zero latency, (3) infinite bandwidth, (4) secure, (5) topology
  never changes, (6) one administrator, (7) zero transport cost, (8) homogeneous network. *All false.*
- **CAP theorem** — under a network **P**artition, you must choose **C**onsistency *or*
  **A**vailability; you can't have both. Most systems tune between them (see PACELC for the extended
  version covering latency in the non-partition case).
- **Consistency models** — *strong* (everyone sees the latest write immediately) vs **eventual**
  (replicas converge over time). Cloud-native leans heavily on eventual consistency for scale.
- **Partitioning / sharding** — splitting data (or a Kafka topic) across nodes for parallelism.
- **Replication** — copies for durability and availability; introduces consistency questions.
- **Idempotency** — an operation you can safely repeat with the same result. Essential because in a
  distributed system, messages get delivered **at-least-once** and you *will* see duplicates.
- **Delivery guarantees** — *at-most-once*, *at-least-once*, *exactly-once* (hard/expensive).
- **Backpressure** — a slow consumer signaling a fast producer to slow down, so nothing is
  overwhelmed. (Kafka's consumer lag is backpressure made visible.)
- **Failure is normal** — nodes die, networks drop, clocks skew. Design assuming it.

---

## 5. Architecture patterns (the shapes systems take)

**Evolution:**
- **Monolith** — one deployable unit. Simple to start; hard to scale teams and parts independently.
- **Modular monolith** — one deploy, clean internal module boundaries. A sane middle ground.
- **Microservices** — many small, independently deployable services. Powerful but operationally
  heavy — only worth it past a certain scale/team size.

**Key patterns:**
| Pattern | What it is / when to use |
|---|---|
| **API Gateway** | Single entry point that routes to services; handles auth, rate-limiting, TLS. |
| **Backend-for-Frontend (BFF)** | A gateway tailored per client type (web, mobile). |
| **Service discovery** | Services find each other dynamically (DNS, registry) instead of fixed IPs. |
| **Sidecar** | A helper container next to your app (e.g. a proxy) that adds capabilities without code changes. |
| **Service mesh** | A network of sidecars giving traffic control, mTLS, and telemetry across services. |
| **Event-driven architecture** | Services react to **events** on a broker; decoupled in time and space. |
| **Publish/Subscribe** | Producers emit events; many consumers react independently. |
| **CQRS** | Separate the write model from the read model for scale/clarity. |
| **Event sourcing** | Store the sequence of events as the source of truth; rebuild state by replay. |
| **Saga** | Manage a distributed transaction as a series of local steps with compensations. |
| **Strangler Fig** | Incrementally replace a monolith by routing slices to new services over time. |
| **Circuit breaker / bulkhead** | Resilience patterns (see §7). |

---

## 6. Communication styles

**Synchronous (request/response) — caller waits for a reply:**
- **REST/HTTP** — ubiquitous, simple, resource-oriented.
- **gRPC** — fast binary RPC over HTTP/2, strongly typed (Protobuf); great service-to-service.
- **GraphQL** — client-specified queries; flexible read APIs.
- *Trade-off:* simple mental model, but tight temporal coupling — if the callee is down/slow, the
  caller suffers. Needs resilience patterns.

**Asynchronous (messaging/streaming) — fire and continue:**
- **Message queues** (RabbitMQ, SQS) — task distribution, work queues.
- **Event streaming** (Apache Kafka, Pulsar) — durable, replayable, high-throughput event logs.
- **Lightweight pub/sub** (NATS) — fast, simple messaging.
- *Trade-off:* decoupled and resilient (broker buffers), but eventual consistency and harder
  debugging (no single call stack).

> **Rule of thumb:** use **sync** for "I need an answer now" (a query), **async** for "this happened,
> react whenever" (an event). Real systems mix both — exactly what the lab's `v2` builds.

---

## 7. Resilience patterns (design for failure)

| Pattern | What it does |
|---|---|
| **Timeout** | Don't wait forever for a slow dependency. |
| **Retry (with backoff + jitter)** | Recover from transient failures without stampeding. |
| **Circuit breaker** | After repeated failures, "trip" and fail fast instead of hammering a dead service; probe to recover. |
| **Bulkhead** | Isolate resources so one overloaded dependency can't sink the whole app. |
| **Rate limiting / throttling** | Protect services from being overwhelmed. |
| **Backpressure** | Let consumers signal producers to slow down. |
| **Graceful degradation / fallback** | Serve a reduced experience (cached/default) instead of an error. |
| **Health checks & self-healing** | Liveness/readiness probes let the orchestrator restart/replace bad instances. |
| **Idempotency + dead-letter queues** | Safely handle duplicates and quarantine "poison" messages. |

---

## 8. The tech-stack ecosystem (the CNCF landscape, organized)

The layers of a cloud-native platform, bottom to top, with the **free/OSS** options:

| Layer | Purpose | Open-source tools |
|---|---|---|
| **Containerization** | Package app + deps | **Docker**, containerd, Podman, OCI images |
| **Container registry** | Store/distribute images | Harbor, Docker Registry, GHCR |
| **Orchestration** | Schedule, scale, heal containers | **Kubernetes**, k3s, kind (local), OpenShift (OKD) |
| **Packaging/templating** | Deploy k8s apps repeatably | **Helm**, Kustomize |
| **Service mesh** | Traffic mgmt, mTLS, telemetry | Istio, Linkerd, Cilium |
| **Ingress / API gateway** | External entry, routing | NGINX Ingress, Traefik, Kong, Spring Cloud Gateway |
| **Messaging / streaming** | Async comms, event backbone | **Apache Kafka**, RabbitMQ, NATS, Apache Pulsar |
| **Databases** | Persistent state | PostgreSQL, MySQL, MongoDB, Cassandra |
| **Caching** | Fast reads, offload DBs | Redis, Memcached |
| **CI/CD** | Automate build → deploy | Jenkins, GitHub Actions, GitLab CI, Tekton, Argo Workflows |
| **GitOps** | Git as deployment source of truth | Argo CD, Flux |
| **Infrastructure as Code** | Provision infra declaratively | Terraform/OpenTofu, Pulumi, Ansible |
| **Observability — metrics** | Numbers over time | **Prometheus**, Grafana |
| **Observability — logs** | Detailed events | Loki, Elasticsearch/OpenSearch, Fluent Bit |
| **Observability — traces** | Per-request paths | **OpenTelemetry**, Jaeger, Tempo, Zipkin |
| **Autoscaling** | Scale on demand/events | HPA, VPA, **KEDA** (event/lag-driven), Cluster Autoscaler |
| **Secrets / config** | Manage sensitive config | Vault, Sealed Secrets, External Secrets, k8s ConfigMaps/Secrets |
| **Security / policy** | Guardrails, supply chain | OPA/Gatekeeper, Kyverno, Falco, Trivy, cosign |
| **Serverless / FaaS** | Event-driven functions | Knative, OpenFaaS |

> **CNCF** (Cloud Native Computing Foundation) is the neutral home for many of these projects
> (Kubernetes, Prometheus, Envoy, OpenTelemetry, etc.). Its "landscape" map is the canonical survey
> of the ecosystem — huge, but this table is the baseline slice that matters most.

---

## 9. Kubernetes — the baseline vocabulary

Because k8s is the center of gravity, know these core objects:

- **Pod** — the smallest deployable unit; one or more containers sharing network/storage.
- **Deployment** — declares desired replicas of a pod; handles rollouts and self-healing.
- **Service** — a stable network name + load balancer in front of a set of pods.
- **Ingress** — routes external HTTP traffic to Services.
- **ConfigMap / Secret** — externalized config and sensitive values.
- **Namespace** — a virtual cluster for isolating groups of resources.
- **Node** — a worker machine (VM/physical) running pods.
- **Controller / reconciliation loop** — the engine that continuously drives actual state → desired
  state. This *is* the declarative principle in action.
- **StatefulSet / PersistentVolume** — for stateful workloads (databases, brokers) that need stable
  identity and storage.

---

## 10. Data in distributed systems

- **Database-per-service** — each microservice owns its data; others access it only via that
  service's API (no shared tables). Preserves loose coupling.
- **Polyglot persistence** — pick the right store per job (relational, document, key-value, graph,
  time-series).
- **Distributed transactions are hard** — avoid two-phase commit; prefer **sagas** and eventual
  consistency.
- **The outbox pattern** — reliably publish events *and* commit DB changes atomically.
- **Migrations as code** — schema changes versioned and applied automatically (e.g. Flyway/Liquibase).

---

## 11. How this baseline maps to the learning lab

Everything above is abstract until you build it. Here's where each piece shows up in the roadmap:

| Baseline concept | Where you learn it | Lab version |
|---|---|---|
| Containers (Docker), images, registries | Building/running producer & consumer images | **v1** |
| Event streaming, partitioning, pub/sub, consumer groups | Apache Kafka core | **v1** |
| Delivery guarantees, backpressure, idempotency | Kafka lag & rebalancing experiments | **v1** |
| Orchestration (Kubernetes objects, declarative state, self-healing) | kind cluster, Deployments/Services, `kubectl scale` | **v1 (Phase 5)** |
| Event-driven autoscaling (KEDA) | Lag-based autoscaling | **v1.1** |
| Data contracts, schema evolution, dead-letter queues | Schema Registry + DLT | **v1.2** |
| Microservices, API gateway, service discovery | Spring Boot ecosystem | **v2** |
| Sync vs async communication (REST + Kafka together) | order/inventory/notification services | **v2** |
| Resilience patterns (circuit breaker, retry, bulkhead) | Resilience4j experiments | **v2** |
| Database-per-service, migrations | Postgres + JPA + Flyway | **v2** |
| Observability — metrics, logs, traces | Prometheus/Grafana/Loki/OpenTelemetry | **v3** |
| RED/USE methods, alerting, correlation | Dashboards + trace↔log↔metric | **v3** |

> **The point:** by the end of the roadmap you'll have *touched* every layer of §8 with a real,
> running, observable system — the baseline turned into muscle memory.

---

## 12. Glossary (quick reference)

- **Broker** — a server that stores and routes messages/events (e.g. a Kafka node).
- **Consumer group** — a set of consumers that share the work of reading a topic.
- **Declarative** — you specify the desired end state, not the steps to get there.
- **Elasticity** — automatic scaling with demand.
- **Eventual consistency** — replicas converge to the same state over time, not instantly.
- **Idempotent** — safe to apply the same operation multiple times.
- **Immutable infrastructure** — servers/images are replaced, never modified in place.
- **Lag** — how far behind a consumer is from the latest messages (a health/backpressure signal).
- **Orchestrator** — software that schedules and manages containers (Kubernetes).
- **Reconciliation loop** — continuously drives actual state toward desired state.
- **Sidecar** — a helper container attached to an app to add capabilities transparently.
- **Stateless** — holds no local state between requests; disposable and horizontally scalable.
- **Service mesh** — an infrastructure layer (usually sidecars) handling service-to-service comms.

---

## Further reading (all free)
- **The Twelve-Factor App** — https://12factor.net
- **CNCF Cloud Native Landscape** — https://landscape.cncf.io
- **Kubernetes docs** — https://kubernetes.io/docs
- **Apache Kafka docs** — https://kafka.apache.org/documentation
- *Fallacies of Distributed Computing*, *CAP theorem* — searchable classics worth a read.

> This is the **baseline**. The `GUIDE.md` lab manual is where you make it real.
