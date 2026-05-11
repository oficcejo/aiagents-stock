package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
	"github.com/injoyai/tdx/protocol"
	"time"
)

func main() {
	common.Test(func(c *tdx.Client) {
		old := time.Now().Add(-time.Hour * 24 * 17)
		resp, err := c.GetKlineUntil(protocol.TypeKlineDay, "sz000001", func(k *protocol.Kline) bool {
			return k.Time.Sub(old) < 0
		})
		logs.PanicErr(err)
		for _, v := range resp.List {
			logs.Debug(v)
		}
		logs.Debug(resp.Count)
	})
}
