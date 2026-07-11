# ADR 0001: Use Three K3s Server Nodes

Status: Accepted

## Decision

Use Raspberry Pis `.51`, `.52`, and `.53` as K3s server and embedded-etcd nodes.
Use `.54` and `.55` as agents.

## Rationale

Three members provide an odd etcd quorum and tolerate one server failure without
placing control-plane and database duties on every Pi.

## Consequences

Server maintenance must be performed one node at a time. Future Intel nodes join as
agents first; a later control-plane migration requires a separate reviewed procedure.
