package protocol

import (
	"encoding/hex"
	"testing"
)

func TestUTF8ToGBK(t *testing.T) {
	s := "789c6378c1cec7a5cbcbc061c5b4898987b9050ed1f90c65b74c1825bd18c1b42890fecff09c81819191f13fc3c9f3bb169f5e7dfefeb5ef57f7199a305009308208e5b32bb6bcbf7014871200176e1df3"
	//s := "b1cb74001c00000000000d005100bd00789c6378c1cecb252ace6066c5b4898987b9050ed1f90cc5b74c18a5bc18c1b43490fecff09c81819191f13fc3c9f3bb169f5e7dfefeb5ef57f7199a305009308208e5b32bb6bcbf70148712002d7f1e13"
	bs, err := hex.DecodeString(s)
	if err != nil {
		t.Error(err)
		return
	}
	t.Log(string(bs[68:]))
	bs = UTF8ToGBK(bs)
	t.Log(string(bs))
}

func Test_getVolume(t *testing.T) {
	t.Log(getVolume(1237966432))
	t.Log(getVolume2(1237966432))

}
