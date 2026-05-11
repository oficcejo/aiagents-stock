package protocol

import (
	"errors"
	"fmt"
	"time"

	"github.com/injoyai/base/types"
	"github.com/injoyai/conv"
)

var (
	// 中国标准时间时区 (UTC+8)
	locationCST = time.FixedZone("CST", 8*3600)
)

type TradeResp struct {
	Count uint16
	List  Trades
}

// Trade 分时成交，todo 时间没有到秒，客户端上也没有,东方客户端能显示秒
type Trade struct {
	Time   time.Time //时间, 09:30
	Price  Price     //价格
	Volume int       //成交量,手
	Status int       //0是买，1是卖，2中性/汇总 中途也可能出现2,例20241115(sz000001)的14:56
	Number int       //单数,历史数据该字段无效
}

func (this *Trade) String() string {
	return fmt.Sprintf("%s \t%-6s \t%-6s \t%-6d(手) \t%-4d(单) \t%-4s",
		this.Time, this.Price, this.Amount(), this.Volume, this.Number, this.StatusString())
}

// Amount 成交额
func (this *Trade) Amount() Price {
	return this.Price * Price(this.Volume*100)
}

func (this *Trade) StatusString() string {
	switch this.Status {
	case 0:
		return "买入"
	case 1:
		return "卖出"
	default:
		return ""
	}
}

// AvgVolume 平均每单成交量
func (this *Trade) AvgVolume() float64 {
	return float64(this.Volume) / float64(this.Number)
}

// AvgPrice 平均每单成交金额
func (this *Trade) AvgPrice() Price {
	return Price(this.AvgVolume() * float64(this.Price) * 100)
}

// IsBuy 是否是买单
func (this *Trade) IsBuy() bool {
	return this.Status == 0
}

// IsSell 是否是卖单
func (this *Trade) IsSell() bool {
	return this.Status == 1
}

type trade struct{}

func (trade) Frame(code string, start, count uint16) (*Frame, error) {
	exchange, number, err := DecodeCode(code)
	if err != nil {
		return nil, err
	}

	codeBs := []byte(number)
	codeBs = append(codeBs, Bytes(start)...)
	codeBs = append(codeBs, Bytes(count)...)
	return &Frame{
		Control: Control01,
		Type:    TypeMinuteTrade,
		Data:    append([]byte{exchange.Uint8(), 0x0}, codeBs...),
	}, nil
}

func (trade) Decode(bs []byte, c TradeCache) (*TradeResp, error) {

	_, code, err := DecodeCode(c.Code)
	if err != nil {
		return nil, err
	}

	if len(bs) < 2 {
		return nil, errors.New("数据长度不足")
	}

	resp := &TradeResp{
		Count: Uint16(bs[:2]),
	}

	bs = bs[2:]

	lastPrice := Price(0)
	for i := uint16(0); i < resp.Count; i++ {
		timeStr := GetHourMinute([2]byte(bs[:2]))
		// 数据中的时间本身就是北京时间，使用CST时区解析
		t, err := time.ParseInLocation("2006010215:04", c.Date+timeStr, locationCST)
		if err != nil {
			return nil, err
		}
		mt := &Trade{Time: t}
		var sub Price
		bs, sub = GetPrice(bs[2:])
		lastPrice += sub * 10 //把分转换成厘
		mt.Price = lastPrice / basePrice(code)
		bs, mt.Volume = CutInt(bs)
		bs, mt.Number = CutInt(bs)
		bs, mt.Status = CutInt(bs)
		bs, _ = CutInt(bs) //这个得到的是0，不知道是啥
		resp.List = append(resp.List, mt)
	}

	return resp, nil
}

type Trades []*Trade

// Klines 合并分时成交成k线
func (this Trades) Klines() Klines {
	//按天分割
	m := make(types.SortMap[int64, Trades])
	for _, v := range this {
		//获取当天零点的时间戳
		unix := time.Date(v.Time.Year(), v.Time.Month(), v.Time.Day(), 0, 0, 0, 0, v.Time.Location()).Unix()
		m[unix] = append(m[unix], v)
	}

	//按天排序
	mKline := types.SortMap[int64, Klines]{}
	for date, v := range m {
		//生成一分钟k线
		t := time.Unix(date, 0)
		mKline[date] = v.klinesForDay(t)
	}
	//按时间排序
	lss := mKline.Sort()
	ls := Klines{}
	for _, v := range lss {
		ls = append(ls, v...)
	}
	return ls
}

// Kline 合并分时成交成1个k线,注意分时成交时间保持一致
func (this Trades) Kline(t time.Time, last Price) *Kline {
	k := &Kline{
		Time:  t,
		Last:  last,
		Open:  last,
		High:  last,
		Low:   last,
		Close: last,
	}
	first := 0
	for _, v := range this {
		if v.Price <= 0 {
			continue
		}
		switch first {
		case 0:
			k.Open = v.Price
			k.High = v.Price
			k.Low = v.Price
			k.Close = v.Price
		default:
			k.High = conv.Select(k.High < v.Price, v.Price, k.High)
			k.Low = conv.Select(k.Low > v.Price, v.Price, k.Low)
		}
		k.Close = v.Price
		k.Volume += int64(v.Volume)
		k.Amount += v.Price * Price(v.Volume) * 100
		first++
	}
	return k
}

// kline1 生成一分钟k线,一天
func (this Trades) klinesForDay(date time.Time) Klines {
	_930 := 570  //9:30 的分钟
	_1130 := 690 //11:30 的分钟
	_1300 := 780 //13:00 的分钟
	_1500 := 900 //15:00 的分钟
	keys := []int(nil)
	//早上
	m := map[int]Trades{}
	for i := 1; i <= 120; i++ {
		keys = append(keys, _930+i)
		m[_930+i] = []*Trade{}
	}
	//下午
	for i := 1; i <= 120; i++ {
		keys = append(keys, _1300+i)
		m[_1300+i] = []*Trade{}
	}
	//获取开盘价,有可能前几分钟没有数据,先遍历一遍
	var open Price
	for _, v := range this {
		if v.Price > 0 {
			open = v.Price
			break
		}
	}
	//分组,按
	for _, v := range this {
		ms := minutes(v.Time)
		t := conv.Select(ms < _930, _930, ms)
		t++
		t = conv.Select(t > _1130 && t <= _1300, _1130, t)
		t = conv.Select(t > _1500, _1500, t)
		m[t] = append(m[t], v)
	}
	//合并
	ls := []*Kline(nil)
	for _, v := range keys {
		k := m[v].Kline(time.Date(date.Year(), date.Month(), date.Day(), v/60, v%60, 0, 0, date.Location()), open)
		open = k.Close
		ls = append(ls, k)
	}
	return ls
}

type TradeCache struct {
	Date string //日期
	Code string //计算倍数
}
