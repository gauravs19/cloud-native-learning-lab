# Cloud-Native Learning Lab — Lab Manual

A hands-on, follow-along manual for learning the **cloud-native / microservices** stack by
building real systems and *observing* how they behave. Managed as a **monorepo**, grown in
**versioned batches** (SemVer), built **entirely on open-source / free tooling**.

> **Manual version:** `v1.0.0` · **Platform:** Windows 11/10 (PowerShell) · **Assumes:** no prior
> Docker/Kafka/Kubernetes experience — every install and validation step is spelled out.

> **How this manual works:** each numbered **Exercise** is a small unit of work with a clear
> action, an expected result, and a checkpoint. Do them in order. Don't move past a
> **✅ CHECKPOINT** until you've seen the expected result — that's how you know it clicked.

---

## How to use this manual (conventions)

| Marker | Meaning |
|---|---|
| 🎯 **Objectives** | What you'll be able to do after the lab |
| 🧰 **Setup** | Tools/files you need before starting |
| ▶️ **Do** | An action to perform |
| 💻 (code block) | The exact command or file contents |
| 👀 **Expect** | What you should see if it worked |
| 📝 **Record** | Write down what you observed (fill-in table) — this is how you learn |
| 🧠 **Why** | The concept behind the step |
| ✅ **CHECKPOINT** | Stop and verify before continuing |
| 🧹 **Cleanup** | How to tear it down |

**Tips before you start**
- Keep **two terminals** open: one to run commands, one to tail logs.
- Keep **Kafka UI** (http://localhost:8080) open in a browser once it's up.
- When a step says *Record*, actually write it in the table. The tables are the point.

---

## Ground rules

1. **Open-source / free only** — no paid licenses or expiring trials. Docker Desktop is avoided
   in favor of **Docker Engine / Rancher Desktop**.
2. **Monorepo** — one lab per numbered folder under `labs/`; each lab is self-contained.
3. **SemVer batches** — MAJOR = new lab, MINOR = addition within a lab, PATCH = fix.
4. **Learn by observing** — every exercise ends in something you can see and record.

## Roadmap at a glance

| Version | Folder | Focus | Status |
|---|---|---|---|
| **v1.0** | `labs/01-kafka` | Kafka partitioning, consumer groups, rebalancing, Docker → Kubernetes | **performable now** |
| v1.1 | `labs/01-kafka` | KEDA lag-based autoscaling | preview |
| v1.2 | `labs/01-kafka` | Schema Registry + Avro, dead-letter topics | preview |
| **v2.0** | `labs/02-spring-microservices` | Spring Boot microservices ecosystem | preview |
| **v3.0** | `labs/03-observability` | Metrics, logs, traces over the whole stack | preview |

## Monorepo layout

```
cloud-native-learning-lab/
├── GUIDE.md                       ← this lab manual
├── README.md                      ← short index (create when scaffolding)
├── labs/
│   ├── 01-kafka/                  ← LAB 1 (v1.x)
│   │   ├── docker-compose.yml
│   │   ├── producer/              ← Python FastAPI producer
│   │   ├── consumer/              ← Spring Boot consumer
│   │   └── k8s/                   ← kind manifests
│   ├── 02-spring-microservices/   ← LAB 2 (v2.x)
│   └── 03-observability/          ← LAB 3 (v3.x)
└── shared/                        ← cross-lab helpers (only if needed)
```

> **All commands in Lab 1 assume this working directory:**
> `cd D:\__claude\cloud-native-learning-lab\labs\01-kafka`

---
---

# LAB 1 — Kafka core

| | |
|---|---|
| **Lab version** | `v1.0.0` |
| **Folder** | `labs/01-kafka` |
| **Depends on** | nothing (start here) |
| **Add-ons** | `v1.1` KEDA autoscaling · `v1.2` Schema Registry + DLT (previews below) |
| **Status** | performable now |

### 🎯 Objectives
By the end of this lab you will be able to:
1. Run Apache Kafka (KRaft, single node) and Kafka UI locally with Docker Compose.
2. Explain and demonstrate **why parallelism = `min(partitions, consumers)`**.
3. Produce keyed events and show that **same key → same partition**.
4. Scale consumers and **watch a live rebalance**; prove idle consumers past the partition count.
5. Add partitions live and observe **key remapping** + Kafka's refusal to shrink partitions.
6. Reproduce the entire system on real **Kubernetes** with `kind` and `kubectl scale`.

### ⏱️ Estimated time
2–3 hours (Phases 1–4 ≈ 90 min; Phase 5 Kubernetes ≈ 60 min).

### 🧠 The one rule that explains everything
> **Within one consumer group, each partition is consumed by exactly one consumer at a time.**
> So effective parallelism = `min(partitions, consumers)`.

| Partitions | Consumers | Result |
|-----------:|----------:|--------|
| 3 | 1 | one consumer does all the work |
| 3 | 3 | perfect spread — 1 partition each |
| 3 | 5 | **2 consumers sit idle** (partitions cap it) |
| 6 | 5 | all busy; one consumer handles 2 partitions |

You will *prove each of these rows yourself* in the experiments.

---

## Exercise 1.0 — Set up your Windows environment (from scratch)

This exercise assumes a **fresh Windows machine with nothing installed**. You'll install each tool,
then immediately **validate** it before moving on. Do the sub-steps in order — later tools depend on
earlier ones.

> **Golden rule for Windows installs:** after installing anything that adds a command, **close and
> reopen PowerShell** (or open a new tab). New tools are added to your `PATH`, and an already-open
> terminal won't see them until it restarts. If a freshly installed command says *"not recognized"*,
> 90% of the time you just need a new terminal.

### 1.0.a — Open PowerShell (your main tool)

▶️ **Do.** Press `Win`, type **PowerShell**, and click **Windows PowerShell**. For installs you'll
sometimes need admin: right-click → **Run as administrator**.

▶️ **Do (validate).**
```powershell
$PSVersionTable.PSVersion    # shows your PowerShell version
```
👀 **Expect.** A version number (5.1 or higher is fine).
✅ **CHECKPOINT 1.0.a.** PowerShell opens and prints a version.

### 1.0.b — Confirm `winget` (the Windows package manager)

`winget` comes built into Windows 11 and recent Windows 10. We use it to install most tools.

▶️ **Do (validate).**
```powershell
winget --version
```
👀 **Expect.** A version like `v1.x.x`.
🛠️ **If "not recognized":** install **App Installer** from the Microsoft Store (search "App
Installer"), then reopen PowerShell and retry.
✅ **CHECKPOINT 1.0.b.** `winget --version` prints a version.

### 1.0.c — Install Docker (via Rancher Desktop — OSS, no license)

Docker runs all our containers. We use **Rancher Desktop** (fully open-source) to avoid Docker
Desktop's licensing terms. It provides the `docker` command.

▶️ **Do (install).**
```powershell
winget install --id SUSE.RancherDesktop -e
```
*(Alternative — Docker Desktop, free for personal use: `winget install --id Docker.DockerDesktop -e`.
Either gives you the `docker` command; the rest of the manual is identical.)*

▶️ **Do (first-run setup).**
1. Launch **Rancher Desktop** from the Start menu.
2. When prompted, choose container engine **dockerd (moby)** — this is what gives the `docker` CLI.
3. Wait for the whale/status to show **running** (first start downloads components — a few minutes).
4. **Close and reopen PowerShell** so `docker` is on your PATH.

▶️ **Do (validate).**
```powershell
docker --version
docker run --rm hello-world
```
👀 **Expect.** `docker --version` prints a version; `hello-world` prints *"Hello from Docker!"*.

🛠️ **If it fails — common Windows first-run snags (in order):**

1. **`WSL … is too old` / `wsl.exe exited with code 1`** — the WSL platform predates the engine.
   This blocks Rancher Desktop's first-run setup entirely. Fix:
   ```powershell
   wsl --update
   wsl --version        # confirm it bumped (want 2.2+; newer is fine)
   wsl --shutdown       # restart WSL cleanly
   ```
   Then fully quit and reopen Rancher Desktop so it re-provisions on the updated WSL.
2. **Engine not started yet** — Rancher Desktop can take a few minutes on first start (it also
   brings up its own Kubernetes). Wait until the app shows **running**. You can restart its backend
   from a terminal with `rdctl shutdown` then `rdctl start`.
3. **`docker` not recognized** *and/or* **`error getting credentials … docker-credential-wincred …
   executable file not found`** — Rancher Desktop's bin folder isn't on your PATH (its automatic
   PATH integration didn't run — often a side effect of snag #1). Both the `docker` CLI *and* its
   credential helper live there. Add it to your **user PATH** (no admin needed):
   ```powershell
   $rbin = "C:\Program Files\Rancher Desktop\resources\resources\win32\bin"
   [Environment]::SetEnvironmentVariable("Path",
     ([Environment]::GetEnvironmentVariable("Path","User").TrimEnd(';') + ";" + $rbin), "User")
   ```
   Then **open a new PowerShell** (PATH changes only apply to new terminals) and retry.
4. **Podman also installed?** If you see errors mentioning `podman-machine-default`, you have Podman
   *and* Rancher Desktop competing over WSL. For this lab you only need Rancher Desktop — quit or
   uninstall Podman Desktop, or just leave its (stopped) machine alone once WSL is updated.

✅ **CHECKPOINT 1.0.c.** `hello-world` prints its greeting **from a freshly opened terminal**. This
proves Docker actually works — the most important checkpoint in setup.

> 🧠 **Why dockerd (moby), not containerd?** Rancher Desktop offers two engines:
> **dockerd (moby)** gives you the classic `docker` / `docker compose` CLI; **containerd** is the
> leaner CNCF runtime you drive with `nerdctl` instead. We choose **dockerd** because:
> 1. **This manual is written in `docker` commands** — every `docker compose up`, `docker build`,
>    `docker exec` works verbatim. With containerd you'd translate each to `nerdctl`, which is
>    *mostly* compatible but not identical — needless friction while you're learning Kafka/k8s.
> 2. **`kind` (Phase 5) assumes a Docker-compatible daemon** — `docker build` + `kind load
>    docker-image` is smoothest on dockerd.
> 3. **`docker compose` is first-class** on dockerd, and Compose drives Phases 1–4.
>
> The nice nuance: containerd isn't being avoided — it's the *more* cloud-native runtime, and the
> containers **inside** your `kind` cluster (Phase 5) are run by containerd automatically, no matter
> what you pick here. So: **host CLI = Docker (for convenience), in-cluster runtime = containerd.**
> If you'd rather use `nerdctl`/containerd as your host engine too, it works — you'd just translate
> the `docker` commands.

### 1.0.d — Install Python 3.12

The producer is a Python app.

▶️ **Do (install).**
```powershell
winget install --id Python.Python.3.12 -e
```
▶️ **Do.** Close and reopen PowerShell.

▶️ **Do (validate).**
```powershell
python --version
pip --version
```
👀 **Expect.** `Python 3.12.x` and a `pip` version.
🛠️ **If "not recognized":** reopen the terminal; if still failing, re-run the installer and ensure
**"Add python.exe to PATH"** is checked.
✅ **CHECKPOINT 1.0.d.** Both `python` and `pip` report versions.

### 1.0.e — Install Java 21 (OpenJDK LTS)

The consumer is a Spring Boot (Java) app. We use **Java 21** — the current LTS (Long-Term Support)
release, modern (adds virtual threads) and fully supported by the Spring Boot version in this lab.
*(17 is the older LTS floor; 25 is the newest LTS but would need a newer Spring Boot.)*

▶️ **Do (install).**
```powershell
winget install --id Microsoft.OpenJDK.21 -e
```
▶️ **Do.** Close and reopen PowerShell.

▶️ **Do (validate).**
```powershell
java -version
```
👀 **Expect.** Version text mentioning `21` (e.g. `openjdk version "21.0.x"`).
🛠️ **If "not recognized":** reopen the terminal. If it persists, check `JAVA_HOME` isn't pointing at
an old JDK: `echo $env:JAVA_HOME`.
✅ **CHECKPOINT 1.0.e.** `java -version` shows a 21.x version.

### 1.0.f — Install kubectl (Kubernetes CLI)

`kubectl` is how you talk to any Kubernetes cluster.

▶️ **Do (install).**
```powershell
winget install --id Kubernetes.kubectl -e
```
▶️ **Do.** Close and reopen PowerShell.

▶️ **Do (validate).**
```powershell
kubectl version --client
```
👀 **Expect.** A client version (e.g. `Client Version: v1.3x.x`). *(It's normal to see a note that it
can't reach a server yet — you have no cluster until Phase 5.)*
✅ **CHECKPOINT 1.0.f.** `kubectl version --client` prints a client version.

### 1.0.g — Install kind (Kubernetes-in-Docker)

`kind` runs a real Kubernetes cluster inside Docker — free, local, disposable.

▶️ **Do (install).**
```powershell
winget install --id Kubernetes.kind -e
```
▶️ **Do.** Close and reopen PowerShell.

▶️ **Do (validate).**
```powershell
kind version
```
👀 **Expect.** A version like `kind v0.2x.x`.
✅ **CHECKPOINT 1.0.g.** `kind version` prints a version. *(kind needs Docker running — which you
already validated in 1.0.c.)*

### 1.0.h — Confirm `curl.exe` (already on Windows — use `curl.exe`, not `curl`)

You'll use curl to hit the producer's REST API. **Windows 10/11 ships it built-in — nothing to
install.** But there's a critical PowerShell gotcha:

> ⚠️ **In PowerShell, `curl` is an alias for `Invoke-WebRequest`, not the real curl.** So
> `curl --version` becomes `Invoke-WebRequest --version` and fails with
> *"The remote name could not be resolved: '--version'"*. **Always call `curl.exe`** (with the
> `.exe`) to get the real tool. This matters for every curl command in this manual — they all use
> `-X`, `-H`, `-d` flags that only the real curl understands.

▶️ **Do (validate).**
```powershell
curl.exe --version
```
👀 **Expect.** A `curl 8.x.x` (or `7.x.x`) version line — **not** a web error.
🛠️ **If truly missing** (very old Windows): `winget install --id cURL.cURL -e`, then reopen the
terminal. You still call it as `curl.exe`.
✅ **CHECKPOINT 1.0.h.** `curl.exe --version` prints a version.

### 1.0.i — (Optional) A code editor

Any text editor works, but **VS Code** (free/OSS) makes editing the project files pleasant:
```powershell
winget install --id Microsoft.VisualStudioCode -e
```

### 1.0 — Final environment record

📝 **Record** the version of each tool. Every row must be filled before you start Phase 1.

| Tool | Command | Version you have | OK? |
|---|---|---|---|
| Docker | `docker --version` |  |  |
| Docker works | `docker run --rm hello-world` | (greeting seen?) |  |
| Python | `python --version` |  |  |
| pip | `pip --version` |  |  |
| Java | `java -version` |  |  |
| kubectl | `kubectl version --client` |  |  |
| kind | `kind version` |  |  |
| curl | `curl.exe --version` |  |  |

✅ **CHECKPOINT 1.0 (gate).** Every tool reports a version **and** `docker run hello-world` printed
its greeting. Do not continue to Phase 1 until this whole table is filled.

---

## Phase 1 — Kafka + Kafka UI running locally

Goal: get Kafka up and *see* it in a browser before writing any code.

### Exercise 1.1 — Create the Compose file

▶️ **Do.** Create `labs/01-kafka/docker-compose.yml`:
```yaml
services:
  kafka:
    image: apache/kafka:3.8.0
    container_name: kafka
    ports:
      - "9092:9092"      # internal listener (for containers)
      - "29092:29092"    # host listener (for apps running on your laptop)
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093,PLAINTEXT_HOST://:29092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
```

🧠 **Why — every knob that matters:**
- `KAFKA_PROCESS_ROLES: broker,controller` — this one node is both the data broker and the Raft
  controller (KRaft mode). No ZooKeeper. In production these roles are separated.
- **Three listeners** — Kafka exposes multiple endpoints, each with a purpose:
  `PLAINTEXT` (`:9092`) between containers, `CONTROLLER` (`:9093`) internal Raft only,
  `PLAINTEXT_HOST` (`:29092`) for apps on your Windows host outside Docker.
- `KAFKA_ADVERTISED_LISTENERS` — the addresses Kafka *hands back* to clients so they know where to
  reconnect. This is the #1 cause of Kafka connection pain; hence two names (`kafka` vs `localhost`).
- `KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"` — on purpose, so you create topics explicitly and see
  clear "topic not found" errors instead of silent creation.
- Replication factors `1` — single node, nothing to replicate (prod uses 3).

### Exercise 1.2 — Start Kafka & Kafka UI

▶️ **Do.**
```powershell
cd D:\__claude\cloud-native-learning-lab\labs\01-kafka
docker compose up -d kafka kafka-ui
docker compose ps
docker compose logs -f kafka   # Ctrl+C once you see "Kafka Server started"
```

👀 **Expect.** `docker compose ps` shows `kafka` and `kafka-ui` both **running**. The logs print
`Kafka Server started`.

▶️ **Do.** Open **http://localhost:8080**.

👀 **Expect.** Cluster `local`, **1 broker**, **0 topics**.

📝 **Record.**

| Check | Observed |
|---|---|
| kafka container state |  |
| kafka-ui container state |  |
| Brokers shown in UI |  |
| Topics shown in UI |  |

✅ **CHECKPOINT 1.2.** Kafka UI loads and shows 1 broker, 0 topics.

### Exercise 1.3 — Create your first topic (3 partitions)

▶️ **Do.**
```powershell
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 `
  --create --topic events --partitions 3 --replication-factor 1

docker exec -it kafka /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 --describe --topic events
```

🧠 **Why.** `--describe` prints each partition's *leader*, *replicas*, and *in-sync replicas
(ISR)*. On a single node all point at broker 1 — read it now so it makes sense when you add nodes later.

👀 **Expect.** `--describe` lists partitions `events-0`, `events-1`, `events-2`, all Leader: 1.
Refresh Kafka UI → topic `events` with 3 partitions.

📝 **Record.** Partition count shown in UI: ______   Leader of each partition: ______

✅ **CHECKPOINT 1.3 — Phase 1 done.** Topic `events` with 3 partitions is visible in the browser.

---

## Phase 2 — Python producer (FastAPI)

### Exercise 2.1 — Create the producer files

▶️ **Do.** Create `producer/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
confluent-kafka==2.5.3
```

▶️ **Do.** Create `producer/app.py`:
```python
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("KAFKA_TOPIC", "events")

producer = Producer({"bootstrap.servers": BOOTSTRAP})
app = FastAPI(title="Kafka Learning Producer")


class Event(BaseModel):
    key: str          # partition key, e.g. a userId / orderId
    message: str


def _delivery(err, msg):
    if err:
        print(f"DELIVERY FAILED: {err}")
    else:
        print(f"delivered key={msg.key()} -> partition {msg.partition()} offset {msg.offset()}")


@app.post("/publish")
def publish(event: Event):
    payload = json.dumps({"message": event.message})
    # KEY DECIDES THE PARTITION: Kafka hashes the key -> same key = same partition
    producer.produce(TOPIC, key=event.key, value=payload, callback=_delivery)
    producer.flush()
    return {"status": "sent", "key": event.key}


@app.post("/publish-bulk")
def publish_bulk(count: int = 30):
    """Send `count` events across keys user-0..user-9 to watch partition spread."""
    for i in range(count):
        key = f"user-{i % 10}"
        producer.produce(TOPIC, key=key, value=json.dumps({"n": i}), callback=_delivery)
    producer.flush()
    return {"status": "sent", "count": count}


@app.get("/health")
def health():
    return {"ok": True}
```

🧠 **Why — the ideas hiding here:**
- **The `key` is the whole lesson.** Kafka computes `hash(key) % partitions` to pick a partition.
  Same key → same partition → **ordering preserved for that key**. No key → round-robin.
- `_delivery` prints the *actual* partition and offset — your proof of the hash.
- `BOOTSTRAP` defaults to `localhost:29092` (host listener) for laptop runs; overridden to
  `kafka:9092` in Docker/k8s.

▶️ **Do.** Create `producer/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
🧠 **Why.** `requirements.txt` is copied/installed before `app.py` so Docker caches the slow pip
layer and only re-runs it when dependencies change.

### Exercise 2.2 — Local smoke test (optional but recommended)

▶️ **Do.**
```powershell
cd producer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload    # uses localhost:29092 — Kafka must be up from Phase 1
```
▶️ **Do.** In a second terminal:
```powershell
curl.exe -X POST http://localhost:8000/publish -H "Content-Type: application/json" -d '{\"key\":\"user-1\",\"message\":\"hello\"}'
```
▶️ **Do.** Repeat the same command 3 times, then change the key to `user-7` and run 3 more.

👀 **Expect.** uvicorn logs `delivered key=user-1 -> partition X`. Same key → **same partition
every time**; different key → possibly a different partition.

📝 **Record.**

| Key | Partition seen (run 1) | (run 2) | (run 3) | Consistent? |
|---|---|---|---|---|
| user-1 |  |  |  |  |
| user-7 |  |  |  |  |

✅ **CHECKPOINT 2.2 — Phase 2 done.** Same key always lands on the same partition.

---

## Phase 3 — Spring Boot consumer

### Exercise 3.1 — Create the consumer project

▶️ **Do.** Create `consumer/pom.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.4</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>consumer</artifactId>
    <version>1.0.0</version>
    <properties>
        <java.version>21</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```
🧠 **Why.** The `starter-parent` manages dependency versions (you don't pin `spring-kafka`). The
maven plugin builds the runnable fat jar used by the Dockerfile. Deps are minimal now — **v2 adds
actuator, web, JPA, etc.**

▶️ **Do.** Create `consumer/src/main/resources/application.yml`:
```yaml
spring:
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP:localhost:29092}
    consumer:
      group-id: ${KAFKA_GROUP:event-consumers}
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    listener:
      # threads per pod = extra consumers in the group. Start at 1 so pod count == consumer count.
      concurrency: ${KAFKA_CONCURRENCY:1}

app:
  topic: ${KAFKA_TOPIC:events}
  # a fake work delay (ms) so you can watch lag build up and clear
  process-delay-ms: ${PROCESS_DELAY_MS:200}
```
🧠 **Why — the settings that matter:**
- `${VAR:default}` — every value can be overridden by an env var in Docker/k8s.
- `auto-offset-reset: earliest` — a *new* group reads from the start of the topic (see all messages).
- `concurrency` — listener threads per pod; **each thread is a separate consumer in the group.**
  Start at 1 so *pods = consumers*; you'll change it deliberately in Experiment D.
- `process-delay-ms` — a fake `Thread.sleep` so **lag** is visible before it drains.

▶️ **Do.** Create `consumer/src/main/java/com/example/consumer/ConsumerApplication.java`:
```java
package com.example.consumer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ConsumerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConsumerApplication.class, args);
    }
}
```

▶️ **Do.** Create `consumer/src/main/java/com/example/consumer/EventListener.java`:
```java
package com.example.consumer;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

@Component
public class EventListener {

    @Value("${app.process-delay-ms}")
    private long delayMs;

    // The pod's hostname — in k8s this is the pod name, so you can SEE which pod got which partition.
    private final String pod = System.getenv().getOrDefault("HOSTNAME", "local");

    @KafkaListener(topics = "${app.topic}", groupId = "${spring.kafka.consumer.group-id}")
    public void onMessage(ConsumerRecord<String, String> record,
                          @Header(KafkaHeaders.RECEIVED_PARTITION) int partition) throws InterruptedException {
        Thread.sleep(delayMs); // simulate work so lag is observable
        System.out.printf("[pod=%s] partition=%d offset=%d key=%s value=%s%n",
                pod, partition, record.offset(), record.key(), record.value());
    }
}
```
> 🔍 **The `[pod=...] partition=...` log line is your microscope.** When you scale pods or add
> partitions, tail these logs and watch which pod owns which partition — that's rebalancing, live.

▶️ **Do.** Create `consumer/Dockerfile` (multi-stage):
```dockerfile
# ---- build stage ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q clean package -DskipTests

# ---- run stage ----
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/consumer-1.0.0.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```
🧠 **Why.** Build stage has Maven+JDK (big); run stage has only a JRE + jar (small).
`dependency:go-offline` is a cached layer so Maven doesn't re-download on every code change.
You'll reuse this pattern for every Spring service in Lab 2.

✅ **CHECKPOINT 3.1 — Phase 3 files created.** All consumer files exist. (It builds in Phase 4.)

---

## Phase 4 — Run the whole system + experiments

### Exercise 4.1 — Add producer & consumer to Compose

▶️ **Do.** Append to `docker-compose.yml` (same indentation as `kafka`):
```yaml
  producer:
    build: ./producer
    container_name: producer
    ports:
      - "8000:8000"
    environment:
      KAFKA_BOOTSTRAP: kafka:9092    # internal listener — producer is a container now
      KAFKA_TOPIC: events
    depends_on:
      - kafka

  consumer:
    build: ./consumer
    environment:
      KAFKA_BOOTSTRAP: kafka:9092
      KAFKA_GROUP: event-consumers
      KAFKA_TOPIC: events
      KAFKA_CONCURRENCY: "1"
      PROCESS_DELAY_MS: "200"
    depends_on:
      - kafka
    # NOTE: no container_name here, so we can scale it to multiple instances
```
🧠 **Why.** The producer now uses `kafka:9092` (it's a container). The consumer has **no
`container_name`** — Compose can only scale services without a fixed name, and scaling is exactly
what Experiment B needs.

▶️ **Do.**
```powershell
docker compose up -d --build
docker compose ps
```
👀 **Expect.** `kafka`, `kafka-ui`, `producer`, and one `consumer` all running.

✅ **CHECKPOINT 4.1.** All four services up; the consumer built without errors.

### Exercise 4.2 — EXPERIMENT A: partition distribution

▶️ **Do.**
```powershell
curl.exe -X POST "http://localhost:8000/publish-bulk?count=30"
docker compose logs consumer
```
👀 **Expect.** ~30 log lines across partitions 0/1/2; each key consistently on one partition. In
Kafka UI → Topics → `events` → Messages, each partition's offset has grown.

📝 **Record.**

| Partition | # messages seen | Example key on it |
|---|---|---|
| events-0 |  |  |
| events-1 |  |  |
| events-2 |  |  |

✅ **CHECKPOINT A.** Keys are spread across 3 partitions; each key stays on one partition.

### Exercise 4.3 — EXPERIMENT B: scale consumers, watch rebalancing

▶️ **Do.** Scale to 3 (topic has 3 partitions → perfect 1:1):
```powershell
docker compose up -d --scale consumer=3
docker compose logs -f consumer
```
👀 **Expect.** Log lines: `Revoking previously assigned partitions` then `partitions assigned:
[events-0]` etc. Each consumer gets ~1 partition.

▶️ **Do.** Scale to 5 — more consumers than partitions:
```powershell
docker compose up -d --scale consumer=5
docker compose logs consumer | Select-String "partitions assigned"
```
👀 **Expect.** **2 consumers get `[]` (idle).** That's `min(3, 5) = 3` proven.

📝 **Record.**

| # consumers | # with a partition | # idle | Matches min(3,N)? |
|---|---|---|---|
| 3 |  |  |  |
| 5 |  |  |  |

🔍 In Kafka UI → **Consumers → event-consumers**: note members, assignment, and **lag** per partition.

✅ **CHECKPOINT B.** With 5 consumers and 3 partitions, exactly 2 are idle.

### Exercise 4.4 — EXPERIMENT C: add partitions live

▶️ **Do.**
```powershell
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 --alter --topic events --partitions 6
docker compose logs -f consumer   # watch a rebalance kick in
```
👀 **Expect.** A rebalance; the previously-idle consumers now get partitions (5 consumers cover 6
partitions). Send more bulk messages — a key like `user-3` may now map to a **different** partition.

▶️ **Do.** Try to shrink partitions:
```powershell
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 --alter --topic events --partitions 2
```
👀 **Expect.** **Error** — Kafka refuses. You cannot shrink partitions.

📝 **Record.** Idle consumers after going to 6 partitions: ______   Did a key remap? (Y/N) ______
Shrink error message: __________________________

🧠 **Why it matters.** Per-key ordering across a partition change is **not** guaranteed — the big
lesson of live re-partitioning.

✅ **CHECKPOINT C.** Idle consumers lit up at 6 partitions; shrink was rejected.

### Exercise 4.5 — EXPERIMENT D: concurrency inside one pod

▶️ **Do.** Set `KAFKA_CONCURRENCY: "3"` on the consumer in `docker-compose.yml`, then:
```powershell
docker compose up -d --scale consumer=1 --build
docker compose logs consumer | Select-String "partitions assigned"
```
👀 **Expect.** One consumer container runs **3 listener threads** = 3 consumers in the group =
covers 3 partitions alone.

📝 **Record.** Partitions covered by the single container: ______

✅ **CHECKPOINT D — Kafka concepts done.** `concurrency` multiplies effective consumers per pod.
Now Kubernetes.

---

## Phase 5 — Kubernetes with kind

`kind` runs a real Kubernetes cluster inside Docker containers. Fully open-source.

### Exercise 5.1 — Create the kind cluster config

▶️ **Do.** Create `k8s/kind-cluster.yaml`:
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080   # kafka-ui NodePort
        hostPort: 8080
      - containerPort: 30800   # producer NodePort
        hostPort: 8000
```
🧠 **Why.** `extraPortMappings` punches host ports through the kind container to the NodePort
Services inside, so your browser at `localhost:8080`/`:8000` reaches pods in the cluster.

### Exercise 5.2 — Create cluster & load images

🧠 **Why.** kind nodes have their *own* image store, isolated from host Docker. You must build then
`kind load`, or pods fail with `ErrImagePull`.

▶️ **Do.**
```powershell
cd D:\__claude\cloud-native-learning-lab\labs\01-kafka
kind create cluster --name kafka-lab --config k8s/kind-cluster.yaml
kubectl cluster-info --context kind-kafka-lab

docker build -t producer:local ./producer
docker build -t consumer:local ./consumer

kind load docker-image producer:local --name kafka-lab
kind load docker-image consumer:local --name kafka-lab
```
👀 **Expect.** `cluster-info` prints the control plane URL; both images report "loaded".

✅ **CHECKPOINT 5.2.** Cluster exists; both images loaded into it.

### Exercise 5.3 — Create the manifests

▶️ **Do.** Create `k8s/kafka.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
spec:
  replicas: 1
  selector:
    matchLabels: { app: kafka }
  template:
    metadata:
      labels: { app: kafka }
    spec:
      containers:
        - name: kafka
          image: apache/kafka:3.8.0
          ports:
            - containerPort: 9092
          env:
            - { name: KAFKA_NODE_ID, value: "1" }
            - { name: KAFKA_PROCESS_ROLES, value: "broker,controller" }
            - { name: KAFKA_CONTROLLER_QUORUM_VOTERS, value: "1@localhost:9093" }
            - { name: KAFKA_LISTENERS, value: "PLAINTEXT://:9092,CONTROLLER://:9093" }
            - { name: KAFKA_ADVERTISED_LISTENERS, value: "PLAINTEXT://kafka:9092" }
            - { name: KAFKA_CONTROLLER_LISTENER_NAMES, value: "CONTROLLER" }
            - { name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP, value: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT" }
            - { name: KAFKA_INTER_BROKER_LISTENER_NAME, value: "PLAINTEXT" }
            - { name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR, value: "1" }
            - { name: KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR, value: "1" }
            - { name: KAFKA_TRANSACTION_STATE_LOG_MIN_ISR, value: "1" }
            - { name: KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS, value: "0" }
            - { name: KAFKA_AUTO_CREATE_TOPICS_ENABLE, value: "false" }
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
spec:
  selector: { app: kafka }
  ports:
    - port: 9092
      targetPort: 9092
```
🧠 **Why.** In k8s the advertised listener is `kafka:9092` — the **Service name**. All pods reach
the broker by that DNS name. Single-node uses `localhost:9093` for the controller quorum.

▶️ **Do.** Create `k8s/kafka-ui.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-ui
spec:
  replicas: 1
  selector:
    matchLabels: { app: kafka-ui }
  template:
    metadata:
      labels: { app: kafka-ui }
    spec:
      containers:
        - name: kafka-ui
          image: provectuslabs/kafka-ui:latest
          ports: [{ containerPort: 8080 }]
          env:
            - { name: KAFKA_CLUSTERS_0_NAME, value: "local" }
            - { name: KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS, value: "kafka:9092" }
---
apiVersion: v1
kind: Service
metadata:
  name: kafka-ui
spec:
  type: NodePort
  selector: { app: kafka-ui }
  ports:
    - port: 8080
      targetPort: 8080
      nodePort: 30080
```

▶️ **Do.** Create `k8s/producer.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: producer
spec:
  replicas: 1
  selector:
    matchLabels: { app: producer }
  template:
    metadata:
      labels: { app: producer }
    spec:
      containers:
        - name: producer
          image: producer:local
          imagePullPolicy: IfNotPresent   # use the kind-loaded image, don't pull from a registry
          ports: [{ containerPort: 8000 }]
          env:
            - { name: KAFKA_BOOTSTRAP, value: "kafka:9092" }
            - { name: KAFKA_TOPIC, value: "events" }
---
apiVersion: v1
kind: Service
metadata:
  name: producer
spec:
  type: NodePort
  selector: { app: producer }
  ports:
    - port: 8000
      targetPort: 8000
      nodePort: 30800
```
🧠 **Why.** `imagePullPolicy: IfNotPresent` is essential with `kind load` — the default `Always`
would try (and fail) to pull `producer:local` from a nonexistent registry.

▶️ **Do.** Create `k8s/consumer.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: consumer
spec:
  replicas: 1                    # <-- you'll scale THIS to watch rebalancing
  selector:
    matchLabels: { app: consumer }
  template:
    metadata:
      labels: { app: consumer }
    spec:
      containers:
        - name: consumer
          image: consumer:local
          imagePullPolicy: IfNotPresent
          env:
            - { name: KAFKA_BOOTSTRAP, value: "kafka:9092" }
            - { name: KAFKA_GROUP, value: "event-consumers" }
            - { name: KAFKA_TOPIC, value: "events" }
            - { name: KAFKA_CONCURRENCY, value: "1" }
            - { name: PROCESS_DELAY_MS, value: "200" }
```
🧠 **Why.** The consumer has **no Service** — nothing connects *to* it; it pulls from Kafka.
`replicas` is the k8s equivalent of `--scale consumer=N`.

### Exercise 5.4 — Deploy & create the topic

▶️ **Do.**
```powershell
kubectl apply -f k8s/kafka.yaml
kubectl wait --for=condition=available deploy/kafka --timeout=120s
kubectl apply -f k8s/kafka-ui.yaml -f k8s/producer.yaml -f k8s/consumer.yaml
kubectl get pods -w        # wait until all Running; Ctrl+C to stop
```
▶️ **Do.** Create the topic inside the cluster:
```powershell
$kafkaPod = kubectl get pod -l app=kafka -o jsonpath='{.items[0].metadata.name}'
kubectl exec -it $kafkaPod -- /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 --create --topic events --partitions 3 --replication-factor 1
```
▶️ **Do.** Open **http://localhost:8080** and produce:
```powershell
curl.exe -X POST "http://localhost:8000/publish-bulk?count=50"
```
👀 **Expect.** All pods `Running`; Kafka UI shows the `events` topic and messages arriving.

✅ **CHECKPOINT 5.4.** Full stack running on Kubernetes; messages flowing.

### Exercise 5.5 — EXPERIMENT E: scale pods, watch rebalancing on k8s

▶️ **Do.**
```powershell
kubectl scale deployment consumer --replicas=3
kubectl get pods -l app=consumer
kubectl logs -f -l app=consumer --prefix --max-log-requests=10
```
👀 **Expect.** `[pod=consumer-xxxx] partition=N` — each pod claims different partitions.

▶️ **Do.** Scale to 5, then add partitions:
```powershell
kubectl scale deployment consumer --replicas=5
kubectl exec -it $kafkaPod -- /opt/kafka/bin/kafka-topics.sh `
  --bootstrap-server localhost:9092 --alter --topic events --partitions 6
```
👀 **Expect.** At 5 pods / 3 partitions, 2 pods idle; after going to 6 partitions, the idle pods
activate. Kafka UI → Consumers → `event-consumers` shows members + lag live.

📝 **Record.**

| Replicas | Partitions | Pods with work | Pods idle |
|---|---|---|---|
| 3 | 3 |  |  |
| 5 | 3 |  |  |
| 5 | 6 |  |  |

✅ **CHECKPOINT E — Lab 1 complete.** You reproduced the partition/consumer rule on real Kubernetes.

---

## Lab 1 — Completion checklist

- [ ] 1.0 Prerequisites verified
- [ ] Phase 1: Kafka + UI up, topic created, seen in browser
- [ ] Phase 2: producer sends, same key → same partition
- [ ] Phase 3: consumer project created
- [ ] Exp A: partition distribution recorded
- [ ] Exp B: scaled consumers, idle ones past partition count recorded
- [ ] Exp C: added partitions live (key remap + can't-shrink) recorded
- [ ] Exp D: `concurrency` multiplied consumers per pod
- [ ] Phase 5: same behavior reproduced on Kubernetes with `kubectl scale`

## Lab 1 — Reflection questions (answer from what you recorded)
1. With 4 partitions and 6 consumers, how many consumers would be idle? Why?
2. Why did `user-3` possibly change partitions after you added partitions in Exp C?
3. What's the difference between scaling **pods** and raising **`concurrency`**? When would you pick each?
4. Why does Kafka forbid *shrinking* partitions but allow *growing* them?

## Lab 1 — 🧹 Cleanup
```powershell
docker compose down -v            # Docker Compose
kind delete cluster --name kafka-lab   # kind
```

## Lab 1 — Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Producer can't connect | Wrong bootstrap. Host app → `localhost:29092`; container/pod → `kafka:9092`. |
| `Topic 'events' not present` | Auto-create is off (on purpose). Create it with `kafka-topics.sh`. |
| Consumer logs nothing | No messages yet, or offset — we set `earliest`. Check the group in Kafka UI. |
| kind pod stuck `ErrImagePull` | You forgot `kind load docker-image`, or `imagePullPolicy` isn't `IfNotPresent`. |
| Rebalance seems slow | Normal — the short pause *is* the lesson. |
| Can't reduce partitions | Expected. Kafka forbids it. Create a new topic instead. |
| Kafka UI empty | Check `KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092` and that kafka is healthy. |

---
---

# UPCOMING LABS (previews)

> These labs aren't performable yet — their code doesn't exist. They're detailed plans so you know
> what's next and how it builds on Lab 1. When you reach one, it gets the same full
> Exercise/Checkpoint treatment as Lab 1.

## LAB 1 add-on — v1.1: KEDA lag-based autoscaling *(all OSS)*
Manual `kubectl scale` teaches the mechanics; **KEDA** (CNCF, OSS) scales consumers automatically
on **consumer lag**. You'll install KEDA into kind, add a `ScaledObject` with the Kafka scaler,
fire a large bulk publish, and watch pods scale up as lag rises and back down as it drains — the
ceiling still being `min(partitions, consumers)`. *Concepts: event-driven autoscaling, scale-to-zero,
HPA vs KEDA.*

## LAB 1 add-on — v1.2: Schema Registry + Avro & dead-letter topics *(all OSS)*
Add data contracts with **Apicurio Registry** (Apache 2.0), serialize Avro/JSON-Schema, and run a
schema-evolution experiment. Add a **dead-letter topic** via Spring Kafka's `DefaultErrorHandler`
+ `DeadLetterPublishingRecoverer`, and watch a poison message retry then land in `events.DLT`.
*Concepts: data contracts, schema evolution/compatibility, poison-message handling, retry vs DLT.*

## LAB 2 — v2.0: Spring Boot microservices ecosystem *(all OSS)*
Grow the single consumer into a small e-commerce-style system that mixes **synchronous REST** and
**asynchronous Kafka** communication:

```
client ─HTTP▶ api-gateway ─HTTP▶ order-service ─HTTP▶ inventory-service
                                      │ publishes "order.created"
                                      └────▶ Kafka ────▶ notification-service (consumes)
```

Patterns you'll learn (each an OSS sub-topic): **Spring Cloud Gateway** (routing),
**Spring Cloud Config** (git-backed central config), **service discovery** (k8s DNS or Eureka),
**OpenFeign** (declarative HTTP client), **Resilience4j** (circuit breaker/retry/timeout/bulkhead/
rate-limit), **PostgreSQL + Spring Data JPA + Flyway** (DB-per-service + migrations),
**Spring profiles**, **Testcontainers**, and **Actuator** (the hook Lab 3 plugs into).

Planned experiments: sync vs async side by side; trip a circuit breaker by killing a service;
retry+timeout under injected latency; central-config refresh with no restart; DB-per-service
isolation; load-balance a scaled stateless service. Deploy path mirrors Lab 1 (Compose → kind).

## LAB 3 — v3.0: Observability across the whole stack *(all OSS)*
Make Labs 1–2 observable using the OSS **three pillars**:
- **Metrics:** Micrometer → **Prometheus** → **Grafana** (RED method; custom counters/timers).
- **Kafka lag as a graph:** kafka-lag-exporter → Prometheus → Grafana (connects to v1 lag + v1.1 KEDA).
- **Logs:** structured JSON (logstash-logback-encoder) → **Loki** → Grafana, correlated by `traceId`.
- **Traces:** **OpenTelemetry** → **Tempo**/**Jaeger**, with context propagation across HTTP *and*
  across Kafka — one trace spanning sync + async hops.
- **Alerting:** Prometheus **Alertmanager** / Grafana alerts.

Planned experiments: find the slow hop via a trace; watch lag become a time-series graph; follow
one `traceId` through the gateway → order → Kafka → notification; trigger an alert; pivot
metric → trace → log for one incident. *Concepts: the three pillars, RED/USE, context propagation,
metric↔trace↔log correlation — closing the loop back to Lab 1.*

---

## Working order
1. Perform **Lab 1 (v1.0)** end to end — complete every checkpoint and fill every Record table.
2. Optionally add **v1.1 / v1.2** to deepen Kafka.
3. Move to **Lab 2 (v2.0)** — reuse Lab 1's Kafka + Spring Boot skills.
4. Finish with **Lab 3 (v3.0)** — instrument everything and make it observable.

Paste any error and I'll help you fix it. When a Kafka idea grows, we log it as a new **v1.x** so
the roadmap stays clean.
