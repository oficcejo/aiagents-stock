package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
)

func main() {
	common.Test(func(c *tdx.Client) {

		resp, err := c.GetHistoryTradeDay("20251010", "sz000001")
		logs.PanicErr(err)

		ks := resp.List.Klines()

		for _, v := range ks {
			logs.Debug(v)
		}

	})
}
