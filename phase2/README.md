# Digital Asset Compliance PoC

Proof of concept exploring **KYB, KYT, transaction monitoring and financial crime controls** in a permissioned digital asset environment using **Hyperledger Besu**.

The goal is to demonstrate, in a simple and reproducible way, how on-chain transactions can be monitored and correlated with compliance information to generate explainable risk alerts.

> This is an educational PoC and not a production AML system.

---

## About the Project

The project was built in two phases.

### Phase 1 — Simulated Transactions

The first version used simulated transactions to validate the compliance logic before adding blockchain infrastructure.

It included:

- KYB status associated with entities
- transaction value checks
- wallet-risk indicators
- sanctions indicators
- rapid pass-through detection
- explainable risk scoring
- CLEAR / REVIEW / ALERT / CRITICAL classifications

### Phase 2 — Hyperledger Besu

The second phase connected the same compliance logic to a real private **Hyperledger Besu** network.

Transactions are now:

- signed locally
- submitted to Besu through JSON-RPC
- recorded in real QBFT blocks
- retrieved directly from the blockchain
- evaluated by the Python monitoring engine

---

## Architecture

```text
Institution / Wallet
        |
        v
Hyperledger Besu
        |
        | JSON-RPC
        v
Python Compliance Engine
        |
        +--> KYB checks
        +--> Transaction Monitoring
        +--> Wallet Risk
        +--> Sanctions Signals
        +--> Behavioral Analysis
        |
        v
     Risk Score
        |
   +----+----+---------+
   |         |         |
 CLEAR     REVIEW     ALERT / CRITICAL
```

---

## What Was Implemented

The current PoC includes:

- private Hyperledger Besu network
- QBFT consensus
- real blockchain transactions
- real transaction hashes and block numbers
- Python JSON-RPC integration
- KYB information linked to blockchain addresses
- high-value transaction detection
- rapid pass-through detection
- simulated wallet-risk intelligence
- simulated sanctions screening
- explainable risk scoring

The current version uses native test ETH only as a development asset.

---

## Demo Results

### 1. Normal Transaction

**Banco Alpha → Custodian Gamma**

Amount:

```text
2 ETH
```

The transaction was signed locally and successfully recorded on Hyperledger Besu.

Example result:

```text
Status: 1
Block: 4304
Gas used: 21000
```

Compliance result:

```text
Risk Score: 0
CLEAR
No material risk indicators
```

### 2. Rapid Pass-Through

The following behavior was tested:

```text
Banco Alpha
    |
    | 12 ETH
    v
Fintech Delta
    |
    | 11 ETH shortly afterwards
    v
Custodian Gamma
```

The first transaction triggered the high-value rule.

The second transaction was correlated with the previous one and identified as a **rapid pass-through** pattern.

Rules triggered:

```text
High-value transaction
Rapid pass-through
```

Result:

```text
Risk Score: 60
ALERT
```

This demonstrates basic behavioral transaction monitoring rather than evaluating each transaction only in isolation.

---

## Project Structure

```text
poc-compliance-digital-assets
|
├── README.md
|
├── phase1
|   ├── poc.py
|   ├── entities.json
|   └── transactions.json
|
└── phase2
    ├── besu_monitor.py
    ├── send_transaction.py
    ├── test_rpc.py
    ├── entities.json
    ├── wallet_intelligence.json
    ├── config.json
    └── requirements-phase2.txt
```

---

## How to Run — Phase 2

### Requirements

- Docker Desktop
- WSL2 / Ubuntu
- Python 3
- Node.js
- npm
- Hyperledger Besu Developer Quickstart

### 1. Start the Besu network

From the generated Besu quickstart directory:

```bash
./run.sh
```

The JSON-RPC endpoint used by the PoC is:

```text
http://localhost:8545
```

Chain ID:

```text
1337
```

### 2. Test the connection

```bash
python3 test_rpc.py
```

### 3. Send a test transaction

```bash
python3 send_transaction.py
```

The transaction is signed locally and submitted to the Besu RPC endpoint.

### 4. Run the monitoring engine

```bash
python3 besu_monitor.py --from-block <block_number>
```

The monitor reads transactions directly from the blockchain and applies the compliance rules.

---

## What Is Real vs Simulated

### Real

- Hyperledger Besu blockchain
- QBFT blocks
- blockchain addresses
- transaction hashes
- transaction values
- timestamps
- sender and recipient addresses
- JSON-RPC blockchain queries
- behavioral correlation between transactions

### Simulated

- KYB provider
- wallet-risk provider
- sanctions screening provider
- blockchain intelligence provider

This separation is intentional. A future version can replace the simulated intelligence layer with an external KYT / blockchain analytics provider without changing the basic monitoring flow.

---

## Roadmap

### Phase 1 — Completed

Simulated transactions and rule-based compliance engine.

### Phase 2 — Completed

Real Hyperledger Besu transactions monitored through JSON-RPC.

### Phase 3

Replace native test ETH with a fictitious ERC-20 stablecoin such as **BRLx**.

### Future Improvements

- smart contract event monitoring
- additional transaction-monitoring rules
- investigator workflow
- dashboard improvements
- integration with an external blockchain intelligence / KYT provider

---

## Security Notice

All accounts, entities, private keys and transactions used in this project are exclusively for local development and demonstration.

**Never use development private keys with real funds or on public blockchain networks.**

---

## Topics

`Hyperledger Besu` `Digital Assets` `KYB` `KYT` `AML` `Transaction Monitoring` `Blockchain Analytics` `Financial Crime` `Stablecoins` `On-chain Investigations`
