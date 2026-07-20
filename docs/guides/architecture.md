# Architecture

## Overview

```
┌──────────────────────────────────────────────────────────┐
│                     Application Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Commands  │  │ Plugins   │  │ Events    │  │ Tasks     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
├───────┴─────────────┴──────────────┴──────────────┴──────┤
│                       SoSad Core                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Router   │  │Middleware│  │    DI     │  │   Error   │  │
│  │          │  │ Pipeline │  │ Container │  │ Pipeline  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └─────────────┴──────────────┴──────────────┘       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               Hikari (Transport Layer)                 │  │
│  │  ┌──────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ GatewayBot    │  │  RESTClient                   │  │  │
│  │  └──────────────┘  └──────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Core components

### Client
The main entry point. Available as `Client` (Gateway) and `RESTClient` (REST).

### Router
Dispatches incoming interactions (slash commands, components, modals) to registered handlers.

### Middleware Pipeline
ASGI-inspired middleware chain. Each request passes through all middleware before reaching the handler.

### DI Container
FastAPI-style dependency injection. Singleton, scoped, and factory providers.

### Error Pipeline
Global error handling pipeline. Catch and handle errors in one place.

### Event Dispatcher
Typed event system. Subscribe to Hikari events or custom typed events.

### Task Scheduler
Background task runner. Decorator-based with interval support.

### Plugin System
Auto-discovery of plugins from directories and packages.

## Request lifecycle

```
1. Discord sends interaction
2. Hikari receives and emits event
3. Event dispatcher forwards to router
4. Router resolves command/component
5. Middleware pipeline executes (pre)
6. DI container resolves dependencies
7. Checks run
8. Cooldown check
9. Handler executes
10. Middleware pipeline executes (post)
11. Response sent to Discord
```

## Design principles

- **Composition over inheritance** — hikari wrapped, not subclassed
- **Type safety first** — pyright strict mode enforced
- **Minimal magic** — explicit over implicit
- **Pluggable** — middleware, storage, transport all swappable
- **Framework agnostic** — works with FastAPI, Quart, serverless
