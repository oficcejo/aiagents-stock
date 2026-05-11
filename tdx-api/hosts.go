package tdx

import (
	"github.com/injoyai/base/types"
	"github.com/injoyai/logs"
	"net"
	"strings"
	"sync"
	"time"
)

var (

	// Hosts 所有服务器地址(2024-11-30测试通过)
	Hosts = func() []string {
		lenSH := len(SHHosts)
		lenBJ := len(BJHosts)
		lenGZ := len(GZHosts)
		lenWH := len(WHHosts)

		ls := make([]string, lenSH+lenBJ+lenGZ+lenWH)
		copy(ls[:lenSH], SHHosts)
		copy(ls[lenSH:lenSH+lenBJ], BJHosts)
		copy(ls[lenSH+lenBJ:lenSH+lenBJ+lenGZ], GZHosts)
		copy(ls[lenSH+lenBJ+lenGZ:lenSH+lenBJ+lenGZ+lenWH], WHHosts)
		return ls
	}()

	// SHHosts 上海服务器地址
	SHHosts = []string{
		"124.71.187.122",  //华为
		"122.51.120.217",  //腾讯
		"111.229.247.189", //腾讯
		"124.70.176.52",   //华为
		"123.60.186.45",   //华为
		"122.51.232.182",  //腾讯
		"118.25.98.114",   //腾讯
		"124.70.199.56",   //华为
		"121.36.225.169",  //华为
		"123.60.70.228",   //华为
		"123.60.73.44",    //华为
		"124.70.133.119",  //华为
		"124.71.187.72",   //华为
		"123.60.84.66",    //华为
	}

	// BJHosts 北京服务器地址
	BJHosts = []string{
		"121.36.54.217",  //华为
		"121.36.81.195",  //华为
		"123.249.15.60",  //华为
		"124.70.75.113",  //华为
		"120.46.186.223", //华为
		"124.70.22.210",  //华为
		"139.9.133.247",  //华为
	}

	// GZHosts 广州服务器地址,客户端上可能显示深圳
	GZHosts = []string{
		"124.71.85.110",   //华为
		"139.9.51.18",     //华为
		"139.159.239.163", //华为
		"124.71.9.153",    //华为
		"116.205.163.254", //华为
		"116.205.171.132", //华为
		"116.205.183.150", //华为
		"111.230.186.52",  //腾讯
		"110.41.4.4",      //华为
		"110.41.2.72",     //华为
		"110.41.154.219",  //华为
		"110.41.147.114",  //华为,这个客户端显示深圳线路1,IP查询是广州的
	}

	// WHHosts 武汉服务器地址
	WHHosts = []string{
		"119.97.185.59", //电信
	}
)

// FastHosts 通过tcp(ping不可用)连接速度的方式筛选排序可用的地址
func FastHosts(hosts ...string) []DialResult {
	wg := sync.WaitGroup{}
	wg.Add(len(hosts))
	mu := sync.Mutex{}
	ls := types.List[DialResult](nil)
	for _, host := range hosts {
		go func(host string) {
			defer wg.Done()
			addr := host
			if !strings.Contains(addr, ":") {
				addr += ":7709"
			}
			now := time.Now()
			c, err := net.Dial("tcp", addr)
			if err != nil {
				logs.Err(err)
				return
			}
			spend := time.Since(now)
			c.Close()
			mu.Lock()
			ls = append(ls, DialResult{
				Host:  host,
				Spend: spend,
			})
			mu.Unlock()
		}(host)
	}
	wg.Wait()
	return ls.Sort(func(a, b DialResult) bool {
		return a.Spend < b.Spend
	})
}

// DialResult 连接结果
type DialResult struct {
	Host  string
	Spend time.Duration
}
