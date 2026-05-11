package protocol

import (
	"errors"
	"github.com/injoyai/conv"
	"time"
)

type historyMinute struct{}

func (this historyMinute) Frame(date, code string) (*Frame, error) {
	exchange, number, err := DecodeCode(code)
	if err != nil {
		return nil, err
	}
	dataBs := Bytes(conv.Uint32(date))
	dataBs = append(dataBs, exchange.Uint8())
	dataBs = append(dataBs, []byte(number)...)
	return &Frame{
		Control: Control01,
		Type:    TypeHistoryMinute,
		Data:    dataBs,
	}, nil
}

func (this historyMinute) Decode(bs []byte) (*MinuteResp, error) {

	if len(bs) < 6 {
		return nil, errors.New("数据长度不足")
	}

	resp := &MinuteResp{
		Count: Uint16(bs[:2]),
	}

	multiple := Price(1) * 10
	//if bs[5] > 0x40 {
	//multiple = 10
	//}

	//2-4字节是啥?
	bs = bs[6:]

	lastPrice := Price(0)
	t := time.Date(0, 0, 0, 9, 30, 0, 0, time.Local)
	for i := uint16(0); i < resp.Count; i++ {
		var price Price
		bs, price = GetPrice(bs)
		bs, _ = GetPrice(bs) //这个是什么
		lastPrice += price
		var number int
		bs, number = CutInt(bs)

		if i == 120 {
			t = t.Add(time.Minute * 90)
		}
		resp.List = append(resp.List, PriceNumber{
			Time:   t.Add(time.Minute * time.Duration(i+1)).Format("15:04"),
			Price:  lastPrice * multiple,
			Number: number,
		})
	}
	return resp, nil
}
