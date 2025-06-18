package liman_core

import (
	"testing"
)

func TestHello(t *testing.T) {
	expected := "Hello from Liman Core!"
	actual := Hello()
	if actual != expected {
		t.Errorf("Expected %q, but got %q", expected, actual)
	}
}
