package protocol

import (
	"encoding/hex"
	"testing"
)

func Test_stockKline_Frame(t *testing.T) {
	//预期0c02000000001c001c002d050000303030303031 0900 0100 0000 0a00 00000000000000000000
	//   0c00000000011c001c002d050000313030303030 0900 0000 0000 0a00 00000000000000000000
	f, _ := MKline.Frame(TypeKlineDay, "sz000001", 0, 10)
	t.Log(f.Bytes().HEX())
}

func Test_stockKline_Decode(t *testing.T) {
	s := "0a0078da340198b8018404bc055ee8b3e949ad2b094f79da34010af801a002cc0260dec949859ded4e7ada34016882028e04e603b8f91e4a111f394f7dda3401e401c20200f604f84d2b4ad4d0444f7eda3401721eaa0268d87bc549ee80e34e7fda34011e288601c601d08db849230ed54e80da3401727c32da013023584999a0784e81da3401147c0ad001d0fa86498d989a4e84da34015e6800d60278c28e491ca6a14e85da340154d001b801da01403e924989d6a54e"
	bs, err := hex.DecodeString(s)
	if err != nil {
		t.Error(err)
		return
	}
	resp, err := MKline.Decode(bs, KlineCache{
		Type: 9,
		Kind: "",
	})
	if err != nil {
		t.Error(err)
		return
	}
	t.Log(len(resp.List))
	for _, v := range resp.List {
		t.Log(v)
	}
}
