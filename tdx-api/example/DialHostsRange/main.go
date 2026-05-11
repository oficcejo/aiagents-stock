package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
)

func main() {
	_, err := tdx.DialHostsRange([]string{"1", "2", "127.0.0.1"})
	logs.PrintErr(err)
}
