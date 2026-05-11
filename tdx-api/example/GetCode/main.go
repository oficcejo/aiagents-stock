package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
	"github.com/injoyai/tdx/protocol"
)

func main() {
	common.Test(func(c *tdx.Client) {
		resp, err := c.GetCode(protocol.ExchangeSH, 369)
		logs.PanicErr(err)

		for i, v := range resp.List {
			logs.Debug(i, v, v.LastPrice)
		}
		logs.Debug("总数:", resp.Count)
	})
}
