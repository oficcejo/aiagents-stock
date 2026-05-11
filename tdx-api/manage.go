package tdx

import (
	"errors"
	"github.com/injoyai/ios/client"
	"github.com/robfig/cron/v3"
	"time"
)

const (
	DefaultDatabaseDir = "./data/database"
)

func NewManageMysql(cfg *ManageConfig, op ...client.Option) (*Manage, error) {
	//初始化配置
	if cfg == nil {
		cfg = &ManageConfig{}
	}
	if cfg.CodesFilename == "" {
		return nil, errors.New("未配置Codes的数据库")
	}
	if cfg.WorkdayFileName == "" {
		return nil, errors.New("未配置Workday的数据库")
	}
	if cfg.Dial == nil {
		cfg.Dial = DialDefault
	}

	//通用客户端
	commonClient, err := cfg.Dial(op...)
	if err != nil {
		return nil, err
	}
	commonClient.Wait.SetTimeout(time.Second * 5)

	//代码管理
	codes, err := NewCodesMysql(commonClient, cfg.CodesFilename)
	if err != nil {
		return nil, err
	}

	//工作日管理
	workday, err := NewWorkdayMysql(commonClient, cfg.WorkdayFileName)
	if err != nil {
		return nil, err
	}

	//连接池
	p, err := NewPool(func() (*Client, error) {
		return cfg.Dial(op...)
	}, cfg.Number)
	if err != nil {
		return nil, err
	}

	return &Manage{
		Pool:    p,
		Config:  cfg,
		Codes:   codes,
		Workday: workday,
		Cron:    cron.New(cron.WithSeconds()),
	}, nil
}

func NewManage(cfg *ManageConfig, op ...client.Option) (*Manage, error) {
	//初始化配置
	if cfg == nil {
		cfg = &ManageConfig{}
	}
	if cfg.CodesFilename == "" {
		cfg.CodesFilename = DefaultDatabaseDir + "/codes.db"
	}
	if cfg.WorkdayFileName == "" {
		cfg.WorkdayFileName = DefaultDatabaseDir + "/workday.db"
	}
	if cfg.Dial == nil {
		cfg.Dial = DialDefault
	}

	//通用客户端
	commonClient, err := cfg.Dial(op...)
	if err != nil {
		return nil, err
	}
	commonClient.Wait.SetTimeout(time.Second * 5)

	//代码管理
	codes, err := NewCodesSqlite(commonClient, cfg.CodesFilename)
	if err != nil {
		return nil, err
	}

	//工作日管理
	workday, err := NewWorkdaySqlite(commonClient, cfg.WorkdayFileName)
	if err != nil {
		return nil, err
	}

	//连接池
	p, err := NewPool(func() (*Client, error) {
		return cfg.Dial(op...)
	}, cfg.Number)
	if err != nil {
		return nil, err
	}

	return &Manage{
		Pool:    p,
		Config:  cfg,
		Codes:   codes,
		Workday: workday,
		Cron:    cron.New(cron.WithSeconds()),
	}, nil
}

type Manage struct {
	*Pool
	Config  *ManageConfig
	Codes   *Codes
	Workday *Workday
	Cron    *cron.Cron
}

// RangeStocks 遍历所有股票
func (this *Manage) RangeStocks(f func(code string)) {
	for _, v := range this.Codes.GetStocks() {
		f(v)
	}
}

// RangeETFs 遍历所有ETF
func (this *Manage) RangeETFs(f func(code string)) {
	for _, v := range this.Codes.GetETFs() {
		f(v)
	}
}

// AddWorkdayTask 添加工作日任务
func (this *Manage) AddWorkdayTask(spec string, f func(m *Manage)) {
	this.Cron.AddFunc(spec, func() {
		if this.Workday.TodayIs() {
			f(this)
		}
	})
}

type ManageConfig struct {
	Number          int                                                //客户端数量
	CodesFilename   string                                             //代码数据库位置
	WorkdayFileName string                                             //工作日数据库位置
	Dial            func(op ...client.Option) (cli *Client, err error) //默认连接方式
}
