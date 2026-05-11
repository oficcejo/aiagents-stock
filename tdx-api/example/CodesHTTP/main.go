package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx/extend"
	"time"
)

func main() {
	go extend.ListenCodesHTTP(10033)

	<-time.After(time.Second * 3)
	c := extend.DialCodesHTTP("http://localhost:10033")
	stocks, err := c.GetStocks()
	logs.PanicErr(err)

	for _, v := range stocks {
		println(v)
	}
}
