package extend

import (
	"testing"
)

func TestNewSpiderTHS(t *testing.T) {
	ls, err := GetTHSDayKline("sz000001", THS_HFQ)
	if err != nil {
		t.Error(err)
		return
	}
	for _, v := range ls {
		t.Log(v)
	}
}
