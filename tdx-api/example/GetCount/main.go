package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/protocol"
)

func main() {
	c, err := tdx.Dial("124.71.187.122:7709")
	logs.PanicErr(err)

	resp, err := c.GetCount(protocol.ExchangeSH)
	logs.PanicErr(err)

	logs.Debug(resp.Count)

	<-c.Done()
}
