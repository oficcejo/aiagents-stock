package protocol

type Control uint8

func (this Control) Uint8() uint8 {
	return uint8(this)
}

const (
	Control01 Control = 0x01 //好像都是01，暂时不知道啥含义
)

type Exchange uint8

func (this Exchange) Uint8() uint8 { return uint8(this) }

func (this Exchange) String() string {
	switch this {
	case ExchangeSZ:
		return "sz"
	case ExchangeSH:
		return "sh"
	case ExchangeBJ:
		return "bj"
	default:
		return "unknown"
	}
}

func (this Exchange) Name() string {
	switch this {
	case ExchangeSH:
		return "上海"
	case ExchangeSZ:
		return "深圳"
	case ExchangeBJ:
		return "北京"
	default:
		return "未知"
	}
}

const (
	ExchangeSZ Exchange = iota //深圳交易所
	ExchangeSH                 //上海交易所
	ExchangeBJ                 //北京交易所
)

const (
	TypeKline5Minute  uint8 = 0  // 5分钟K 线
	TypeKline15Minute uint8 = 1  // 15分钟K 线
	TypeKline30Minute uint8 = 2  // 30分钟K 线
	TypeKline60Minute uint8 = 3  // 60分钟K 线
	TypeKlineHour     uint8 = 3  // 1小时K 线
	TypeKlineDay2     uint8 = 4  // 日K 线, 发现和Day的区别是这个要除以100,其他未知
	TypeKlineWeek     uint8 = 5  // 周K 线
	TypeKlineMonth    uint8 = 6  // 月K 线
	TypeKlineMinute   uint8 = 7  // 1分钟
	TypeKlineMinute2  uint8 = 8  // 1分钟K 线,未知啥区别
	TypeKlineDay      uint8 = 9  // 日K 线
	TypeKlineQuarter  uint8 = 10 // 季K 线
	TypeKlineYear     uint8 = 11 // 年K 线
)

const (
	KindIndex = "index"
	KindStock = "stock"
)
