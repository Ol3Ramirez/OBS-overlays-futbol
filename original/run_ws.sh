#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
exec uv run "$DIR/ws_relay.py"
