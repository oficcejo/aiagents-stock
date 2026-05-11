package tdx

import (
	"context"
	"github.com/injoyai/ios"
	"github.com/injoyai/ios/module/tcp"
	"github.com/injoyai/logs"
	"math/rand"
	"net"
	"strings"
	"time"
)

func NewTCPDial(addr string) ios.DialFunc {
	if !strings.Contains(addr, ":") {
		addr += ":7709"
	}
	return tcp.NewDial(addr)
}

func NewHostDial(hosts []string) ios.DialFunc {
	if len(hosts) == 0 {
		hosts = Hosts
	}
	index := 0

	return func(ctx context.Context) (ios.ReadWriteCloser, string, error) {
		defer func() { index++ }()
		if index >= len(hosts) {
			index = 0
		}
		addr := hosts[index]
		if !strings.Contains(addr, ":") {
			addr += ":7709"
		}
		c, err := net.Dial("tcp", addr)
		return c, addr, err
	}
}

func NewRandomDial(hosts []string) ios.DialFunc {
	if len(hosts) == 0 {
		hosts = Hosts
	}
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	return func(ctx context.Context) (ios.ReadWriteCloser, string, error) {
		addr := hosts[r.Intn(len(hosts))]
		if !strings.Contains(addr, ":") {
			addr += ":7709"
		}
		c, err := net.Dial("tcp", addr)
		return c, addr, err
	}
}

func NewRangeDial(hosts []string) ios.DialFunc {
	if len(hosts) == 0 {
		hosts = Hosts
	}
	return func(ctx context.Context) (c ios.ReadWriteCloser, _ string, err error) {
		for i, addr := range hosts {
			select {
			case <-ctx.Done():
				return nil, "", ctx.Err()
			default:
			}
			if !strings.Contains(addr, ":") {
				addr += ":7709"
			}
			c, err = net.Dial("tcp", addr)
			if err == nil {
				return c, addr, nil
			}
			if i < len(hosts)-1 {
				//最后一个错误返回出去
				logs.Err(err, "等待2秒后尝试下一个服务地址...")
				<-time.After(time.Second * 2)
			}
		}
		return
	}
}
