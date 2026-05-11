package protocol

import (
	"errors"
	"fmt"
)

type CodeResp struct {
	Count uint16
	List  []*Code
}

type Code struct {
	Name      string  //股票名称
	Code      string  //股票代码
	Multiple  uint16  //倍数,基本是0x64=100
	Decimal   int8    //小数点,基本是2
	LastPrice float64 //昨收价格,单位元,对个股无效,对指数有效,对其他未知
}

func (this *Code) String() string {
	return fmt.Sprintf("%s(%s)", this.Code, this.Name)
}

type code struct{}

func (code) Frame(exchange Exchange, start uint16) *Frame {
	return &Frame{
		Control: Control01,
		Type:    TypeCode,
		Data:    []byte{exchange.Uint8(), 0x0, uint8(start), uint8(start >> 8)},
	}
}

func (code) Decode(bs []byte) (*CodeResp, error) {

	if len(bs) < 2 {
		return nil, errors.New("数据长度不足")
	}

	resp := &CodeResp{
		Count: Uint16(bs[:2]),
	}
	bs = bs[2:]

	for i := uint16(0); i < resp.Count; i++ {
		sec := &Code{
			Code:      string(bs[:6]),
			Multiple:  Uint16(bs[6:8]),
			Name:      string(UTF8ToGBK(bs[8:16])),
			Decimal:   int8(bs[20]),
			LastPrice: getVolume2(Uint32(bs[21:25])),
		}
		//logs.Debug(bs[25:29]) //26和28字节 好像是枚举(基本是44,45和34,35)
		bs = bs[29:]
		resp.List = append(resp.List, sec)
	}

	return resp, nil

}
