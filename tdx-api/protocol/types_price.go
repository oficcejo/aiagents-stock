package protocol

import (
	"fmt"
)

// Price 价格，单位厘
type Price int64

func (this Price) Float64() float64 {
	return float64(this) / 1000
}

func (this Price) Int64() int64 {
	return int64(this)
}

func (this Price) String() string {
	return fmt.Sprintf("%s元", FloatUnitString(this.Float64()))
}

type PriceLevel struct {
	Buy    bool  //买卖
	Price  Price //价 想买卖的价格
	Number int   //量 想买卖的数量
}

type PriceLevels [5]PriceLevel

func (this PriceLevels) String() string {
	s := ""
	if this[0].Buy {
		for i, v := range this {
			s += fmt.Sprintf("买%d  %s  %s\n", i+1, v.Price, IntUnitString(v.Number))
		}

	} else {
		for i := 4; i >= 0; i-- {
			s += fmt.Sprintf("卖%d  %s  %s\n", i+1, this[i].Price, IntUnitString(this[i].Number))
		}
	}
	return s
}

// K k线图
type K struct {
	Last  Price //昨天收盘价
	Open  Price //今日开盘价
	High  Price //今日最高价
	Low   Price //今日最低价
	Close Price //今日收盘价
}

func (this K) String() string {
	return fmt.Sprintf("昨收:%s, 今开:%s, 最高:%s, 最低:%s, 今收:%s", this.Last, this.Open, this.High, this.Low, this.Close)
}

// DecodeK 一般是占用6字节
func DecodeK(bs []byte) ([]byte, K) {
	k := K{}

	//当日收盘价，一般2字节
	bs, k.Close = GetPrice(bs)

	//前日收盘价，一般1字节
	bs, k.Last = GetPrice(bs)
	k.Last += k.Close

	//当日开盘价，一般1字节
	bs, k.Open = GetPrice(bs)
	k.Open += k.Close

	//当日最高价，一般1字节
	bs, k.High = GetPrice(bs)
	k.High += k.Close

	//当日最低价，一般1字节
	bs, k.Low = GetPrice(bs)
	k.Low += k.Close

	//默认按股票展示
	k.Last *= 10
	k.Open *= 10
	k.Close *= 10
	k.High *= 10
	k.Low *= 10

	return bs, k
}

func GetPrice(bs []byte) ([]byte, Price) {
	for i := range bs {
		if bs[i]&0x80 == 0 {
			return bs[i+1:], getPrice(bs[:i+1])
		}
	}
	return bs, 0
}

/*
字节的第一位表示后续是否有数据（字节）
第一字节 的第二位表示正负 1负0正 有效数据为后6位
后续字节 的有效数据为后7位
最大长度未知
0x20说明有后续数据
*/
func getPrice(bs []byte) (data Price) {

	for i := range bs {
		switch i {
		case 0:
			//取后6位
			data += Price(int32(bs[0] & 0x3F))

		default:
			//取后7位
			data += Price(int32(bs[i]&0x7F) << uint8(6+(i-1)*7))

		}

		//判断是否有后续数据
		if bs[i]&0x80 == 0 {
			break
		}
	}

	//第一字节的第二位为1表示为负数
	if len(bs) > 0 && bs[0]&0x40 > 0 {
		data = -data
	}

	return
}

func CutInt(bs []byte) ([]byte, int) {
	for i := range bs {
		if bs[i]&0x80 == 0 {
			return bs[i+1:], getData(bs[:i+1])
		}
	}
	return bs, 0
}

func getData(bs []byte) (data int) {

	for i := range bs {
		switch i {
		case 0:
			//取后6位
			data += int(bs[0] & 0x3F)

		default:
			//取后7位
			data += int(bs[i]&0x7F) << uint8(6+(i-1)*7)

		}

		//判断是否有后续数据
		if bs[i]&0x80 == 0 {
			break
		}
	}

	//第一字节的第二位为1表示为负数
	if len(bs) > 0 && bs[0]&0x40 > 0 {
		data = -data
	}

	return
}
