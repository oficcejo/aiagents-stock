package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
)

func main() {

	common.Test(func(c *tdx.Client) {
		resp, err := c.GetHistoryMinute("20250314", "sz000001")
		logs.PanicErr(err)

		for _, v := range resp.List {
			logs.Debug(v)
		}

		logs.Debug(resp.Count)

	})
}
