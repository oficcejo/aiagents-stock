package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"time"
)

func main() {
	m, err := tdx.NewManage(nil)
	logs.PanicErr(err)

	codes := m.Codes.GetStocks()
	//codes = []string{
	//	"sz000001",
	//	"sz000002",
	//}

	for _, code := range codes {
		m.Do(func(c *tdx.Client) error {
			resp, err := c.GetHistoryMinute(time.Now().Format("20060102"), code)
			logs.PanicErr(err)

			resp2, err := c.GetKlineDay(code, 0, 1)
			logs.PanicErr(err)

			if len(resp2.List) == 0 {
				logs.Debug(code)
				return nil
			}

			if len(resp.List) == 0 {
				logs.Debug(code)
				return nil
			}

			if resp2.List[0].Close != resp.List[len(resp.List)-1].Price {
				logs.Debug(code)
			}

			return nil

		})
	}

}
