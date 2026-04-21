# Architecture

## High-Level Components

1. Window monitor worker
2. Clipboard monitor worker
3. Optional file growth monitor worker
4. Curses UI loop
5. Shared mutable session state

## Data Flow

1. Workers collect events and update shared state fields.
2. Workers append `Event` objects to state log/history.
3. UI loop reads state and renders score, detector stats, and event list.
4. On exit, report is generated from accumulated state.

## Core Modules

- `main.py`
  - Runtime implementation and entrypoint.
  - Contains worker loops, curses TUI rendering, and session report output.

- `patterns.py`
  - Contains static pattern sets and constants.
  - Includes AI tool patterns, terminal/editor patterns, source extensions, and suspicion window.

- `helper.py`
  - Provides utility functions:
    - active window lookup
    - AI window classification
    - clipboard read
    - code-like text detection
    - duration formatting
    - watch path expansion

- `state.py`
  - Defines `Event` and `State` dataclasses.
  - Encapsulates score and verdict properties.

## Concurrency Model

- Uses Python threads with a shared `threading.Event` stop flag.
- Worker loops sleep using `stop.wait(...)` to support responsive shutdown.
- Shared state is mutated without explicit locks.

Given current update frequency and usage pattern, this is acceptable, but stricter synchronization may be added later if needed.
