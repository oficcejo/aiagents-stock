package protocol

import (
	"bytes"
	"compress/zlib"
	"errors"
	"fmt"
	"github.com/injoyai/base/types"
	"github.com/injoyai/conv"
	"io"
)

const (
	// Prefix 固定帧头
	Prefix = 0x0C

	// PrefixResp 响应帧头
	PrefixResp = 0xB1CB7400
)

type Message interface {
	Bytes() types.Bytes
}

/*
Frame 数据帧
0c 02189300 01 0300 0300 0d00 01
0c 00000000 00 0200 0200 1500
0c 01000000 01 0300 0300 0d00 01
0c 01000000 01 0300 0300 0d00 01
0c 02000000 01 1a00 1a00 3e05 050000000000000002000030303030303101363030303038

0c0100000001030003000d0001
*/
type Frame struct {
	MsgID   uint32  //消息ID
	Control Control //控制码,这个还不知道怎么定义
	Type    uint16  //请求类型,如建立连接，请求分时数据等
	Data    []byte  //数据
}

/*
Bytes

0c00000000011c001c002d0500003030303030310900010000000a0000000000000000000000

Prefix: 0c
MsgID: 0208d301
Control: 01
Length: 1c00
Length: 1c00
Type: 2d05
000030303030303104000100a401a40100000000000000000000
*/
func (this *Frame) Bytes() types.Bytes {
	length := uint16(len(this.Data) + 2)
	data := make([]byte, 12+len(this.Data))
	data[0] = Prefix
	copy(data[1:], Bytes(this.MsgID))
	data[5] = this.Control.Uint8()
	copy(data[6:], Bytes(length))
	copy(data[8:], Bytes(length))
	copy(data[10:], Bytes(this.Type))
	copy(data[12:], this.Data)
	return data
}

type Response struct {
	Prefix    uint32 //未知,猜测是帧头
	Control   uint8  //响应的控制码,目前发现0c是错误,1c是成功,猜测左数右第4位代表是否成功
	MsgID     uint32 //消息ID
	Unknown   uint8  //未知,猜测是响应的控制码
	Type      uint16 //响应类型,对应请求类型,如建立连接，请求分时数据等
	ZipLength uint16 //数据长度
	Length    uint16 //未压缩长度
	Data      []byte //数据域
}

/*
Decode
帧头		|控制码  	|消息ID    	|控制码   	|数据类型   	|未解压长度  	|解压长度   	|数据域
b1cb7400 	|1c   	|00000000 	|00      	|0d00       |5100      		|bd00     	|789c6378c1cecb252ace6066c5b4898987b9050ed1f90cc5b74c18a5bc18c1b43490fecff09c81819191f13fc3c9f3bb169f5e7dfefeb5ef57f7199a305009308208e5b32bb6bcbf70148712002d7f1e13
*/
func Decode(bs []byte) (*Response, error) {
	if len(bs) < 16 {
		return nil, errors.New("数据长度不足")
	}
	resp := &Response{
		Prefix:    Uint32(bs[:4]),
		Control:   bs[4],
		MsgID:     Uint32(bs[5:9]),
		Unknown:   bs[9],
		Type:      Uint16(bs[10:12]),
		ZipLength: Uint16(bs[12:14]),
		Length:    Uint16(bs[14:16]),
		Data:      bs[16:],
	}

	if resp.Control&0x10 != 0x10 {
		//return nil, fmt.Errorf("请求失败,请检查参数")
	}

	if int(resp.ZipLength) != len(bs[16:]) {
		return nil, fmt.Errorf("压缩数据长度不匹配,预期%d,得到%d", resp.ZipLength+16, len(bs))
	}

	//进行数据解压
	if resp.ZipLength != resp.Length {
		r, err := zlib.NewReader(bytes.NewReader(resp.Data))
		if err != nil {
			return nil, err
		}
		defer r.Close()
		resp.Data, err = io.ReadAll(r)
		if err != nil {
			return nil, err
		}
	}

	if int(resp.Length) != len(resp.Data) {
		return nil, fmt.Errorf("解压数据长度不匹配,预期%d,得到%d", resp.Length, len(resp.Data))
	}

	return resp, nil
}

// ReadFrom 这里的r推荐传入*bufio.Reader
func ReadFrom(r io.Reader) (result []byte, err error) {

	prefix := make([]byte, 4)
	for {
		result = []byte(nil)

		//读取帧头
		_, err := io.ReadFull(r, prefix)
		if err != nil {
			return nil, err
		}
		if conv.Uint32(prefix) != PrefixResp {
			continue
		}
		result = append(result, prefix...)

		//读取12字节
		buf := make([]byte, 12)
		_, err = io.ReadFull(r, buf)
		if err != nil {
			return nil, err
		}
		result = append(result, buf...)

		//获取后续字节长度
		length := uint16(result[13])<<8 + uint16(result[12])
		buf = make([]byte, length)
		_, err = io.ReadFull(r, buf)
		if err != nil {
			return nil, err
		}
		result = append(result, buf...)

		return result, nil
	}

}
