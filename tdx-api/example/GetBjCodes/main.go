package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx/extend"
)

func main() {
	ls, err := extend.GetBjCodes()
	if err != nil {
		logs.Err(err)
		return
	}
	for _, v := range ls {
		logs.Debug(v)
	}
	logs.Debug("总数量:", len(ls))
}
