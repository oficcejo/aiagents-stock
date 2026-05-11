package main

import (
	"context"
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/extend"
	"path/filepath"
	"time"
)

func main() {

	m, err := tdx.NewManage(nil)
	logs.PanicErr(err)

	err = extend.NewPullKline(extend.PullKlineConfig{
		Codes:   []string{"sz000001"},
		Tables:  []string{extend.Year},
		Dir:     filepath.Join(tdx.DefaultDatabaseDir, "kline"),
		Limit:   1,
		StartAt: time.Time{},
	}).Run(context.Background(), m)
	logs.PanicErr(err)

}
