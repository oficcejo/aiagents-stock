package tdx

import (
	"errors"
	"fmt"
	"github.com/injoyai/base/maps"
	"github.com/injoyai/base/maps/wait"
	"github.com/injoyai/conv"
	"github.com/injoyai/ios"
	"github.com/injoyai/ios/client"
	"github.com/injoyai/ios/module/common"
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx/protocol"
	"runtime/debug"
	"sync/atomic"
	"time"
)

const (
	LevelNone  = common.LevelNone
	LevelDebug = common.LevelDebug
	LevelWrite = common.LevelWrite
	LevelRead  = common.LevelRead
	LevelInfo  = common.LevelInfo
	LevelError = common.LevelError
	LevelAll   = common.LevelAll
)

// WithDebug 是否打印通讯数据
func WithDebug(b ...bool) client.Option {
	return func(c *client.Client) {
		c.Logger.Debug(b...)
	}
}

func WithLevel(level int) client.Option {
	return func(c *client.Client) {
		c.Logger.SetLevel(level)
	}
}

// WithRedial 断线重连
func WithRedial(b ...bool) client.Option {
	return func(c *client.Client) {
		c.SetRedial(b...)
	}
}

// DialDefault 默认连接方式
func DialDefault(op ...client.Option) (cli *Client, err error) {
	op = append([]client.Option{WithRedial()}, op...)
	return DialHostsRange(Hosts, op...)
}

// Dial 与服务器建立连接
func Dial(addr string, op ...client.Option) (cli *Client, err error) {
	return DialWith(NewTCPDial(addr), op...)
}

// DialHosts 与服务器建立连接,多个服务器轮询,开启重试生效
func DialHosts(hosts []string, op ...client.Option) (cli *Client, err error) {
	return DialWith(NewHostDial(hosts), op...)
}

// DialHostsRandom 与服务器建立连接,多个服务器随机连接
func DialHostsRandom(hosts []string, op ...client.Option) (cli *Client, err error) {
	return DialWith(NewRandomDial(hosts), op...)
}

// DialHostsRange 遍历设置的服务地址进行连接,成功则结束遍历
func DialHostsRange(hosts []string, op ...client.Option) (cli *Client, err error) {
	return DialWith(NewRangeDial(hosts), op...)
}

// DialWith 与服务器建立连接
func DialWith(dial ios.DialFunc, op ...client.Option) (cli *Client, err error) {

	cli = &Client{
		Wait: wait.New(time.Second * 2),
		m:    maps.NewSafe(),
	}

	cli.Client, err = client.Dial(dial, func(c *client.Client) {
		c.Logger.Debug(true)                           //关闭日志打印
		c.Logger.SetLevel(LevelInfo)                   //设置日志级别
		c.Logger.WithHEX()                             //以HEX显示
		c.SetOption(op...)                             //自定义选项
		c.Event.OnReadFrom = protocol.ReadFrom         //分包
		c.Event.OnDealMessage = cli.handlerDealMessage //解析数据并处理
		c.Event.OnConnected = func(c *client.Client) error {
			//无数据超时时间是60秒,30秒发送一个心跳包
			c.GoTimerWriter(30*time.Second, func(w ios.MoreWriter) error {
				bs := protocol.MHeart.Frame().Bytes()
				_, err := w.Write(bs)
				return err
			})
			f := protocol.MConnect.Frame()
			if _, err = c.Write(f.Bytes()); err != nil {
				c.Close()
			}
			return nil
		}
	})
	if err != nil {
		return nil, err
	}

	go cli.Client.Run()

	return cli, err
}

type Client struct {
	*client.Client              //客户端实例
	Wait           *wait.Entity //异步回调,设置超时时间,超时则返回错误
	m              *maps.Safe   //有部分解析需要用到代码,返回数据获取不到,固请求的时候缓存下
	msgID          uint32       //消息id,使用SendFrame自动累加
}

// handlerDealMessage 处理服务器响应的数据
func (this *Client) handlerDealMessage(c *client.Client, msg ios.Acker) {

	defer func() {
		if e := recover(); e != nil {
			logs.Err(e)
			debug.PrintStack()
		}
	}()

	f, err := protocol.Decode(msg.Payload())
	if err != nil {
		logs.Err(err)
		return
	}

	//从缓存中获取数据,响应数据中不同类型有不同的处理方式,但是响应无返回该类型,固根据消息id进行缓存
	val, _ := this.m.GetAndDel(conv.String(f.MsgID))

	var resp any
	switch f.Type {

	case protocol.TypeConnect:

	case protocol.TypeHeart:

	case protocol.TypeCount:
		resp, err = protocol.MCount.Decode(f.Data)

	case protocol.TypeCode:
		resp, err = protocol.MCode.Decode(f.Data)

	case protocol.TypeQuote:
		resp = protocol.MQuote.Decode(f.Data)

	case protocol.TypeMinute:
		resp, err = protocol.MMinute.Decode(f.Data)

	case protocol.TypeHistoryMinute:
		resp, err = protocol.MHistoryMinute.Decode(f.Data)

	case protocol.TypeMinuteTrade:
		resp, err = protocol.MTrade.Decode(f.Data, val.(protocol.TradeCache))

	case protocol.TypeHistoryMinuteTrade:
		resp, err = protocol.MHistoryTrade.Decode(f.Data, val.(protocol.TradeCache))

	case protocol.TypeKline:
		resp, err = protocol.MKline.Decode(f.Data, val.(protocol.KlineCache))

	default:
		err = fmt.Errorf("通讯类型未解析:0x%X", f.Type)

	}

	if err != nil {
		logs.Err(err)
		return
	}

	this.Wait.Done(conv.String(f.MsgID), resp)

}

// SetTimeout 设置超时时间
func (this *Client) SetTimeout(t time.Duration) {
	this.Wait.SetTimeout(t)
}

// SendFrame 发送数据,并等待响应
func (this *Client) SendFrame(f *protocol.Frame, cache ...any) (any, error) {
	f.MsgID = atomic.AddUint32(&this.msgID, 1)
	if len(cache) > 0 {
		this.m.Set(conv.String(f.MsgID), cache[0])
	}
	if _, err := this.Client.Write(f.Bytes()); err != nil {
		return nil, err
	}
	return this.Wait.Wait(conv.String(f.MsgID))
}

// GetCount 获取市场内的股票数量
func (this *Client) GetCount(exchange protocol.Exchange) (*protocol.CountResp, error) {
	f := protocol.MCount.Frame(exchange)
	result, err := this.SendFrame(f)
	if err != nil {
		return nil, err
	}
	return result.(*protocol.CountResp), nil
}

// GetCode 获取市场内指定范围内的所有证券代码,一次固定返回1000只,上证股票有效范围370-1480
// 上证前370只是395/399开头的(中证500/总交易等辅助类),在后面的话是一些100开头的国债
// 600开头的股票是上证A股，属于大盘股，其中6006开头的股票是最早上市的股票， 6016开头的股票为大盘蓝筹股；900开头的股票是上证B股；
// 000开头的股票是深证A股，001、002开头的股票也都属于深证A股， 其中002开头的股票是深证A股中小企业股票；200开头的股票是深证B股；
// 300开头的股票是创业板股票；400开头的股票是三板市场股票。
func (this *Client) GetCode(exchange protocol.Exchange, start uint16) (*protocol.CodeResp, error) {
	f := protocol.MCode.Frame(exchange, start)
	result, err := this.SendFrame(f)
	if err != nil {
		return nil, err
	}
	return result.(*protocol.CodeResp), nil
}

// GetCodeAll 通过多次请求的方式获取全部证券代码
func (this *Client) GetCodeAll(exchange protocol.Exchange) (*protocol.CodeResp, error) {
	resp := &protocol.CodeResp{}

	//通达信没有北交所代码列表,通过爬虫的方式从北交所官网获取,放在这里是为了方便业务逻辑
	//不放在extend包时防止循环引用
	//todo 这是临时方案,等通达信有北交所代码列表时再改
	if exchange == protocol.ExchangeBJ {
		codes, err := GetBjCodes()
		if err != nil {
			return nil, err
		}
		resp.Count = uint16(len(codes))
		for _, v := range codes {
			resp.List = append(resp.List, &protocol.Code{
				Code:      v.Code,
				Name:      v.Name,
				LastPrice: v.Last,
			})
		}
		return resp, nil
	}

	size := uint16(1000)
	for start := uint16(0); ; start += size {
		r, err := this.GetCode(exchange, start)
		if err != nil {
			return nil, err
		}
		resp.Count += r.Count
		resp.List = append(resp.List, r.List...)
		if r.Count < size {
			break
		}
	}
	return resp, nil
}

// GetStockAll 获取所有股票代码
func (this *Client) GetStockAll() ([]string, error) {
	ls := []string(nil)
	for _, ex := range []protocol.Exchange{protocol.ExchangeSH, protocol.ExchangeSZ, protocol.ExchangeBJ} {
		resp, err := this.GetCodeAll(ex)
		if err != nil {
			return nil, err
		}
		for _, v := range resp.List {
			if protocol.IsStock(v.Code) {
				ls = append(ls, v.Code)
			}
		}
	}
	return ls, nil
}

// GetETFAll 获取所有ETF代码
func (this *Client) GetETFAll() ([]string, error) {
	ls := []string(nil)
	for _, ex := range []protocol.Exchange{protocol.ExchangeSH, protocol.ExchangeSZ} {
		resp, err := this.GetCodeAll(ex)
		if err != nil {
			return nil, err
		}
		for _, v := range resp.List {
			if protocol.IsETF(v.Code) {
				ls = append(ls, v.Code)
			}
		}
	}
	return ls, nil
}

// GetQuote 获取盘口五档报价
func (this *Client) GetQuote(codes ...string) (protocol.QuotesResp, error) {
	for i := range codes {
		//如果是股票代码,则加上前缀
		codes[i] = protocol.AddPrefix(codes[i])
		if !protocol.IsStock(codes[i]) {
			if DefaultCodes == nil {
				return nil, errors.New("DefaultCodes未初始化")
			}
			//不是股票代码的话，根据codes的信息加上前缀
			codes[i] = DefaultCodes.AddExchange(codes[i])
		}
	}

	f, err := protocol.MQuote.Frame(codes...)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f)
	if err != nil {
		return nil, err
	}
	quotes := result.(protocol.QuotesResp)

	{ //todo 临时处理下先,后续优化,感觉有问题
		//判断长度和预期是否一致
		if len(quotes) != len(codes) {
			return nil, fmt.Errorf("预期%d个，实际%d个", len(codes), len(quotes))
		}
		for i, code := range codes {
			if !protocol.IsStock(code) {
				m := DefaultCodes.Get(code)
				if m == nil {
					return nil, fmt.Errorf("未查询到代码[%s]相关信息", code)
				}
				for ii, v := range quotes[i].SellLevel {
					quotes[i].SellLevel[ii].Price = m.Price(v.Price)
				}
				for ii, v := range quotes[i].BuyLevel {
					quotes[i].BuyLevel[ii].Price = m.Price(v.Price)
				}
				quotes[i].K = protocol.K{
					Last:  m.Price(quotes[i].K.Last),
					Open:  m.Price(quotes[i].K.Open),
					High:  m.Price(quotes[i].K.High),
					Low:   m.Price(quotes[i].K.Low),
					Close: m.Price(quotes[i].K.Close),
				}
			}
		}
	}

	return quotes, nil
}

// GetMinute 获取分时数据,todo 解析好像不对,先用历史数据
func (this *Client) GetMinute(code string) (*protocol.MinuteResp, error) {
	return this.GetHistoryMinute(time.Now().Format("20060102"), code)

	f, err := protocol.MMinute.Frame(code)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f)
	if err != nil {
		return nil, err
	}
	return result.(*protocol.MinuteResp), nil
}

// GetHistoryMinute 获取历史分时数据
func (this *Client) GetHistoryMinute(date, code string) (*protocol.MinuteResp, error) {
	f, err := protocol.MHistoryMinute.Frame(date, code)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f)
	if err != nil {
		return nil, err
	}
	return result.(*protocol.MinuteResp), nil
}

func (this *Client) GetTrade(code string, start, count uint16) (*protocol.TradeResp, error) {
	return this.GetMinuteTrade(code, start, count)
}

// GetMinuteTrade 获取分时交易详情,服务器最多返回1800条,count-start<=1800
func (this *Client) GetMinuteTrade(code string, start, count uint16) (*protocol.TradeResp, error) {
	code = protocol.AddPrefix(code)
	f, err := protocol.MTrade.Frame(code, start, count)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f, protocol.TradeCache{
		Date: time.Now().Format("20060102"),
		Code: code,
	})
	if err != nil {
		return nil, err
	}
	return result.(*protocol.TradeResp), nil
}

func (this *Client) GetTradeAll(code string) (*protocol.TradeResp, error) {
	return this.GetMinuteTradeAll(code)
}

// GetMinuteTradeAll 获取分时全部交易详情,todo 只做参考 因为交易实时在进行,然后又是分页读取的,所以会出现读取间隔内产生的交易会丢失
func (this *Client) GetMinuteTradeAll(code string) (*protocol.TradeResp, error) {
	resp := &protocol.TradeResp{}
	size := uint16(1800)
	for start := uint16(0); ; start += size {
		r, err := this.GetMinuteTrade(code, start, size)
		if err != nil {
			return nil, err
		}
		resp.Count += r.Count
		resp.List = append(r.List, resp.List...)

		if r.Count < size {
			break
		}
	}
	return resp, nil
}

func (this *Client) GetHistoryTrade(date, code string, start, count uint16) (*protocol.TradeResp, error) {
	return this.GetHistoryMinuteTrade(date, code, start, count)
}

// GetHistoryMinuteTrade 获取历史分时交易
// 只能获取昨天及之前的数据,服务器最多返回2000条,count-start<=2000,如果日期输入错误,则返回0
// 历史数据只能查到20000609
func (this *Client) GetHistoryMinuteTrade(date, code string, start, count uint16) (*protocol.TradeResp, error) {
	code = protocol.AddPrefix(code)
	f, err := protocol.MHistoryTrade.Frame(date, code, start, count)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f, protocol.TradeCache{
		Date: date,
		Code: code,
	})
	if err != nil {
		return nil, err
	}
	return result.(*protocol.TradeResp), nil
}

// GetHistoryTradeFull 获取上市至今的分时成交
func (this *Client) GetHistoryTradeFull(code string, w *Workday) (protocol.Trades, error) {
	return this.GetHistoryTradeBefore(code, w, time.Now())
}

// GetHistoryTradeBefore 获取上市至今的分时成交
func (this *Client) GetHistoryTradeBefore(code string, w *Workday, before time.Time) (protocol.Trades, error) {
	ls := protocol.Trades(nil)
	resp, err := this.GetKlineMonthAll(code)
	if err != nil {
		return nil, err
	}
	if len(resp.List) == 0 {
		return nil, nil
	}
	start := time.Date(resp.List[0].Time.Year(), resp.List[0].Time.Month(), 1, 0, 0, 0, 0, resp.List[0].Time.Location())
	var res *protocol.TradeResp
	w.Range(start, before, func(t time.Time) bool {
		for i := 0; i < 3; i++ {
			res, err = this.GetHistoryTradeDay(t.Format("20060102"), code)
			if err == nil {
				break
			}
		}
		if err != nil {
			return false
		}
		ls = append(ls, res.List...)
		return true
	})
	return ls, err
}

// GetHistoryTradeDay 获取历史某天分时全部交易,通过多次请求来拼接,只能获取昨天及之前的数据
func (this *Client) GetHistoryTradeDay(date, code string) (*protocol.TradeResp, error) {
	return this.GetHistoryMinuteTradeDay(date, code)
}

// GetHistoryMinuteTradeDay 获取历史某天分时全部交易,通过多次请求来拼接,只能获取昨天及之前的数据
// 历史数据只能查到20000609
func (this *Client) GetHistoryMinuteTradeDay(date, code string) (*protocol.TradeResp, error) {
	resp := &protocol.TradeResp{}
	size := uint16(2000)
	for start := uint16(0); ; start += size {
		r, err := this.GetHistoryMinuteTrade(date, code, start, size)
		if err != nil {
			return nil, err
		}
		resp.Count += r.Count
		resp.List = append(r.List, resp.List...)
		if r.Count < size {
			break
		}
	}
	return resp, nil
}

/*



 */

// GetIndex 获取指数,接口是和k线一样的,但是解析不知道怎么区分(解析方式不一致),所以加一个方法
func (this *Client) GetIndex(Type uint8, code string, start, count uint16) (*protocol.KlineResp, error) {
	code = protocol.AddPrefix(code)
	f, err := protocol.MKline.Frame(Type, code, start, count)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f, protocol.KlineCache{Type: Type, Kind: protocol.KindIndex})
	if err != nil {
		return nil, err
	}
	return result.(*protocol.KlineResp), nil
}

// GetIndexUntil 获取指数k线数据，通过多次请求来拼接,直到满足func返回true
func (this *Client) GetIndexUntil(Type uint8, code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	resp := &protocol.KlineResp{}
	size := uint16(800)
	var last *protocol.Kline
	for start := uint16(0); ; start += size {
		r, err := this.GetIndex(Type, code, start, size)
		if err != nil {
			return nil, err
		}
		if last != nil && len(r.List) > 0 {
			last.Last = r.List[len(r.List)-1].Close
		}
		if len(r.List) > 0 {
			last = r.List[0]
		}
		for i := len(r.List) - 1; i >= 0; i-- {
			if f(r.List[i]) {
				resp.Count += r.Count - uint16(i)
				resp.List = append(r.List[i:], resp.List...)
				return resp, nil
			}
		}
		resp.Count += r.Count
		resp.List = append(r.List, resp.List...)
		if r.Count < size {
			break
		}
	}
	return resp, nil
}

// GetIndexAll 获取全部k线数据
func (this *Client) GetIndexAll(Type uint8, code string) (*protocol.KlineResp, error) {
	return this.GetIndexUntil(Type, code, func(k *protocol.Kline) bool { return false })
}

func (this *Client) GetIndexDay(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetIndex(protocol.TypeKlineDay, code, start, count)
}

func (this *Client) GetIndexDayUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetIndexUntil(protocol.TypeKlineDay, code, f)
}

func (this *Client) GetIndexDayAll(code string) (*protocol.KlineResp, error) {
	return this.GetIndexAll(protocol.TypeKlineDay, code)
}

func (this *Client) GetIndexWeekAll(code string) (*protocol.KlineResp, error) {
	return this.GetIndexAll(protocol.TypeKlineWeek, code)
}

func (this *Client) GetIndexMonthAll(code string) (*protocol.KlineResp, error) {
	return this.GetIndexAll(protocol.TypeKlineMonth, code)
}

func (this *Client) GetIndexQuarterAll(code string) (*protocol.KlineResp, error) {
	return this.GetIndexAll(protocol.TypeKlineQuarter, code)
}

func (this *Client) GetIndexYearAll(code string) (*protocol.KlineResp, error) {
	return this.GetIndexAll(protocol.TypeKlineYear, code)
}

/*


 */

// GetKline 获取k线数据,推荐收盘之后获取,否则会获取到当天的数据
func (this *Client) GetKline(Type uint8, code string, start, count uint16) (*protocol.KlineResp, error) {
	code = protocol.AddPrefix(code)
	f, err := protocol.MKline.Frame(Type, code, start, count)
	if err != nil {
		return nil, err
	}
	result, err := this.SendFrame(f, protocol.KlineCache{Type: Type, Kind: protocol.KindStock})
	if err != nil {
		return nil, err
	}
	return result.(*protocol.KlineResp), nil
}

// GetKlineUntil 获取k线数据，通过多次请求来拼接,直到满足func返回true
func (this *Client) GetKlineUntil(Type uint8, code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	resp := &protocol.KlineResp{}
	size := uint16(800)
	var last *protocol.Kline
	for start := uint16(0); ; start += size {
		r, err := this.GetKline(Type, code, start, size)
		if err != nil {
			return nil, err
		}
		if last != nil && len(r.List) > 0 {
			last.Last = r.List[len(r.List)-1].Close
		}
		if len(r.List) > 0 {
			last = r.List[0]
		}
		for i := len(r.List) - 1; i >= 0; i-- {
			if f(r.List[i]) {
				resp.Count += r.Count - uint16(i)
				resp.List = append(r.List[i:], resp.List...)
				return resp, nil
			}
		}
		resp.Count += r.Count
		resp.List = append(r.List, resp.List...)
		if r.Count < size {
			break
		}
	}
	return resp, nil
}

// GetKlineAll 获取全部k线数据
func (this *Client) GetKlineAll(Type uint8, code string) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(Type, code, func(k *protocol.Kline) bool { return false })
}

// GetKlineMinute 获取一分钟k线数据,每次最多800条,最多只能获取24000条数据
func (this *Client) GetKlineMinute(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineMinute, code, start, count)
}

// GetKlineMinuteAll 获取一分钟k线全部数据,最多只能获取24000条数据
func (this *Client) GetKlineMinuteAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineMinute, code)
}

func (this *Client) GetKlineMinuteUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineMinute, code, f)
}

// GetKline5Minute 获取五分钟k线数据
func (this *Client) GetKline5Minute(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKline5Minute, code, start, count)
}

// GetKline5MinuteAll 获取5分钟k线全部数据
func (this *Client) GetKline5MinuteAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKline5Minute, code)
}

func (this *Client) GetKline5MinuteUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKline5Minute, code, f)
}

// GetKline15Minute 获取十五分钟k线数据
func (this *Client) GetKline15Minute(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKline15Minute, code, start, count)
}

// GetKline15MinuteAll 获取十五分钟k线全部数据
func (this *Client) GetKline15MinuteAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKline15Minute, code)
}

func (this *Client) GetKline15MinuteUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKline15Minute, code, f)
}

// GetKline30Minute 获取三十分钟k线数据
func (this *Client) GetKline30Minute(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKline30Minute, code, start, count)
}

// GetKline30MinuteAll 获取三十分钟k线全部数据
func (this *Client) GetKline30MinuteAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKline30Minute, code)
}

func (this *Client) GetKline30MinuteUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKline30Minute, code, f)
}

// GetKline60Minute 获取60分钟k线数据
func (this *Client) GetKline60Minute(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKline60Minute, code, start, count)
}

// GetKlineHour 获取小时k线数据
func (this *Client) GetKlineHour(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKline60Minute, code, start, count)
}

// GetKline60MinuteAll 获取60分钟k线全部数据
func (this *Client) GetKline60MinuteAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKline60Minute, code)
}

// GetKlineHourAll 获取小时k线全部数据
func (this *Client) GetKlineHourAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKline60Minute, code)
}

func (this *Client) GetKline60MinuteUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKline60Minute, code, f)
}

func (this *Client) GetKlineHourUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKline60Minute, code, f)
}

// GetKlineDay 获取日k线数据
func (this *Client) GetKlineDay(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineDay, code, start, count)
}

// GetKlineDayAll 获取日k线全部数据
func (this *Client) GetKlineDayAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineDay, code)
}

func (this *Client) GetKlineDayUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineDay, code, f)
}

// GetKlineWeek 获取周k线数据
func (this *Client) GetKlineWeek(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineWeek, code, start, count)
}

// GetKlineWeekAll 获取周k线全部数据
func (this *Client) GetKlineWeekAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineWeek, code)
}

func (this *Client) GetKlineWeekUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineWeek, code, f)
}

// GetKlineMonth 获取月k线数据
func (this *Client) GetKlineMonth(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineMonth, code, start, count)
}

// GetKlineMonthAll 获取月k线全部数据
func (this *Client) GetKlineMonthAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineMonth, code)
}

func (this *Client) GetKlineMonthUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineMonth, code, f)
}

// GetKlineQuarter 获取季k线数据
func (this *Client) GetKlineQuarter(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineQuarter, code, start, count)
}

// GetKlineQuarterAll 获取季k线全部数据
func (this *Client) GetKlineQuarterAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineQuarter, code)
}

func (this *Client) GetKlineQuarterUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineQuarter, code, f)
}

// GetKlineYear 获取年k线数据
func (this *Client) GetKlineYear(code string, start, count uint16) (*protocol.KlineResp, error) {
	return this.GetKline(protocol.TypeKlineYear, code, start, count)
}

// GetKlineYearAll 获取年k线数据
func (this *Client) GetKlineYearAll(code string) (*protocol.KlineResp, error) {
	return this.GetKlineAll(protocol.TypeKlineYear, code)
}

func (this *Client) GetKlineYearUntil(code string, f func(k *protocol.Kline) bool) (*protocol.KlineResp, error) {
	return this.GetKlineUntil(protocol.TypeKlineYear, code, f)
}
