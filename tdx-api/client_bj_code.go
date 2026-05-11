package tdx

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/injoyai/conv"
	"io"
	"net/http"
	"strings"
	"time"
)

const (
	// UrlBjCodes 最后跟的是时间戳(ms),但是随便什么时间戳都能请求成功
	UrlBjCodes = "https://www.bse.cn/nqhqController/nqhq_en.do?callback=jQuery3710848510589806625_%d"
)

func GetBjCodes() ([]*BjCode, error) {
	list := []*BjCode(nil)
	//这个200预防下bug,除非北京上市公司有4000个
	for page := 0; page < 200; page++ {
		ls, done, err := getBjCodes(page)
		if err != nil {
			return nil, err
		}

		list = append(list, ls...)
		if done {
			break
		}
		<-time.After(time.Millisecond * 100)
	}
	return list, nil
}

func getBjCodes(page int) (_ []*BjCode, last bool, err error) {

	url := fmt.Sprintf(UrlBjCodes, time.Now().UnixMilli())

	bodyStr := "page=" + conv.String(page) + "&type_en=%5B%22B%22%5D&sortfield=hqcjsl&sorttype=desc&xxfcbj_en=%5B2%5D&zqdm="

	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(bodyStr))
	if err != nil {
		return nil, false, err
	}
	req.Header.Set("X-Requested-With", "XMLHttpRequest")
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.39 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, false, err
	}
	defer resp.Body.Close()

	bs, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, false, err
	}

	//处理数据
	i := bytes.IndexByte(bs, '(')
	if len(bs) < 1 || len(bs) <= i {
		return nil, false, errors.New("未知错误: " + string(bs))
	}

	bs = bs[i+1 : len(bs)-1]

	ls := []*BjCodes(nil)
	err = json.Unmarshal(bs, &ls)
	if err != nil {
		return nil, false, err
	}

	if len(ls) == 0 {
		return nil, false, errors.New("未知错误: " + string(bs))
	}

	return ls[0].Data, ls[0].LastPage, nil
}

type BjCodes struct {
	Data        []*BjCode `json:"content"`
	TotalNumber int       `json:"totalElements"`
	TotalPage   int       `json:"totalPages"`
	LastPage    bool      `json:"lastPage"`
}

type BjCode struct {
	Date      string  `json:"hqjsrq"` //日期
	Code      string  `json:"hqzqdm"` //代码
	Name      string  `json:"hqzqjc"` //名称
	LastClose float64 `json:"hqzrsp"` //前一天收盘价
	Open      float64 `json:"hqjrkp"` //开盘价
	High      float64 `json:"hqzgcj"` //最高价
	Low       float64 `json:"hqzdcj"` //最低价
	Last      float64 `json:"hqzjcj"` //最新价/收盘价
	Volume    int     `json:"hqcjsl"` //成交量,股
	Amount    float64 `json:"hqcjje"` //成交额,元
}
