# User Profile

> This file is read by Lucky and sent to Claude as context for scoring event relevance.

---

## Who I Am

- **Name:** Jayti Pattni
- **Location:** Auckland, New Zealand
- **Year of study / career stage:** Recent Graduate
- **Degree / field:** BE(Hons) in Computer Systems Engineering, University of Auckland
- **Expected graduation:** September 2026

---

## What I'm Building Toward

What I'm optimizing for over the next 6–12 months (be honest — this drives everything):

- [ ] Landing a [specific role type, e.g. entry-level firmware/embedded engineering] internship/grad role
- [ ] Building a portfolio of [specific kinds of projects]
- [ ] Networking with [specific kinds of people — engineers at hardware companies? founders? researchers?]
- [ ] Winning / placing at hackathons for resume signal
- [ ] Learning [specific skills]

**Companies/industries I'd love to work at:** [e.g. Tesla, Apple, Rocket Lab, robotics startups, defense, medical devices — be specific, this helps score sponsor/host relevance]

---

## Technical Skills & Interests

**Strong in:**
- [e.g. C/C++ for embedded, Python, FPGA, FreeRTOS, AI]

**Comfortable with:**
- [e.g. Linux, Git, basic web dev, REST APIs]

**Want to learn / would attend events about:**
- [e.g. RTOS internals, signal processing, RF design, Rust for embedded, computer vision on edge devices]

**Actively NOT interested in (low score these):**
- [e.g. pure web3/blockchain hackathons, NFT-related events, MLM-style "founder" networking, crypto trading, pure frontend/CSS-focused events]

---

## Event Preferences

**Format preferences (rank if multiple apply):**
- In-person events in Auckland: love
- Online hackathons: fine
- Hybrid: fine
- Travel within NZ: willing if travel + accommodation is covered, willing if a dream-employer is hosting (e.g. OpenStar Technologies)
- International travel: if sponsored or in Sydney, Melbourne, Brisbane

**Time commitment:**
- Weekend hackathons (24–48h): yes
- Multi-week competitions: case-by-case
- Single-evening meetups: yes
- Multi-day conferences: case-by-case

**Prize / stakes:**
- Minimum prize pool to bother applying to a hackathon: don't care about prizes
- Care about resume-name-recognition hackathons (MLH, MIT, etc.) even with no prize: yes

---

## Hard Filters (auto-low-score)

Events that match any of these should be scored 1–3 regardless of other factors:

- Past start date (already handled by code, but defense-in-depth)
- Requires getting a visa, so somewhere other than NZ and Australia
- Costs more than [$200] to attend with no scholarship option
- Topic is in my "not interested" list above
- Targets audience I'm not in (e.g. "high school students only", "PhD researchers only", "founders with funded startups")

---

## Soft Boosts (auto-high-score)

Events matching any of these should lean toward 8–10:

- Hosted/sponsored by a company on my dream-employer list
- Topic directly matches a skill I want to learn
- Past winners' projects look impressive / similar to what I'd build
- Has a track or theme aligned with embedded/firmware/hardware
- Held by a community I respect (e.g. specific clubs, professional bodies)
- Offers mentorship or recruiter access

---

## Scoring Rubric (used in the prompt)

Tell Claude how to think about the 1–10 scale:

- **9–10:** Drop everything. Dream-employer hosting, directly on my career path, deadline is soon enough I should apply tonight.
- **7–8:** Strong fit. Apply this week. Notify me immediately.
- **5–6:** Maybe worth it if I have spare bandwidth. Show in weekly digest, not push notification.
- **3–4:** Tangentially related. Log but don't notify.
- **1–2:** Auto-filter. Don't bother surfacing.

**Notification threshold:** notify on score ≥ [7]

---

## Notes for Future Me

- Things I tried that didn't work / events I regret attending: [fill in over time]
- Patterns I've noticed in scoring (where the LLM gets it wrong): [fill in over time, then update prompt]