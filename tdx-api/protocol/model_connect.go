package protocol

import (
	"errors"
)

var (
	MConnect       = connect{}
	MHeart         = heart{}
	MCount         = count{}
	MQuote         = quote{}
	MCode          = code{}
	MMinute        = minute{}
	MHistoryMinute = historyMinute{}
	MTrade         = trade{}
	MHistoryTrade  = historyTrade{}
	MKline         = kline{}
)

type ConnectResp struct {
	Info string
}

type connect struct{}

func (connect) Frame() *Frame {
	return &Frame{
		Control: Control01,
		Type:    TypeConnect,
		Data:    []byte{0x01},
	}
}

func (connect) Decode(bs []byte) (*ConnectResp, error) {
	if len(bs) < 68 {
		return nil, errors.New("数据长度不足")
	}
	//前68字节暂时还不知道是什么
	return &ConnectResp{Info: string(UTF8ToGBK(bs[68:]))}, nil
}

/*



 */

type heart struct{}

func (this *heart) Frame() *Frame {
	return &Frame{
		Control: Control01,
		Type:    TypeHeart,
	}
}
