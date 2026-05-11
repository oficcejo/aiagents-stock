package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
)

func main() {
	common.Test(func(c *tdx.Client) {

		_, err := tdx.NewWorkdaySqlite(c) //"./workday.db"
		logs.PanicErr(err)

		_, err = tdx.NewCodesSqlite(c) //"./codes.db"
		logs.PanicErr(err)

		c.Close()
	})
}
