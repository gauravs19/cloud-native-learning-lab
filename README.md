# Cloud-Native Learning Lab

A personal, hands-on lab for learning the **cloud-native / distributed systems** stack by building
real systems and watching how they behave — **Kafka, Spring Boot, Docker, and Kubernetes**, growing
over time. Built entirely on **open-source / free** tooling.

> Learning project, not a product. Grown in versioned batches (SemVer) as a monorepo.

## 📚 The two documents

| File | What it is |
|---|---|
| **[FOUNDATIONS.md](FOUNDATIONS.md)** | The concepts — cloud-native & distributed-systems principles, architecture patterns, and the tool ecosystem. Read this first for the *why*. |
| **[GUIDE.md](GUIDE.md)** | The hands-on lab manual — step-by-step exercises with setup, commands, expected output, and checkpoints. This is the *how*. |

## 🗺️ Roadmap

| Version | Focus | Status |
|---|---|---|
| **v1.0** | Kafka core — partitioning, consumer groups, rebalancing, Docker → Kubernetes | building |
| v1.1 | KEDA lag-based autoscaling | planned |
| v1.2 | Schema Registry + Avro, dead-letter topics | planned |
| **v2.0** | Spring Boot microservices ecosystem (gateway, config, resilience, persistence) | planned |
| **v3.0** | Observability — metrics, logs, traces (Prometheus / Grafana / OpenTelemetry) | planned |

## 🧰 Tech stack (all open-source)

Apache Kafka · Python + FastAPI · Spring Boot (Java 21) · Docker (Rancher Desktop) · Kubernetes (kind)
· and more as the roadmap grows. See [FOUNDATIONS.md §8](FOUNDATIONS.md) for the full ecosystem map.

## 📂 Layout

```
cloud-native-learning-lab/
├── FOUNDATIONS.md          # concepts & baseline
├── GUIDE.md                # hands-on lab manual
└── labs/
    ├── 01-kafka/           # v1.x
    ├── 02-spring-microservices/   # v2.x
    └── 03-observability/   # v3.x
```

## 🚀 Getting started

1. Read **[FOUNDATIONS.md](FOUNDATIONS.md)** for the big picture.
2. Open **[GUIDE.md](GUIDE.md)** and work through **Lab 1 (v1.0)** — it starts with a from-scratch
   Windows environment setup, then Kafka on Docker, then on Kubernetes.

---

*Personal learning project — shared openly, but not seeking contributions.*
