# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>
#
# ==============================================================================
# SYNAPSE - Go Ingestion Gateway (Zero-Port OS Anonymous Pipes)
# Copyright (C) 2026 Noxfort Systems
# ==============================================================================

BINARY_NAME=synapse-gateway
OUTPUT_DIR=../bin
TARGET=$(OUTPUT_DIR)/$(BINARY_NAME)
CMD_SRC=./cmd/gateway

.PHONY: all build test clean run lint

all: test build

build:
	@mkdir -p $(OUTPUT_DIR)
	@echo "🔨 Compiling $(BINARY_NAME) -> $(TARGET)..."
	go build -ldflags="-s -w" -o $(TARGET) $(CMD_SRC)
	@echo "✅ Build successful ($(TARGET))."

test:
	@echo "🧪 Running unit tests..."
	go test -v -race ./...

clean:
	@echo "🧹 Cleaning binaries..."
	rm -f $(TARGET)

run: build
	$(TARGET) -port 8081
