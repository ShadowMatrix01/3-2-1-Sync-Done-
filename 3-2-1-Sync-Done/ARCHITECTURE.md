3-2-1-Sync-Done uses storage tiering and utilizes core systems architecture concepts.
The following is a diagram that shows how the system works (subject to change).
```mermaid
graph LR
    A[Hot Tier: NVMe SSD] -->|Automated Sync| B(Warm Tier: Seagate 1)
    A -->|Automated Sync| C(Warm Tier: Seagate 2)
    B -->|Periodic Manual| D{Cold Tier: USB/Cloud}
    C -->|Periodic Manual| D
    A -.->|Integrity Alert| E[Discord Webhook]