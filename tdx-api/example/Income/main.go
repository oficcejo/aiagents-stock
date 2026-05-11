package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx/extend"
	"time"
)

func main() {
	code := "sz000001"

	pull := extend.NewPullKline(extend.PullKlineConfig{
		Codes:  []string{code},
		Tables: []string{extend.Day},
	})

	//m, err := tdx.NewManage(nil)
	//logs.PanicErr(err)

	//err = pull.Run(context.Background(), m)
	//logs.PanicErr(err)

	ks, err := pull.DayKlines(code)
	logs.PanicErr(err)

	t := time.Now().AddDate(0, -1, -9)
	logs.Debug(t.Format(time.DateOnly))
	ls := extend.DoIncomes(ks, t, 5, 10, 20)

	logs.Debug(len(ls))

	for _, v := range ls {
		logs.Info(v)
	}

}
