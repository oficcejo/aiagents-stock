package extend

import (
	"github.com/injoyai/tdx"
)

func GetBjCodes() ([]string, error) {
	cs, err := tdx.GetBjCodes()
	if err != nil {
		return nil, err
	}
	ls := []string(nil)
	for _, v := range cs {
		ls = append(ls, "bj"+v.Code)
	}
	return ls, nil
}
