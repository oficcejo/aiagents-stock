package protocol

import (
	"encoding/hex"
	"testing"
)

/*
0c00000000011a001a003e05050000000000000002000030303030303101363030303038
0c02000000011a001a003e05050000000000000002000030303030303101363030303038
*/
func TestNewSecurityQuotes(t *testing.T) {
	f, err := MQuote.Frame("sz000001", "sh600008")
	if err != nil {
		t.Error(err)
		return
	}
	t.Log(f.Bytes().HEX())
}

func Test_securityQuote_Decode(t *testing.T) {
	s := "b1cb74000c02000000003e05af00af000136020000303030303031320bb2124c56105987e6d10cf212b78fa801ae01293dc54e8bd740acb8670086ca1e0001af36ba0c4102b467b6054203a68a0184094304891992114405862685108d0100000000e8ff320b0136303030303859098005464502468defd10cc005bed2668e05be15804d8ba12cb3b13a0083c3034100badc029d014201bc990384f70443029da503b7af074403a6e501b9db044504a6e2028dd5048d050000000000005909"
	bs, err := hex.DecodeString(s)
	if err != nil {
		t.Error(err)
		return
	}
	f, err := Decode(bs)
	if err != nil {
		t.Error(err)
		return
	}
	t.Log(hex.EncodeToString(f.Data))
	//SecurityQuote.Decode(f.Data)

}

func Test_getPrice(t *testing.T) {
	t.Log(getPrice([]byte{0x7f, 0x3f, 0x40, 0x3f, 0x01})) //预期-63
	t.Log(getPrice([]byte{0x2f, 0x3f, 0x40, 0x3f, 0x01})) //预期47
}

/*
0c000000000106000600500400000000
0c020000000106000600500400000000
*/
func Test_securityList_Frame(t *testing.T) {
	f := MCode.Frame(ExchangeSH, 0)
	t.Log(f.Bytes().HEX())
}

func Test_stockCount_Frame(t *testing.T) {
	//预期0c0200000001080008004e04000075c73301
	//   0c0000000001070007004e040075c73301
	t.Log(MCount.Frame(ExchangeSH).Bytes().HEX())
}
