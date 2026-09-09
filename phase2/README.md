# Digital Asset Compliance PoC

Proof of concept exploring **KYB, KYT, transaction monitoring and financial crime controls** in a permissioned digital asset environment using **Hyperledger Besu**.

The objective of this project is to demonstrate how blockchain transactions can be monitored and correlated with compliance information to generate explainable risk alerts.

This is an educational PoC and not a production AML system.

---

## Overview

The project currently runs a private Hyperledger Besu network using QBFT consensus.

Transactions are recorded on-chain and retrieved through the Besu JSON-RPC interface.

A Python-based compliance engine then evaluates each transaction using simple KYB/KYT and transaction-monitoring rules.

Current capabilities include:

- KYB information associated with blockchain addresses
- Real transactions recorded on Hyperledger Besu
- High-value transaction detection
- Rapid pass-through detection
- Simulated wallet-risk intelligence
- Simulated sanctions screening
- Explainable risk scoring
- CLEAR / REVIEW / ALERT / CRITICAL classifications

---

## Architecture

```mermaid
flowchart TD

A[Institution / Wallet] --> B[Hyperledger Besu]
B --> C[JSON-RPC]
C --> D[Python Compliance Engine]

E[KYB Registry] --> D
F[Mock Blockchain Intelligence] --> D

D --> G[Transaction Monitoring Rules]
G --> H[Risk Score]

H --> I[CLEAR]
H --> J[REVIEW]
H --> K[ALERT]
H --> L[CRITICAL]