package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/extend"
	"time"
)

func main() {

	c, err := tdx.DialDefault()
	logs.PanicErr(err)

	ks, fs, err := extend.GetTHSDayKlineFactorFull("000001", c)
	logs.PanicErr(err)

	m := map[int64]*extend.THSFactor{}
	for _, v := range fs {
		m[v.Date] = v
	}

	for _, v := range ks[0] {
		logs.Debugf("%s  不复权:%.2f  前复权:%.2f  后复权:%.2f \n",
			time.Unix(v.Date, 0).Format(time.DateOnly),
			v.Close.Float64(),
			v.Close.Float64()*m[v.Date].QFactor,
			v.Close.Float64()*m[v.Date].HFactor,
		)
	}

}
