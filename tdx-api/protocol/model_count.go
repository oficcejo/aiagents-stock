package protocol

import "errors"

type CountResp struct {
	Count uint16
}

type count struct{}

// Frame 0c0200000001080008004e04000075c73301
func (this *count) Frame(exchange Exchange) *Frame {
	return &Frame{
		Control: Control01,
		Type:    TypeCount,
		Data:    []byte{exchange.Uint8(), 0x0, 0x75, 0xc7, 0x33, 0x01}, //后面的4字节不知道啥意思
	}
}

func (this *count) Decode(bs []byte) (*CountResp, error) {
	if len(bs) < 2 {
		return nil, errors.New("数据长度不足")
	}
	return &CountResp{Count: Uint16(bs)}, nil
}
