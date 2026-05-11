package extend

import (
	"context"
	_ "github.com/go-sql-driver/mysql"
	"github.com/injoyai/base/chans"
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/protocol"
	"xorm.io/core"
	"xorm.io/xorm"
)

func NewPullKlineMysql(cfg PullKlineConfig) (*PullKlineMysql, error) {
	db, err := xorm.NewEngine("mysql", cfg.Dir)
	if err != nil {
		return nil, err
	}
	db.SetMapper(core.SameMapper{})
	_tables := []*KlineTable(nil)
	for _, v := range cfg.Tables {
		table := KlineTableMap[v]
		if err = db.Sync2(table); err != nil {
			return nil, err
		}
		_tables = append(_tables, table)
	}
	return &PullKlineMysql{
		tables: _tables,
		Config: cfg,
		DB:     db,
	}, nil
}

type PullKlineMysql struct {
	tables []*KlineTable
	Config PullKlineConfig
	DB     *xorm.Engine
}

func (this *PullKlineMysql) Name() string {
	return "拉取k线数据"
}

func (this *PullKlineMysql) Run(ctx context.Context, m *tdx.Manage) error {
	limit := chans.NewWaitLimit(this.Config.Limit)

	//1. 获取所有股票代码
	codes := this.Config.Codes
	if len(codes) == 0 {
		codes = m.Codes.GetStocks()
	}

	for _, v := range codes {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		limit.Add()
		go func(code string) {
			defer limit.Done()

			for _, table := range this.tables {
				if table == nil {
					continue
				}

				select {
				case <-ctx.Done():
					return
				default:
				}

				var err error

				//2. 获取最后一条数据
				last := new(Kline)
				if _, err = this.DB.Table(table).Where("Code=?", code).Desc("Date").Get(last); err != nil {
					logs.Err(err)
					return
				}

				//3. 从服务器获取数据
				insert := Klines{}
				err = m.Do(func(c *tdx.Client) error {
					insert, err = this.pull(code, last.Date, table.Handler(c))
					return err
				})
				if err != nil {
					logs.Err(err)
					return
				}

				//4. 插入数据库
				err = tdx.NewSessionFunc(this.DB, func(session *xorm.Session) error {
					for i, v := range insert {
						if i == 0 {
							if _, err := session.Table(table).Where("Code=? and Date >= ?", code, v.Date).Delete(); err != nil {
								return err
							}
						}
						if _, err := session.Table(table).Insert(v); err != nil {
							return err
						}
					}
					return nil
				})
				logs.PrintErr(err)

			}

		}(v)
	}
	limit.Wait()
	return nil
}

func (this *PullKlineMysql) pull(code string, lastDate int64, f func(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error)) (Klines, error) {

	if lastDate == 0 {
		lastDate = protocol.ExchangeEstablish.Unix()
	}

	resp, err := f(code, func(k *protocol.Kline) bool {
		return k.Time.Unix() <= lastDate || k.Time.Unix() <= this.Config.StartAt.Unix()
	})
	if err != nil {
		return nil, err
	}

	ks := Klines{}
	for _, v := range resp.List {
		ks = append(ks, &Kline{
			Code:   code,
			Date:   v.Time.Unix(),
			Open:   v.Open,
			High:   v.High,
			Low:    v.Low,
			Close:  v.Close,
			Volume: v.Volume,
			Amount: v.Amount,
		})
	}

	return ks, nil
}
