package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/extend"
	"github.com/injoyai/tdx/protocol"
)

// 扩展API接口

// 获取股票代码列表
func handleGetCodes(w http.ResponseWriter, r *http.Request) {
	exchange := r.URL.Query().Get("exchange")

	type CodesResponse struct {
		Total     int                 `json:"total"`
		Exchanges map[string]int      `json:"exchanges"`
		Codes     []map[string]string `json:"codes"`
	}

	resp := &CodesResponse{
		Exchanges: map[string]int{
			"sh": 0,
			"sz": 0,
			"bj": 0,
		},
		Codes: []map[string]string{},
	}

	allCodes, err := getAllCodeModels()
	if err != nil {
		errorResponse(w, "获取代码列表失败: "+err.Error())
		return
	}
	targetExchange := strings.ToLower(exchange)

	for _, model := range allCodes {
		fullCode := model.FullCode()
		if !protocol.IsStock(fullCode) {
			continue
		}
		exName := strings.ToLower(model.Exchange)
		resp.Exchanges[exName]++

		if targetExchange != "" && targetExchange != "all" && targetExchange != exName {
			continue
		}

		resp.Codes = append(resp.Codes, map[string]string{
			"code":     model.Code,
			"name":     model.Name,
			"exchange": exName,
		})
	}

	resp.Total = len(resp.Codes)

	successResponse(w, resp)
}

// 批量获取行情
func handleBatchQuote(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		errorResponse(w, "只支持POST请求")
		return
	}

	var req struct {
		Codes []string `json:"codes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		errorResponse(w, "请求参数错误: "+err.Error())
		return
	}

	if len(req.Codes) == 0 {
		errorResponse(w, "股票代码列表不能为空")
		return
	}

	// 限制最多50只
	if len(req.Codes) > 50 {
		errorResponse(w, "一次最多查询50只股票")
		return
	}

	quotes, err := client.GetQuote(req.Codes...)
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取行情失败: %v", err))
		return
	}

	successResponse(w, quotes)
}

// 获取历史K线（指定范围，日/周/月K线使用前复权）
func handleGetKlineHistory(w http.ResponseWriter, r *http.Request) {
	code := r.URL.Query().Get("code")
	klineType := r.URL.Query().Get("type")
	limitStr := r.URL.Query().Get("limit")

	if code == "" {
		errorResponse(w, "股票代码不能为空")
		return
	}

	// 解析limit，默认100，最大800
	limit := uint16(100)
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			if l > 800 {
				l = 800
			}
			limit = uint16(l)
		}
	}

	var resp *protocol.KlineResp
	var err error

	switch klineType {
	case "minute1":
		resp, err = client.GetKlineMinute(code, 0, limit)
	case "minute5":
		resp, err = client.GetKline5Minute(code, 0, limit)
	case "minute15":
		resp, err = client.GetKline15Minute(code, 0, limit)
	case "minute30":
		resp, err = client.GetKline30Minute(code, 0, limit)
	case "hour":
		resp, err = client.GetKlineHour(code, 0, limit)
	case "week":
		// 周K线使用前复权
		resp, err = getQfqKlineDay(code)
		if err == nil {
			resp = convertToWeekKline(resp)
			// 限制返回数量
			if len(resp.List) > int(limit) {
				resp.List = resp.List[len(resp.List)-int(limit):]
				resp.Count = limit
			}
		}
	case "month":
		// 月K线使用前复权
		resp, err = getQfqKlineDay(code)
		if err == nil {
			resp = convertToMonthKline(resp)
			// 限制返回数量
			if len(resp.List) > int(limit) {
				resp.List = resp.List[len(resp.List)-int(limit):]
				resp.Count = limit
			}
		}
	case "day":
		fallthrough
	default:
		// 日K线使用前复权
		resp, err = getQfqKlineDay(code)
		if err == nil && len(resp.List) > int(limit) {
			// 只返回最近limit条
			resp.List = resp.List[len(resp.List)-int(limit):]
			resp.Count = limit
		}
	}

	if err != nil {
		errorResponse(w, fmt.Sprintf("获取K线失败: %v", err))
		return
	}

	successResponse(w, resp)
}

// 获取指数数据
func handleGetIndex(w http.ResponseWriter, r *http.Request) {
	code := r.URL.Query().Get("code")
	klineType := r.URL.Query().Get("type")
	limitStr := r.URL.Query().Get("limit")

	if code == "" {
		errorResponse(w, "指数代码不能为空")
		return
	}

	// 解析limit，默认100，最大800
	limit := uint16(100)
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			if l > 800 {
				l = 800
			}
			limit = uint16(l)
		}
	}

	var resp *protocol.KlineResp
	var err error

	// 根据类型选择对应的指数接口
	switch klineType {
	case "minute1":
		resp, err = client.GetIndex(protocol.TypeKlineMinute, code, 0, limit)
	case "minute5":
		resp, err = client.GetIndex(protocol.TypeKline5Minute, code, 0, limit)
	case "minute15":
		resp, err = client.GetIndex(protocol.TypeKline15Minute, code, 0, limit)
	case "minute30":
		resp, err = client.GetIndex(protocol.TypeKline30Minute, code, 0, limit)
	case "hour":
		resp, err = client.GetIndex(protocol.TypeKline60Minute, code, 0, limit)
	case "week":
		resp, err = client.GetIndexWeekAll(code)
		if resp != nil && len(resp.List) > int(limit) {
			resp.List = resp.List[:limit]
			resp.Count = limit
		}
	case "month":
		resp, err = client.GetIndexMonthAll(code)
		if resp != nil && len(resp.List) > int(limit) {
			resp.List = resp.List[:limit]
			resp.Count = limit
		}
	case "day":
		fallthrough
	default:
		resp, err = client.GetIndexDay(code, 0, limit)
	}

	if err != nil {
		errorResponse(w, fmt.Sprintf("获取指数数据失败: %v", err))
		return
	}

	successResponse(w, resp)
}

// 获取指数全部历史K线
func handleGetIndexAll(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	if code == "" {
		errorResponse(w, "指数代码不能为空")
		return
	}

	klineType := strings.TrimSpace(r.URL.Query().Get("type"))
	if klineType == "" {
		klineType = "day"
	}

	limit := parsePositiveInt(r.URL.Query().Get("limit"))
	list, err := fetchIndexAll(code, klineType)
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取指数历史数据失败: %v", err))
		return
	}

	if limit > 0 && len(list) > limit {
		list = list[len(list)-limit:]
	}

	successResponse(w, map[string]interface{}{
		"count": len(list),
		"list":  list,
	})
}

// 获取市场统计
func handleGetMarketStats(w http.ResponseWriter, r *http.Request) {
	type MarketStats struct {
		SH struct {
			Total int `json:"total"`
			Up    int `json:"up"`
			Down  int `json:"down"`
			Flat  int `json:"flat"`
		} `json:"sh"`
		SZ struct {
			Total int `json:"total"`
			Up    int `json:"up"`
			Down  int `json:"down"`
			Flat  int `json:"flat"`
		} `json:"sz"`
		BJ struct {
			Total int `json:"total"`
			Up    int `json:"up"`
			Down  int `json:"down"`
			Flat  int `json:"flat"`
		} `json:"bj"`
		UpdateTime string `json:"update_time"`
	}

	stats := &MarketStats{}
	allCodes, err := getAllCodeModels()
	if err != nil {
		errorResponse(w, "获取市场统计失败: "+err.Error())
		return
	}

	for _, model := range allCodes {
		fullCode := model.FullCode()
		if !protocol.IsStock(fullCode) {
			continue
		}
		lastPrice := model.LastPrice
		switch strings.ToLower(model.Exchange) {
		case "sh":
			stats.SH.Total++
			classifyPrice(lastPrice, &stats.SH.Up, &stats.SH.Down, &stats.SH.Flat)
		case "sz":
			stats.SZ.Total++
			classifyPrice(lastPrice, &stats.SZ.Up, &stats.SZ.Down, &stats.SZ.Flat)
		case "bj":
			stats.BJ.Total++
			classifyPrice(lastPrice, &stats.BJ.Up, &stats.BJ.Down, &stats.BJ.Flat)
		}
	}

	successResponse(w, stats)
}

// 获取各交易所证券数量
func handleGetMarketCount(w http.ResponseWriter, r *http.Request) {
	type ExchangeCount struct {
		Exchange string `json:"exchange"`
		Count    uint16 `json:"count"`
	}

	type Response struct {
		Total     uint32          `json:"total"`
		Exchanges []ExchangeCount `json:"exchanges"`
	}

	exchanges := []protocol.Exchange{protocol.ExchangeSH, protocol.ExchangeSZ, protocol.ExchangeBJ}
	names := map[protocol.Exchange]string{
		protocol.ExchangeSH: "sh",
		protocol.ExchangeSZ: "sz",
		protocol.ExchangeBJ: "bj",
	}

	resp := Response{
		Exchanges: make([]ExchangeCount, 0, len(exchanges)),
	}

	for _, ex := range exchanges {
		countResp, err := client.GetCount(ex)
		if err != nil {
			errorResponse(w, fmt.Sprintf("获取 %s 数量失败: %v", names[ex], err))
			return
		}
		resp.Exchanges = append(resp.Exchanges, ExchangeCount{
			Exchange: names[ex],
			Count:    countResp.Count,
		})
		resp.Total += uint32(countResp.Count)
	}

	successResponse(w, resp)
}

// 获取全部股票代码列表
func handleGetStockCodes(w http.ResponseWriter, r *http.Request) {
	if tdx.DefaultCodes == nil {
		errorResponse(w, "股票代码缓存未初始化")
		return
	}

	limit := parsePositiveInt(r.URL.Query().Get("limit"))
	prefixParam := strings.TrimSpace(r.URL.Query().Get("prefix"))
	includePrefix := true
	if prefixParam != "" {
		includePrefix = strings.ToLower(prefixParam) != "false"
	}

	codes := tdx.DefaultCodes.GetStocks()
	if limit > 0 && len(codes) > limit {
		codes = codes[:limit]
	}

	if !includePrefix {
		for i, code := range codes {
			if len(code) > 2 {
				codes[i] = code[2:]
			}
		}
	}

	successResponse(w, map[string]interface{}{
		"count": len(codes),
		"list":  codes,
	})
}

// 获取全部ETF代码列表
func handleGetETFCodes(w http.ResponseWriter, r *http.Request) {
	if tdx.DefaultCodes == nil {
		errorResponse(w, "代码缓存未初始化")
		return
	}

	limit := parsePositiveInt(r.URL.Query().Get("limit"))
	prefixParam := strings.TrimSpace(r.URL.Query().Get("prefix"))
	includePrefix := true
	if prefixParam != "" {
		includePrefix = strings.ToLower(prefixParam) != "false"
	}

	codes := tdx.DefaultCodes.GetETFs()
	if limit > 0 && len(codes) > limit {
		codes = codes[:limit]
	}

	if !includePrefix {
		for i, code := range codes {
			if len(code) > 2 {
				codes[i] = code[2:]
			}
		}
	}

	successResponse(w, map[string]interface{}{
		"count": len(codes),
		"list":  codes,
	})
}

// 获取ETF列表
func handleGetETFList(w http.ResponseWriter, r *http.Request) {
	exchangeFilter := strings.ToLower(strings.TrimSpace(r.URL.Query().Get("exchange")))
	limitStr := strings.TrimSpace(r.URL.Query().Get("limit"))
	limit := 0
	if limitStr != "" {
		if v, err := strconv.Atoi(limitStr); err == nil && v > 0 {
			limit = v
		}
	}

	models, err := getAllCodeModels()
	if err != nil {
		errorResponse(w, "获取ETF列表失败: "+err.Error())
		return
	}

	type ETF struct {
		Code      string  `json:"code"`
		Name      string  `json:"name"`
		Exchange  string  `json:"exchange"`
		LastPrice float64 `json:"last_price"`
	}

	result := struct {
		Total int   `json:"total"`
		List  []ETF `json:"list"`
	}{List: []ETF{}}

	for _, model := range models {
		fullCode := model.FullCode()
		if !protocol.IsETF(fullCode) {
			continue
		}
		ex := strings.ToLower(model.Exchange)
		if exchangeFilter != "" && exchangeFilter != "all" && exchangeFilter != ex {
			continue
		}
		result.List = append(result.List, ETF{
			Code:      model.Code,
			Name:      model.Name,
			Exchange:  ex,
			LastPrice: model.LastPrice,
		})
		if limit > 0 && len(result.List) >= limit {
			break
		}
	}
	result.Total = len(result.List)
	successResponse(w, result)
}

// 获取历史分时成交（分页）
func handleGetTradeHistory(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	date := strings.TrimSpace(r.URL.Query().Get("date"))
	startStr := strings.TrimSpace(r.URL.Query().Get("start"))
	countStr := strings.TrimSpace(r.URL.Query().Get("count"))

	if code == "" || date == "" {
		errorResponse(w, "code 与 date 均为必填参数")
		return
	}

	start := 0
	if startStr != "" {
		if v, err := strconv.Atoi(startStr); err == nil && v >= 0 {
			start = v
		} else {
			errorResponse(w, "start 参数无效")
			return
		}
	}

	count := 2000
	if countStr != "" {
		if v, err := strconv.Atoi(countStr); err == nil && v > 0 {
			if v > 2000 {
				v = 2000
			}
			count = v
		} else {
			errorResponse(w, "count 参数无效")
			return
		}
	}

	resp, err := client.GetHistoryMinuteTrade(date, code, uint16(start), uint16(count))
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取历史分时成交失败: %v", err))
		return
	}

	successResponse(w, resp)
}

// 获取全天分时成交
func handleGetMinuteTradeAll(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	date := strings.TrimSpace(r.URL.Query().Get("date"))

	if code == "" {
		errorResponse(w, "code 为必填参数")
		return
	}

	var (
		resp *protocol.TradeResp
		err  error
	)

	if date != "" {
		resp, err = client.GetHistoryMinuteTradeDay(date, code)
	} else {
		resp, err = client.GetMinuteTradeAll(code)
	}
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取分时成交失败: %v", err))
		return
	}

	successResponse(w, resp)
}

// 获取上市以来的全部历史分时成交
func handleGetTradeHistoryFull(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	startParam := strings.TrimSpace(r.URL.Query().Get("start_date"))
	endParam := strings.TrimSpace(r.URL.Query().Get("end_date"))
	beforeParam := strings.TrimSpace(r.URL.Query().Get("before"))
	includeToday := parseBool(strings.TrimSpace(r.URL.Query().Get("include_today")))

	if code == "" {
		errorResponse(w, "code 为必填参数")
		return
	}
	if manager == nil || manager.Workday == nil {
		errorResponse(w, "交易日模块未初始化")
		return
	}

	limit := parsePositiveInt(r.URL.Query().Get("limit"))

	var start time.Time
	var end time.Time
	var err error

	if startParam != "" {
		start, err = parseWorkdayDate(startParam)
		if err != nil {
			errorResponse(w, "start_date 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
			return
		}
	} else {
		start = time.Now().AddDate(0, 0, -30)
	}

	if beforeParam != "" {
		end, err = parseWorkdayDate(beforeParam)
		if err != nil {
			errorResponse(w, "before 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
			return
		}
	} else if endParam != "" {
		end, err = parseWorkdayDate(endParam)
		if err != nil {
			errorResponse(w, "end_date 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
			return
		}
	} else {
		end = time.Now()
	}

	if start.After(end) {
		start, end = end, start
	}

	historyEnd := end
	yesterday := time.Now().AddDate(0, 0, -1)
	if historyEnd.After(yesterday) {
		historyEnd = yesterday
	}

	type tradeItem struct {
		Time   string  `json:"time"`
		Price  float64 `json:"price"`
		Volume int     `json:"volume"`
		Status int     `json:"status"`
		Number int     `json:"number"`
	}

	items := []tradeItem{}
	truncated := false
	daysCovered := []string{}
	var lastErr error

	if !start.After(historyEnd) {
		manager.Workday.Range(
			time.Date(start.Year(), start.Month(), start.Day(), 15, 0, 0, 0, time.Local),
			time.Date(historyEnd.Year(), historyEnd.Month(), historyEnd.Day(), 15, 0, 0, 0, time.Local).Add(24*time.Hour),
			func(t time.Time) bool {
				dateStr := t.Format("20060102")
				resp, err := client.GetHistoryMinuteTradeDay(dateStr, code)
				if err != nil {
					lastErr = err
					return true
				}
				if resp == nil || len(resp.List) == 0 {
					return true
				}
				daysCovered = append(daysCovered, dateStr)
				for _, v := range resp.List {
					items = append(items, tradeItem{
						Time:   v.Time.Format(time.RFC3339),
						Price:  v.Price.Float64(),
						Volume: v.Volume,
						Status: v.Status,
						Number: v.Number,
					})
					if limit > 0 && len(items) >= limit {
						truncated = true
						return false
					}
				}
				return true
			},
		)
	}

	if includeToday && !truncated {
		now := time.Now()
		resp, err := client.GetMinuteTradeAll(code)
		if err == nil && resp != nil && len(resp.List) > 0 {
			dateStr := now.Format("20060102")
			daysCovered = append(daysCovered, dateStr)
			for _, v := range resp.List {
				items = append(items, tradeItem{
					Time:   v.Time.Format(time.RFC3339),
					Price:  v.Price.Float64(),
					Volume: v.Volume,
					Status: v.Status,
					Number: v.Number,
				})
				if limit > 0 && len(items) >= limit {
					truncated = true
					break
				}
			}
		} else if err != nil {
			lastErr = err
		}
	}

	if lastErr != nil && len(items) == 0 {
		errorResponse(w, fmt.Sprintf("获取分时成交失败: %v", lastErr))
		return
	}

	successResponse(w, map[string]interface{}{
		"code":          code,
		"start_date":    start.Format("2006-01-02"),
		"end_date":      end.Format("2006-01-02"),
		"limit":         limit,
		"count":         len(items),
		"truncated":     truncated,
		"covered_dates": daysCovered,
		"list":          items,
	})
}

// 获取股票全部历史K线（通达信）
func handleGetKlineAllTDX(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	if code == "" {
		errorResponse(w, "股票代码不能为空")
		return
	}

	klineType := strings.TrimSpace(r.URL.Query().Get("type"))
	if klineType == "" {
		klineType = "day"
	}
	limit := parsePositiveInt(r.URL.Query().Get("limit"))

	list, err := fetchStockKlineAllTDX(code, klineType)
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取K线失败: %v", err))
		return
	}

	if limit > 0 && len(list) > limit {
		list = list[len(list)-limit:]
	}

	respondKlineSuccess(w, "tdx", klineType, list)
}

// 获取股票全部历史K线（同花顺前复权）
func handleGetKlineAllTHS(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	if code == "" {
		errorResponse(w, "股票代码不能为空")
		return
	}

	klineType := strings.TrimSpace(r.URL.Query().Get("type"))
	if klineType == "" {
		klineType = "day"
	}
	limit := parsePositiveInt(r.URL.Query().Get("limit"))

	list, err := fetchStockKlineAllTHS(code, klineType)
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取同花顺K线失败: %v", err))
		return
	}

	if limit > 0 && len(list) > limit {
		list = list[len(list)-limit:]
	}

	respondKlineSuccess(w, "ths", klineType, list)
}

// 获取交易日信息
func handleGetWorkday(w http.ResponseWriter, r *http.Request) {
	if manager == nil || manager.Workday == nil {
		errorResponse(w, "交易日模块未初始化")
		return
	}

	dateParam := strings.TrimSpace(r.URL.Query().Get("date"))
	countStr := strings.TrimSpace(r.URL.Query().Get("count"))

	count := 1
	if countStr != "" {
		if v, err := strconv.Atoi(countStr); err == nil {
			if v < 1 {
				v = 1
			}
			if v > 30 {
				v = 30
			}
			count = v
		}
	}

	target := time.Now()
	if dateParam != "" {
		parsed, err := parseWorkdayDate(dateParam)
		if err != nil {
			errorResponse(w, "date 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
			return
		}
		target = parsed
	}

	isWorkday := manager.Workday.Is(target)

	response := map[string]interface{}{
		"date": map[string]string{
			"iso":     target.Format("2006-01-02"),
			"numeric": target.Format("20060102"),
		},
		"is_workday": isWorkday,
		"next":       collectNeighborWorkdays(target, count, 1),
		"previous":   collectNeighborWorkdays(target, count, -1),
	}

	successResponse(w, response)
}

// 获取指定范围内的交易日列表
func handleGetWorkdayRange(w http.ResponseWriter, r *http.Request) {
	if manager == nil || manager.Workday == nil {
		errorResponse(w, "交易日模块未初始化")
		return
	}

	startParam := strings.TrimSpace(r.URL.Query().Get("start"))
	endParam := strings.TrimSpace(r.URL.Query().Get("end"))
	if startParam == "" || endParam == "" {
		errorResponse(w, "start 与 end 均为必填参数")
		return
	}

	startDate, err := parseWorkdayDate(startParam)
	if err != nil {
		errorResponse(w, "start 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
		return
	}
	endDate, err := parseWorkdayDate(endParam)
	if err != nil {
		errorResponse(w, "end 参数格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
		return
	}
	if endDate.Before(startDate) {
		errorResponse(w, "end 必须大于或等于 start")
		return
	}

	list := make([]map[string]string, 0)
	manager.Workday.Range(startDate, endDate.AddDate(0, 0, 1), func(t time.Time) bool {
		list = append(list, map[string]string{
			"iso":     t.Format("2006-01-02"),
			"numeric": t.Format("20060102"),
		})
		return true
	})

	if len(list) == 0 {
		if err := manager.Workday.Update(); err == nil {
			manager.Workday.Range(startDate, endDate.AddDate(0, 0, 1), func(t time.Time) bool {
				list = append(list, map[string]string{
					"iso":     t.Format("2006-01-02"),
					"numeric": t.Format("20060102"),
				})
				return true
			})
		} else {
			log.Printf("刷新交易日失败: %v", err)
		}
	}

	successResponse(w, map[string]interface{}{
		"count": len(list),
		"list":  list,
	})
}

// 获取服务器状态
func handleGetServerStatus(w http.ResponseWriter, r *http.Request) {
	type ServerStatus struct {
		Status    string `json:"status"`
		Connected bool   `json:"connected"`
		Version   string `json:"version"`
		Uptime    string `json:"uptime"`
	}

	status := &ServerStatus{
		Status:    "running",
		Connected: true,
		Version:   "1.0.0",
		Uptime:    "unknown",
	}

	successResponse(w, status)
}

// 健康检查
func handleHealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "healthy",
		"time":   fmt.Sprintf("%d", 1730617200),
	})
}

// 基于K线的收益率计算
func handleGetIncome(w http.ResponseWriter, r *http.Request) {
	code := strings.TrimSpace(r.URL.Query().Get("code"))
	startParam := strings.TrimSpace(r.URL.Query().Get("start_date"))
	daysParam := strings.TrimSpace(r.URL.Query().Get("days"))

	if code == "" {
		errorResponse(w, "code 为必填参数")
		return
	}
	if startParam == "" {
		errorResponse(w, "start_date 为必填参数")
		return
	}

	startDate, err := parseFullDate(startParam)
	if err != nil {
		errorResponse(w, "start_date 格式错误，应为 YYYYMMDD 或 YYYY-MM-DD")
		return
	}

	dayOffsets := parseDaysParam(daysParam)
	if len(dayOffsets) == 0 {
		dayOffsets = []int{5, 10, 20, 60, 120}
	}

	resp, err := getQfqKlineDay(code)
	if err != nil {
		errorResponse(w, fmt.Sprintf("获取K线失败: %v", err))
		return
	}
	if resp == nil || len(resp.List) == 0 {
		successResponse(w, map[string]interface{}{
			"count": 0,
			"list":  []interface{}{},
		})
		return
	}

	klines := buildExtendKlines(code, resp.List)
	incomes := extend.DoIncomes(klines, startDate, dayOffsets...)

	list := make([]map[string]interface{}, 0, len(incomes))
	for _, income := range incomes {
		if income == nil {
			continue
		}
		list = append(list, map[string]interface{}{
			"offset":    income.Offset,
			"time":      income.Time.Format(time.RFC3339),
			"rise":      income.Rise().Float64(),
			"rise_rate": income.RiseRate(),
			"source": map[string]float64{
				"open":  income.Source.Open.Float64(),
				"high":  income.Source.High.Float64(),
				"low":   income.Source.Low.Float64(),
				"close": income.Source.Close.Float64(),
			},
			"current": map[string]float64{
				"open":  income.Current.Open.Float64(),
				"high":  income.Current.High.Float64(),
				"low":   income.Current.Low.Float64(),
				"close": income.Current.Close.Float64(),
			},
		})
	}

	successResponse(w, map[string]interface{}{
		"count": len(list),
		"list":  list,
	})
}

func getAllCodeModels() ([]*tdx.CodeModel, error) {
	if tdx.DefaultCodes != nil {
		if list, err := tdx.DefaultCodes.GetCodes(true); err == nil && len(list) > 0 {
			return list, nil
		} else if err != nil {
			log.Printf("从数据库读取代码失败: %v", err)
		}
	}

	aggregate := []*tdx.CodeModel{}
	for _, ex := range []protocol.Exchange{protocol.ExchangeSH, protocol.ExchangeSZ, protocol.ExchangeBJ} {
		resp, err := client.GetCodeAll(ex)
		if err != nil || resp == nil {
			if err != nil {
				log.Printf("从服务器获取代码失败(%s): %v", ex.String(), err)
			}
			continue
		}
		for _, v := range resp.List {
			aggregate = append(aggregate, &tdx.CodeModel{
				Name:      v.Name,
				Code:      v.Code,
				Exchange:  ex.String(),
				Multiple:  v.Multiple,
				Decimal:   v.Decimal,
				LastPrice: v.LastPrice,
			})
		}
	}

	return aggregate, nil
}

func classifyPrice(price float64, up, down, flat *int) {
	switch {
	case price > 0:
		*up = *up + 1
	case price < 0:
		*down = *down + 1
	default:
		*flat = *flat + 1
	}
}

func parseWorkdayDate(value string) (time.Time, error) {
	layouts := []string{"20060102", "2006-01-02"}
	for _, layout := range layouts {
		if t, err := time.ParseInLocation(layout, value, time.Local); err == nil {
			return t, nil
		}
	}
	return time.Time{}, fmt.Errorf("invalid date %s", value)
}

func collectNeighborWorkdays(base time.Time, count int, step int) []map[string]string {
	result := make([]map[string]string, 0, count)
	if manager == nil || manager.Workday == nil {
		return result
	}
	cursor := base
	attempts := 0
	maxAttempts := 366
	for len(result) < count && attempts < maxAttempts {
		attempts++
		cursor = cursor.AddDate(0, 0, step)
		if manager.Workday.Is(cursor) {
			result = append(result, map[string]string{
				"iso":     cursor.Format("2006-01-02"),
				"numeric": cursor.Format("20060102"),
			})
		}
	}
	return result
}

func parsePositiveInt(value string) int {
	if value == "" {
		return 0
	}
	n, err := strconv.Atoi(value)
	if err != nil || n <= 0 {
		return 0
	}
	return n
}

func parseFullDate(value string) (time.Time, error) {
	t, err := parseWorkdayDate(value)
	if err != nil {
		return time.Time{}, err
	}
	return time.Date(t.Year(), t.Month(), t.Day(), 15, 0, 0, 0, t.Location()), nil
}

func parseDaysParam(value string) []int {
	if value == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	days := make([]int, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if n, err := strconv.Atoi(part); err == nil && n > 0 {
			days = append(days, n)
		}
	}
	return days
}

func buildExtendKlines(code string, list []*protocol.Kline) extend.Klines {
	ks := make(extend.Klines, 0, len(list))
	for _, item := range list {
		if item == nil {
			continue
		}
		ks = append(ks, &extend.Kline{
			Code:   code,
			Date:   item.Time.Unix(),
			Open:   item.Open,
			High:   item.High,
			Low:    item.Low,
			Close:  item.Close,
			Volume: item.Volume,
			Amount: item.Amount,
		})
	}
	sort.Slice(ks, func(i, j int) bool {
		return ks[i].Date < ks[j].Date
	})
	return ks
}

func parseBool(value string) bool {
	if value == "" {
		return false
	}
	switch strings.ToLower(value) {
	case "1", "true", "yes", "y", "on":
		return true
	default:
		return false
	}
}

func fetchStockKlineAllTDX(code, klineType string) ([]*protocol.Kline, error) {
	switch strings.ToLower(klineType) {
	case "minute1":
		resp, err := client.GetKlineMinuteAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute5":
		resp, err := client.GetKline5MinuteAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute15":
		resp, err := client.GetKline15MinuteAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute30":
		resp, err := client.GetKline30MinuteAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "hour":
		resp, err := client.GetKlineHourAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "day":
		resp, err := client.GetKlineDayAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "week":
		resp, err := client.GetKlineWeekAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "month":
		resp, err := client.GetKlineMonthAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "quarter":
		resp, err := client.GetKlineQuarterAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "year":
		resp, err := client.GetKlineYearAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	default:
		return nil, fmt.Errorf("不支持的K线类型: %s", klineType)
	}
}

func fetchStockKlineAllTHS(code, klineType string) ([]*protocol.Kline, error) {
	resp, err := getQfqKlineDay(code)
	if err != nil {
		return nil, err
	}

	switch strings.ToLower(klineType) {
	case "", "day":
		return resp.List, nil
	case "week":
		return convertToWeekKline(resp).List, nil
	case "month":
		return convertToMonthKline(resp).List, nil
	default:
		return nil, fmt.Errorf("同花顺接口暂仅支持 type=day/week/month")
	}
}

func respondKlineSuccess(w http.ResponseWriter, source, klineType string, list []*protocol.Kline) {
	kType := strings.ToLower(klineType)
	meta := map[string]interface{}{
		"source": source,
		"type":   kType,
	}

	switch source {
	case "tdx":
		meta["batch_limit"] = 800
		meta["notes"] = []string{
			"通达信单次底层请求最多返回 800 条数据，服务端已顺序拼接全量结果",
			"对于上市时间较长的标的，请预估调用耗时（通常 1-5 秒），客户端可增加超时时间",
		}
	case "ths":
		meta["batch_limit"] = len(list)
		meta["notes"] = []string{
			"同花顺接口一次性返回前复权数据，响应时长取决于网络与标的数据量（通常 2-8 秒）",
			"建议调用方在 Python 等客户端中设置 ≥10 秒超时时间，并准备兜底策略",
		}
	default:
		meta["notes"] = []string{"未知数据源，请检查 source 参数"}
	}

	successResponse(w, map[string]interface{}{
		"count": len(list),
		"list":  list,
		"meta":  meta,
	})
}

func fetchIndexAll(code, klineType string) ([]*protocol.Kline, error) {
	switch strings.ToLower(klineType) {
	case "minute1":
		resp, err := client.GetIndexAll(protocol.TypeKlineMinute, code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute5":
		resp, err := client.GetIndexAll(protocol.TypeKline5Minute, code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute15":
		resp, err := client.GetIndexAll(protocol.TypeKline15Minute, code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "minute30":
		resp, err := client.GetIndexAll(protocol.TypeKline30Minute, code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "hour":
		resp, err := client.GetIndexAll(protocol.TypeKline60Minute, code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "week":
		resp, err := client.GetIndexWeekAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "month":
		resp, err := client.GetIndexMonthAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "quarter":
		resp, err := client.GetIndexQuarterAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "year":
		resp, err := client.GetIndexYearAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	case "day":
		fallthrough
	default:
		resp, err := client.GetIndexDayAll(code)
		if err != nil {
			return nil, err
		}
		return resp.List, nil
	}
}
