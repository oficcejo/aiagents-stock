package extend

import (
	"context"
	"github.com/injoyai/conv"
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/protocol"
	"path/filepath"
	"time"
)

func NewPullTrade(dir string) *PullTrade {
	return &PullTrade{
		Dir: dir,
	}
}

type PullTrade struct {
	Dir       string
	StartYear int
	EndYear   int
}

func (this *PullTrade) Pull(ctx context.Context, m *tdx.Manage, code string) error {
	startYear := this.StartYear
	if startYear <= 0 {
		startYear = 2000
	}
	endYear := this.EndYear
	if endYear <= 0 {
		endYear = time.Now().Year()
	}

	for i := startYear; i <= endYear; i++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
		if err := this.PullYear(ctx, m, i, code); err != nil {
			return err
		}
	}
	return nil
}

func (this *PullTrade) PullYear(ctx context.Context, m *tdx.Manage, year int, code string) (err error) {

	tss := protocol.Trades{}
	kss1 := protocol.Klines(nil)
	kss5 := protocol.Klines(nil)
	kss15 := protocol.Klines(nil)
	kss30 := protocol.Klines(nil)
	kss60 := protocol.Klines(nil)

	m.Workday.RangeYear(year, func(t time.Time) bool {

		select {
		case <-ctx.Done():
			err = ctx.Err()
			return false
		default:
		}

		date := t.Format("20060102")

		var resp *protocol.TradeResp
		err = m.Do(func(c *tdx.Client) error {
			resp, err = c.GetHistoryTradeDay(date, code)
			return err
		})
		if err != nil {
			logs.Err(err)
			return false
		}

		tss = append(tss, resp.List...)

		//转成分时K线
		ks := resp.List.Klines()

		kss1 = append(kss1, ks...)
		kss5 = append(kss5, ks.Merge(5)...)
		kss15 = append(kss5, ks.Merge(15)...)
		kss30 = append(kss5, ks.Merge(30)...)
		kss60 = append(kss5, ks.Merge(60)...)

		return true
	})

	if err != nil {
		return
	}

	filename := filepath.Join(this.Dir, "分时成交", code+"-"+conv.String(year)+".csv")
	filename1 := filepath.Join(this.Dir, "1分钟", code+"-"+conv.String(year)+".csv")
	filename5 := filepath.Join(this.Dir, "5分钟", code+"-"+conv.String(year)+".csv")
	filename15 := filepath.Join(this.Dir, "15分钟", code+"-"+conv.String(year)+".csv")
	filename30 := filepath.Join(this.Dir, "30分钟", code+"-"+conv.String(year)+".csv")
	filename60 := filepath.Join(this.Dir, "60分钟", code+"-"+conv.String(year)+".csv")
	name := m.Codes.GetName(code)

	err = TradeToCsv(filename, tss)
	if err != nil {
		return err
	}

	err = KlinesToCsv(filename1, code, name, kss1)
	if err != nil {
		return err
	}

	err = KlinesToCsv(filename5, code, name, kss5)
	if err != nil {
		return err
	}

	err = KlinesToCsv(filename15, code, name, kss15)
	if err != nil {
		return err
	}

	err = KlinesToCsv(filename30, code, name, kss30)
	if err != nil {
		return err
	}

	err = KlinesToCsv(filename60, code, name, kss60)
	if err != nil {
		return err
	}

	return nil
}

func KlinesToCsv(filename string, code, name string, ks protocol.Klines) error {
	data := [][]any{{"日期", "时间", "代码", "名称", "开盘", "最高", "最低", "收盘", "总手", "金额"}}
	for _, v := range ks {
		data = append(data, []any{
			v.Time.Format("20060102"),
			v.Time.Format("15:04"),
			code,
			name,
			v.Open.Float64(),
			v.High.Float64(),
			v.Low.Float64(),
			v.Close.Float64(),
			v.Volume,
			v.Amount.Float64(),
		})
	}

	buf, err := toCsv(data)
	if err != nil {
		return err
	}

	return newFile(filename, buf)
}

func TradeToCsv(filename string, ts protocol.Trades) error {
	data := [][]any{{"日期", "时间", "价格", "成交量(手)", "成交额", "方向(0买,1卖)"}}
	for _, v := range ts {
		data = append(data, []any{
			v.Time.Format(time.DateOnly),
			v.Time.Format("15:04"),
			v.Price.Float64(),
			v.Volume,
			v.Amount().Float64(),
			v.Status,
		})
	}
	buf, err := toCsv(data)
	if err != nil {
		return err
	}
	return newFile(filename, buf)
}
