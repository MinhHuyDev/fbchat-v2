package main

import (
	"slices"
	"testing"
)

func TestHelloPayloadDeclaresCompatibleContract(t *testing.T) {
	payload := helloPayload()

	if got := payload["protocolVersion"]; got != bridgeProtocolVersion {
		t.Fatalf("protocolVersion = %v, want %d", got, bridgeProtocolVersion)
	}
	if got := payload["bridgeVersion"]; got != bridgeVersion {
		t.Fatalf("bridgeVersion = %v, want %q", got, bridgeVersion)
	}

	capabilities, ok := payload["capabilities"].([]string)
	if !ok {
		t.Fatalf("capabilities has type %T, want []string", payload["capabilities"])
	}
	for _, required := range []string{"newClient", "connect", "connectE2EE", "isConnected", "events"} {
		if !slices.Contains(capabilities, required) {
			t.Errorf("capabilities does not contain %q", required)
		}
	}
}
