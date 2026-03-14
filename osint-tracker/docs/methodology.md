# OSINT Methodology — How This Tracker Works

## What Is OSINT?

Open Source Intelligence (OSINT) is the collection and analysis of information from publicly available sources. The word "open" means legally accessible — not hacked, not leaked, not classified. Just public.

OSINT is used by:
- Journalists (Bellingcat, Reuters, BBC Verify)
- Academic researchers (ACLED, IODA, CSIS)
- Governments and NGOs (UN, ICRC)
- Independent analysts and investigators

This project uses the same public data sources used by the above.

---

## The Four Signal Layers

### Layer 1 — Internet Connectivity (IODA)

When a country experiences a conflict event, internet connectivity often drops. This happens because:
- Physical infrastructure is damaged
- Government orders a deliberate shutdown to limit coordination
- ISPs take defensive action

IODA measures three independent signals:
1. **BGP routing** — Are the country's network routes still being advertised globally?
2. **Active probing** — Are IP addresses in the country responding to pings?
3. **Darknet telescope** — Is normal background internet traffic still visible from the country?

A correlated drop across all three is a strong signal of physical disruption.

**Real example:** On February 28, 2026, Iran's connectivity dropped to ~4% of baseline. IODA detected this within minutes. Official confirmation came hours later.

---

### Layer 2 — Conflict Events (ACLED)

ACLED collects verified conflict events from over 200 countries using:
- Local media monitoring (in local languages)
- Trained regional researchers
- Cross-referencing multiple independent sources

Each event is geocoded and tagged by type:
- Explosions/Remote violence (airstrikes, shelling, drones)
- Battles (direct engagement)
- Strategic developments (base movements, captures)
- Protests, riots

A spike in explosion events in a specific geography is a strong conflict indicator.

---

### Layer 3 — News Volume (NewsAPI)

News volume velocity is often a *leading* indicator — reporters file stories before governments make statements.

The key metric is **spike multiplier**: how does today's coverage volume compare to the 7-day baseline?

- 1x = normal
- 3x = elevated, worth monitoring  
- 5x+ = significant event developing
- 9x+ = major breaking event

**Real example:** Iran keyword volume went 9.2x on February 28, 2026 — before the US DoD issued any official statement.

---

### Layer 4 — Aircraft Signals (ADS-B Exchange)

ADS-B (Automatic Dependent Surveillance-Broadcast) is a technology all commercial aircraft are required to transmit. Military aircraft are not required to transmit — but many do, or transmit partially.

ADS-B Exchange is notable because it does **not** remove aircraft at government request (unlike FlightRadar24 or FlightAware). This means:
- US military tankers (KC-135) often remain visible, indicating air-to-air refuelling ops
- ISR aircraft (RC-135, P-8) sometimes appear, indicating intelligence collection
- Increased flight density in a bounding box indicates operational activity

**ICAO Hex ranges by country** (publicly documented):
- US military: AE0000–AFFFFF
- Israeli AF: 738000–739FFF
- UK RAF: 43C000–43DFFF

---

## The Correlation Logic

No single signal is conclusive. Each can have innocent explanations:
- Internet outage → could be a cable cut, not a conflict
- ACLED spike → could be civil unrest, not warfare
- News volume → could be a political scandal, not a military event
- Aircraft → could be a military exercise

**Correlation changes the picture.** When all four signals spike simultaneously:
- Internet down 90%
- ACLED explosions up 400%
- News volume up 9x
- ISR aircraft appearing over adjacent airspace

...the probability of coincidence approaches zero.

This is the same logic OSINT analysts at Bellingcat, ISW, and CNAS applied to reconstruct the early hours of multiple conflicts — including the February 2026 Iran strikes — using only public data.

---

## Ethical and Legal Boundaries

### What This Tool Does
- Queries public APIs with open access
- Aggregates publicly available data
- Applies statistical analysis to public signals
- Renders public data on a map

### What This Tool Does NOT Do
- Access classified networks or databases
- Scrape private communications
- Identify specific individuals
- Access any system without authorisation
- Collect data covered by GDPR/privacy law (no personal data is processed)

### Legal Basis
All data sources used have public APIs with open terms of service for research and educational use:
- **IODA**: Georgia Tech public research API — no key required
- **ACLED**: Free academic registration — research use explicitly permitted
- **NewsAPI**: Free tier for non-commercial use
- **ADS-B Exchange**: Public feed — data is broadcast openly by aircraft

---

## Limitations

1. **Lag**: ACLED data is verified, which means it can be 24–72 hours behind real-time events
2. **Coverage gaps**: ADS-B coverage depends on receiver density — the Gulf region has moderate coverage, remote areas have poor coverage
3. **False positives**: News spikes can be driven by political events unrelated to kinetic conflict
4. **IODA latency**: BGP changes propagate in minutes; active probing results have ~5-minute granularity

This tool is for **research and awareness** — not operational intelligence. Always verify findings against primary sources.

---

## Further Reading

- [Bellingcat OSINT Guide](https://www.bellingcat.com/resources/how-tos/)
- [ACLED Methodology](https://acleddata.com/acleddatanew/wp-content/uploads/dlm_uploads/2019/01/ACLED_Codebook_2019FINAL.docx.pdf)
- [IODA Paper (Georgia Tech)](https://ioda.caida.org/)
- [ADS-B Explained (FAA)](https://www.faa.gov/nextgen/programs/adsb)
- [Conflict Monitoring with Open Data — CNAS](https://www.cnas.org)
