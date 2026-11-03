# Project Proposal: Catching Car Hackers Using Physics

**Student project — Computer Security**
**Area:** Automotive / Cyber-Physical Systems Security + Machine Learning

## The Problem

Modern cars run on an internal computer network (called a CAN bus) that connects parts like wheels, brakes, and the dashboard. This network was designed in the 1980s with **no security at all** — any message from any part is trusted. Researchers have already shown that a hacker who plugs into this network can fake messages: for example, make the car *believe* it is driving at 160 km/h when it is really going 60. The hardest version of this attack is called a **masquerade attack** — the hacker replaces real messages with fake ones that look perfectly normal in every statistical way.

Today's detection tools watch the *traffic patterns* (message rates, timings). But clever attacks copy those patterns too. So the question is: **what else can we watch?**

## The Idea

The car's sensors cannot lie independently, because they are connected by **physics**. The four wheel-speed sensors must roughly agree with each other. The speedometer must match the wheels. The engine temperature cannot jump 100 degrees in one second. If the messages on the network break these physical rules, something is wrong — even when everything else looks normal.

**In short: don't just watch the wire — watch the wheels.**

## What I Will Do

1. Use a **free public dataset** (ROAD, from Oak Ridge National Lab, USA) that contains recordings from a real car with real injected attacks — no need to hack any vehicle ourselves.
2. Build simple detectors that check whether the sensor values obey physics (do wheel speeds agree? does the speedometer track the wheels? does anything freeze while the car moves?).
3. Compare them against standard machine-learning methods (Random Forest, XGBoost, autoencoder) using a strict, fair evaluation protocol.
4. Test whether a modern "physics + AI" hybrid (a physics-informed neural network) actually helps — or whether simple physics rules are enough. Either answer is a publishable finding.

## What I Already Have (Work Done)

- Dataset downloaded and fully analyzed; attack behavior mapped.
- First results: physics checks catch **3 out of 4 attack types perfectly**, with zero attack data used for training.
- One attack type honestly resists all detectors — we understand why, and that is a finding too.
- A full research paper draft (5 pages, 4 figures, ~50 verified references) is already written.

## What I Need

- Faculty guidance on the security/ML methodology and paper positioning.
- **No lab, no car, no GPU** — everything runs on a normal laptop in minutes.

## Why It Matters

Car cybersecurity is now legally required (UN Regulation 155 / ISO SAE 21434), and every manufacturer is hunting for detection methods that work against stealthy attacks. This project produces (a) a clear map of *when* physics-based detection works and when it does not, (b) a reusable honest evaluation protocol, and (c) a submission-ready workshop paper.

**Duration:** one trimester. **Deliverable:** workshop paper submission + open-source code.
