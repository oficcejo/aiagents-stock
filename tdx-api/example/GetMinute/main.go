package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
)

func main() {
	c, err := tdx.Dial("124.71.187.122:7709", tdx.WithDebug())
	logs.PanicErr(err)

	resp, err := c.GetMinute("sz000001")
	logs.PanicErr(err)

	for _, v := range resp.List {
		logs.Debug(v)
	}

	<-c.Done()
}
