package extend

//const (
//	// UrlTHSFactor https://d.10jqka.com.cn/v6/line/hs_000001/01/2016.js
//	UrlTHSFactor = "https://d.10jqka.com.cn/v6/line/hs_%s/0%d/%d.js"
//)

type THSFactor struct {
	Date    int64   `json:"date"`     //时间
	QFactor float64 `json:"q_factor"` //前复权因子
	HFactor float64 `json:"h_factor"` //后复权因子
}
