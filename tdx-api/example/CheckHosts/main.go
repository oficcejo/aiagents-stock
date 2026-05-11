package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
)

func main() {

	for _, v := range tdx.Hosts {

		c, err := tdx.Dial(v)
		if err != nil {
			logs.Errf("[%s:7709] %v", v, err)
			continue
		}
		c.Close()
		logs.Debugf("[%s:7709] 连接成功...\n", v)

	}

}
