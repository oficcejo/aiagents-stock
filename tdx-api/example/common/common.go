package common

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
)

func Test(f func(c *tdx.Client)) {

	//重连方式1,优点,同一个客户端指针
	c, err := tdx.DialWith(tdx.NewHostDial(tdx.Hosts), tdx.WithDebug())
	logs.PanicErr(err)
	f(c)
	<-c.Done()

	//重连方式2
	//for _, v := range tdx.Hosts {
	//	c, err := tdx.DialWith(v, tdx.WithDebug())
	//	if err != nil {
	//		logs.PrintErr(err)
	//		continue
	//	}
	//	f(c)
	//	<-c.Done()
	//	break
	//}
}
