package protocol

import (
	"testing"
)

func Test_quote_Frame(t *testing.T) {
	//0c0000000001130013003e050500000000000000010000303030303031
	f, err := MQuote.Frame("sz000001")
	if err != nil {
		t.Error(err)
		return
	}
	t.Log(f.Bytes().HEX())
}
