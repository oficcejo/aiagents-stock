package tdx

import (
	"errors"
	"github.com/injoyai/conv"
	"github.com/injoyai/ios/client"
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx/protocol"
	"github.com/robfig/cron/v3"
	"math"
	"os"
	"path/filepath"
	"time"
	"xorm.io/core"
	"xorm.io/xorm"
)

// DefaultCodes 增加单例,部分数据需要通过Codes里面的信息计算
var DefaultCodes *Codes

func DialCodes(filename string, op ...client.Option) (*Codes, error) {
	c, err := DialDefault(op...)
	if err != nil {
		return nil, err
	}
	return NewCodesSqlite(c, filename)
}

func NewCodesMysql(c *Client, dsn string) (*Codes, error) {

	//连接数据库
	db, err := xorm.NewEngine("mysql", dsn)
	if err != nil {
		return nil, err
	}
	db.SetMapper(core.SameMapper{})

	return NewCodes(c, db)
}

func NewCodesSqlite(c *Client, filenames ...string) (*Codes, error) {

	//如果没有指定文件名,则使用默认
	defaultFilename := filepath.Join(DefaultDatabaseDir, "codes.db")
	filename := conv.Default(defaultFilename, filenames...)
	filename = conv.Select(filename == "", defaultFilename, filename)

	//如果文件夹不存在就创建
	dir, _ := filepath.Split(filename)
	_ = os.MkdirAll(dir, 0777)

	//连接数据库
	db, err := xorm.NewEngine("sqlite", filename)
	if err != nil {
		return nil, err
	}
	db.SetMapper(core.SameMapper{})
	db.DB().SetMaxOpenConns(1)

	return NewCodes(c, db)
}

func NewCodes(c *Client, db *xorm.Engine) (*Codes, error) {

	if err := db.Sync2(new(CodeModel)); err != nil {
		return nil, err
	}
	if err := db.Sync2(new(UpdateModel)); err != nil {
		return nil, err
	}

	update := new(UpdateModel)
	{ //查询或者插入一条数据
		has, err := db.Where("`Key`=?", "codes").Get(update)
		if err != nil {
			return nil, err
		} else if !has {
			update.Key = "codes"
			if _, err := db.Insert(update); err != nil {
				return nil, err
			}
		}
	}

	cc := &Codes{
		Client: c,
		db:     db,
	}

	{ //设置定时器,每天早上9点更新数据
		task := cron.New(cron.WithSeconds())
		task.AddFunc("10 0 9 * * *", func() {
			for i := 0; i < 3; i++ {
				err := cc.Update()
				if err == nil {
					return
				}
				logs.Err(err)
				<-time.After(time.Minute * 5)
			}
		})
		task.Start()
	}

	{ //判断是否更新过,更新过则不更新
		now := time.Now()
		node := time.Date(now.Year(), now.Month(), now.Day(), 9, 0, 0, 0, time.Local)
		updateTime := time.Unix(update.Time, 0)
		if now.Sub(node) > 0 {
			//当前时间在9点之后,且更新时间在9点之前,需要更新
			if updateTime.Sub(node) < 0 {
				return cc, cc.Update()
			}
		} else {
			//当前时间在9点之前,且更新时间在上个节点之前
			if updateTime.Sub(node.Add(time.Hour*24)) < 0 {
				return cc, cc.Update()
			}
		}
	}

	//从缓存中加载
	return cc, cc.Update(true)
}

type Codes struct {
	*Client                         //客户端
	db        *xorm.Engine          //数据库实例
	Map       map[string]*CodeModel //股票缓存
	list      []*CodeModel          //列表方式缓存
	exchanges map[string][]string   //交易所缓存
}

// GetName 获取股票名称
func (this *Codes) GetName(code string) string {
	if v, ok := this.Map[code]; ok {
		return v.Name
	}
	return "未知"
}

// GetStocks 获取股票代码,sh6xxx sz0xx sz30xx
func (this *Codes) GetStocks(limits ...int) []string {
	limit := conv.Default(-1, limits...)
	ls := []string(nil)
	for _, m := range this.list {
		code := m.FullCode()
		if protocol.IsStock(code) {
			ls = append(ls, code)
		}
		if limit > 0 && len(ls) >= limit {
			break
		}
	}
	return ls
}

// GetETFs 获取基金代码,sz159xxx,sh510xxx,sh511xxx
func (this *Codes) GetETFs(limits ...int) []string {
	limit := conv.Default(-1, limits...)
	ls := []string(nil)
	for _, m := range this.list {
		code := m.FullCode()
		if protocol.IsETF(code) {
			ls = append(ls, code)
		}
		if limit > 0 && len(ls) >= limit {
			break
		}
	}
	return ls
}

func (this *Codes) Get(code string) *CodeModel {
	return this.Map[code]
}

func (this *Codes) AddExchange(code string) string {
	return protocol.AddPrefix(code)
}

// Update 更新数据,从服务器或者数据库
func (this *Codes) Update(byDB ...bool) error {
	codes, err := this.GetCodes(len(byDB) > 0 && byDB[0])
	if err != nil {
		return err
	}
	codeMap := make(map[string]*CodeModel)
	exchanges := make(map[string][]string)
	for _, code := range codes {
		codeMap[code.Exchange+code.Code] = code
		exchanges[code.Code] = append(exchanges[code.Code], code.Exchange)
	}
	this.Map = codeMap
	this.list = codes
	this.exchanges = exchanges
	//更新时间
	_, err = this.db.Where("`Key`=?", "codes").Update(&UpdateModel{Time: time.Now().Unix()})
	return err
}

// GetCodes 更新股票并返回结果
func (this *Codes) GetCodes(byDatabase bool) ([]*CodeModel, error) {

	if this.Client == nil {
		return nil, errors.New("client is nil")
	}

	//2. 查询数据库所有股票
	list := []*CodeModel(nil)
	if err := this.db.Find(&list); err != nil {
		return nil, err
	}

	//如果是从缓存读取,则返回结果
	if byDatabase {
		return list, nil
	}

	mCode := make(map[string]*CodeModel, len(list))
	for _, v := range list {
		mCode[v.Code] = v
	}

	//3. 从服务器获取所有股票代码
	insert := []*CodeModel(nil)
	update := []*CodeModel(nil)
	for _, exchange := range []protocol.Exchange{protocol.ExchangeSH, protocol.ExchangeSZ, protocol.ExchangeBJ} {
		resp, err := this.Client.GetCodeAll(exchange)
		if err != nil {
			return nil, err
		}
		for _, v := range resp.List {
			if _, ok := mCode[v.Code]; ok {
				if mCode[v.Code].Name != v.Name {
					mCode[v.Code].Name = v.Name
					update = append(update, &CodeModel{
						Name:      v.Name,
						Code:      v.Code,
						Exchange:  exchange.String(),
						Multiple:  v.Multiple,
						Decimal:   v.Decimal,
						LastPrice: v.LastPrice,
					})
				}
			} else {
				code := &CodeModel{
					Name:      v.Name,
					Code:      v.Code,
					Exchange:  exchange.String(),
					Multiple:  v.Multiple,
					Decimal:   v.Decimal,
					LastPrice: v.LastPrice,
				}
				insert = append(insert, code)
				list = append(list, code)
			}
		}
	}

	switch this.db.Dialect().URI().DBType {
	case "mysql":
		// 1️⃣ 清空
		if _, err := this.db.Exec("TRUNCATE TABLE codes"); err != nil {
			return nil, err
		}

		data := append(insert, update...)
		// 2️⃣ 直接批量插入
		batchSize := 3000 // 8000(2m16s) 5000(43s) 3000(11s) 1000(59s)
		for i := 0; i < len(data); i += batchSize {
			end := i + batchSize
			if end > len(data) {
				end = len(data)
			}

			slice := conv.Array(data[i:end])
			if _, err := this.db.Insert(slice); err != nil {
				return nil, err
			}
		}
	case "sqlite3":
		//4. 插入或者更新数据库
		err := NewSessionFunc(this.db, func(session *xorm.Session) error {
			for _, v := range insert {
				if _, err := session.Insert(v); err != nil {
					return err
				}
			}
			for _, v := range update {
				if _, err := session.Where("Exchange=? and Code=? ", v.Exchange, v.Code).Cols("Name,LastPrice").Update(v); err != nil {
					return err
				}
			}
			return nil
		})
		if err != nil {
			return nil, err
		}
	}

	return list, nil
}

type UpdateModel struct {
	Key  string
	Time int64 //更新时间
}

func (*UpdateModel) TableName() string {
	return "update"
}

type CodeModel struct {
	ID        int64   `json:"id"`                      //主键
	Name      string  `json:"name"`                    //名称,有时候名称会变,例STxxx
	Code      string  `json:"code" xorm:"index"`       //代码
	Exchange  string  `json:"exchange" xorm:"index"`   //交易所
	Multiple  uint16  `json:"multiple"`                //倍数
	Decimal   int8    `json:"decimal"`                 //小数位
	LastPrice float64 `json:"lastPrice"`               //昨收价格
	EditDate  int64   `json:"editDate" xorm:"updated"` //修改时间
	InDate    int64   `json:"inDate" xorm:"created"`   //创建时间
}

func (*CodeModel) TableName() string {
	return "codes"
}

func (this *CodeModel) FullCode() string {
	return this.Exchange + this.Code
}

func (this *CodeModel) Price(p protocol.Price) protocol.Price {
	return protocol.Price(float64(p) * math.Pow10(int(2-this.Decimal)))
	//return p * protocol.Price(math.Pow10(int(2-this.Decimal)))
}

func NewSessionFunc(db *xorm.Engine, fn func(session *xorm.Session) error) error {
	session := db.NewSession()
	defer session.Close()
	if err := session.Begin(); err != nil {
		session.Rollback()
		return err
	}
	if err := fn(session); err != nil {
		session.Rollback()
		return err
	}
	if err := session.Commit(); err != nil {
		session.Rollback()
		return err
	}
	return nil
}
