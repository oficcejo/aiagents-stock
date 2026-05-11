// 全局变量
let currentStock = '';
let klineChart = null;
let minuteChart = null;

// 工具函数 - 显示加载
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

// 工具函数 - 隐藏加载
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 工具函数 - 格式化数字
function formatNumber(num, decimals = 2) {
    if (!num || isNaN(num)) return '--';
    return parseFloat(num).toFixed(decimals);
}

// 工具函数 - 格式化金额（转换为万、亿）
function formatAmount(num) {
    if (!num || isNaN(num)) return '--';
    num = parseFloat(num);
    if (num >= 100000000) {
        return (num / 100000000).toFixed(2) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(2) + '万';
    }
    return num.toFixed(2);
}

// 工具函数 - 格式化价格（将厘转为元）
function formatPrice(price) {
    if (!price || isNaN(price)) return '--';
    return (parseFloat(price) / 1000).toFixed(2);
}

// 搜索股票
async function searchStock() {
    const keyword = document.getElementById('stockCode').value.trim();
    if (!keyword) {
        alert('请输入股票代码或名称');
        return;
    }

    // 如果直接输入的是6位股票代码，直接加载
    if (/^\d{6}$/.test(keyword)) {
        currentStock = keyword;
        loadStockData(keyword);
        return;
    }

    // 否则搜索
    showLoading();
    try {
        const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`);
        const result = await response.json();
        
        if (result.code === 0 && result.data && result.data.length > 0) {
            displaySearchResults(result.data);
        } else {
            alert('未找到相关股票');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败，请重试');
    } finally {
        hideLoading();
    }
}

// 显示搜索结果
function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    container.innerHTML = '';
    
    results.forEach(item => {
        const div = document.createElement('div');
        div.className = 'search-item';
        div.innerHTML = `
            <span class="search-item-code">${item.code}</span>
            <span class="search-item-name">${item.name}</span>
        `;
        div.onclick = () => {
            currentStock = item.code;
            loadStockData(item.code);
            container.innerHTML = '';
        };
        container.appendChild(div);
    });
}

// 加载股票数据
async function loadStockData(code) {
    showLoading();
    document.getElementById('mainContent').style.display = 'block';
    
    try {
        // 加载五档行情
        await loadQuote(code);
        
        // 默认加载日K线
        await loadKline('day');
        
        // 加载分时数据
        await loadMinute(code);
        
        // 加载分时成交
        await loadTrade(code);
        
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败，请重试');
    } finally {
        hideLoading();
    }
}

// 加载五档行情
async function loadQuote(code) {
    try {
        const response = await fetch(`/api/quote?code=${code}`);
        const result = await response.json();
        
        if (result.code === 0 && result.data && result.data.length > 0) {
            const quote = result.data[0];
            displayQuote(quote);
        }
    } catch (error) {
        console.error('加载五档行情失败:', error);
    }
}

// 显示五档行情
function displayQuote(quote) {
    // 更新股票名称和代码
    document.getElementById('stockName').textContent = quote.Code || '--';
    document.getElementById('stockCode2').textContent = quote.Code || '--';
    
    // 计算价格（从厘转为元）
    const lastPrice = parseFloat(quote.K.Last) / 1000;
    const currentPrice = parseFloat(quote.K.Close) / 1000;
    const openPrice = parseFloat(quote.K.Open) / 1000;
    const highPrice = parseFloat(quote.K.High) / 1000;
    const lowPrice = parseFloat(quote.K.Low) / 1000;
    
    const priceChange = currentPrice - lastPrice;
    const priceChangePercent = lastPrice > 0 ? (priceChange / lastPrice * 100) : 0;
    
    // 更新基本信息
    document.getElementById('lastPrice').textContent = currentPrice.toFixed(2);
    document.getElementById('priceChange').textContent = priceChange > 0 ? '+' + priceChange.toFixed(2) : priceChange.toFixed(2);
    document.getElementById('priceChangePercent').textContent = priceChangePercent > 0 ? '+' + priceChangePercent.toFixed(2) + '%' : priceChangePercent.toFixed(2) + '%';
    document.getElementById('volume').textContent = formatAmount(quote.TotalHand * 100);
    document.getElementById('amount').textContent = formatAmount(quote.Amount);
    document.getElementById('openPrice').textContent = openPrice.toFixed(2);
    document.getElementById('highPrice').textContent = highPrice.toFixed(2);
    document.getElementById('lowPrice').textContent = lowPrice.toFixed(2);
    
    // 设置涨跌颜色
    const priceElements = [document.getElementById('lastPrice'), 
                          document.getElementById('priceChange'), 
                          document.getElementById('priceChangePercent')];
    priceElements.forEach(el => {
        el.className = 'value price ' + (priceChange >= 0 ? 'up' : 'down');
    });
    
    // 更新买卖五档
    const sellLevels = document.getElementById('sellLevels');
    sellLevels.innerHTML = '';
    for (let i = 4; i >= 0; i--) {
        const level = quote.SellLevel[i];
        const price = parseFloat(level.Price) / 1000;
        const volume = Math.round(level.Number / 100);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>卖${i + 1}</td>
            <td>${price.toFixed(2)}</td>
            <td>${volume}</td>
        `;
        sellLevels.appendChild(tr);
    }
    
    const buyLevels = document.getElementById('buyLevels');
    buyLevels.innerHTML = '';
    for (let i = 0; i < 5; i++) {
        const level = quote.BuyLevel[i];
        const price = parseFloat(level.Price) / 1000;
        const volume = Math.round(level.Number / 100);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>买${i + 1}</td>
            <td>${price.toFixed(2)}</td>
            <td>${volume}</td>
        `;
        buyLevels.appendChild(tr);
    }
}

// 加载K线数据
async function loadKline(type, buttonElement) {
    if (!currentStock) return;
    
    showLoading();
    try {
        const response = await fetch(`/api/kline?code=${currentStock}&type=${type}`);
        const result = await response.json();
        
        if (result.code === 0 && result.data) {
            displayKline(result.data, type);
        }
        
        // 更新按钮状态
        document.querySelectorAll('.btn-control').forEach(btn => {
            btn.classList.remove('active');
        });
        // 如果提供了按钮元素，添加active类
        if (buttonElement) {
            buttonElement.classList.add('active');
        } else {
            // 如果没有提供，根据type查找对应按钮
            const buttons = document.querySelectorAll('.btn-control');
            buttons.forEach(btn => {
                if (btn.textContent.includes(getKlineTypeName(type))) {
                    btn.classList.add('active');
                }
            });
        }
    } catch (error) {
        console.error('加载K线失败:', error);
    } finally {
        hideLoading();
    }
}

// 获取K线类型中文名称
function getKlineTypeName(type) {
    const typeMap = {
        'day': '日K',
        'week': '周K',
        'month': '月K',
        'minute30': '30分',
        'minute15': '15分',
        'minute5': '5分'
    };
    return typeMap[type] || '日K';
}

// 显示K线图
function displayKline(data, type) {
    if (!data.List || data.List.length === 0) {
        return;
    }
    
    const chartDom = document.getElementById('klineChart');
    if (!klineChart) {
        klineChart = echarts.init(chartDom);
    }
    if (!chartDom.offsetWidth || !chartDom.offsetHeight) {
        // 容器尚未正确展示时强制设置默认尺寸
        chartDom.style.width = '100%';
        chartDom.style.height = '600px';
        klineChart.resize();
    }
    
    // 准备数据
    const dates = [];
    const klineData = [];
    const volumes = [];
    
    data.List.forEach(item => {
        const date = new Date(item.Time);
        const dateStr = date.getFullYear() + '-' + 
                       String(date.getMonth() + 1).padStart(2, '0') + '-' + 
                       String(date.getDate()).padStart(2, '0') + ' ' +
                       String(date.getHours()).padStart(2, '0') + ':' +
                       String(date.getMinutes()).padStart(2, '0');
        dates.push(dateStr);
        
        const open = parseFloat(item.Open) / 1000;
        const close = parseFloat(item.Close) / 1000;
        const low = parseFloat(item.Low) / 1000;
        const high = parseFloat(item.High) / 1000;
        
        klineData.push([open, close, low, high]);
        volumes.push([dates.length - 1, item.Volume, close >= open ? 1 : -1]);
    });
    
    const option = {
        backgroundColor: '#fff',
        animation: false,
        legend: {
            data: ['K线', '成交量'],
            top: 10
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        grid: [
            {
                left: '8%',
                right: '3%',
                top: '10%',
                height: '60%'
            },
            {
                left: '8%',
                right: '3%',
                top: '75%',
                height: '15%'
            }
        ],
        xAxis: [
            {
                type: 'category',
                data: dates,
                scale: true,
                boundaryGap: true,
                axisLine: { onZero: false },
                splitLine: { show: false },
                min: 'dataMin',
                max: 'dataMax'
            },
            {
                type: 'category',
                gridIndex: 1,
                data: dates,
                scale: true,
                boundaryGap: true,
                axisLine: { onZero: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                min: 'dataMin',
                max: 'dataMax'
            }
        ],
        yAxis: [
            {
                scale: true,
                splitArea: {
                    show: true
                }
            },
            {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            },
            {
                show: true,
                xAxisIndex: [0, 1],
                type: 'slider',
                top: '93%',
                start: 0,
                end: 100
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: klineData,
                itemStyle: {
                    color: '#ef232a',
                    color0: '#14b143',
                    borderColor: '#ef232a',
                    borderColor0: '#14b143'
                }
            },
            {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes.map(item => item[1]),
                itemStyle: {
                    color: function(params) {
                        return volumes[params.dataIndex][2] > 0 ? '#ef232a' : '#14b143';
                    }
                }
            }
        ]
    };
    
    klineChart.setOption(option);
    klineChart.resize();
}

// 加载分时数据
async function loadMinute(code) {
    try {
        const response = await fetch(`/api/minute?code=${code}`);
        const result = await response.json();
        
        if (result.code === 0 && result.data) {
            displayMinute(result.data);
        }
    } catch (error) {
        console.error('加载分时数据失败:', error);
    }
}

// 显示分时图
function displayMinute(data) {
    if (!data.List || data.List.length === 0) {
        return;
    }
    
    const chartDom = document.getElementById('minuteChart');
    if (!minuteChart) {
        minuteChart = echarts.init(chartDom);
    }
    
    const times = [];
    const prices = [];
    const volumes = [];
    
    data.List.forEach(item => {
        times.push(item.Time);
        prices.push((parseFloat(item.Price) / 1000).toFixed(2));
        volumes.push(item.Number);
    });
    
    const option = {
        backgroundColor: '#fff',
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        grid: [
            {
                left: '8%',
                right: '3%',
                top: '10%',
                height: '60%'
            },
            {
                left: '8%',
                right: '3%',
                top: '75%',
                height: '15%'
            }
        ],
        xAxis: [
            {
                type: 'category',
                data: times,
                boundaryGap: false,
                axisLine: { onZero: false },
                splitLine: { show: false }
            },
            {
                type: 'category',
                gridIndex: 1,
                data: times,
                boundaryGap: false,
                axisLine: { onZero: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false }
            }
        ],
        yAxis: [
            {
                scale: true,
                splitArea: {
                    show: true
                }
            },
            {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: '价格',
                type: 'line',
                data: prices,
                smooth: true,
                symbol: 'none',
                lineStyle: {
                    color: '#1890ff',
                    width: 2
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                        { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
                    ])
                }
            },
            {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes,
                itemStyle: {
                    color: '#1890ff'
                }
            }
        ]
    };
    
    minuteChart.setOption(option);
    minuteChart.resize();
}

// 加载分时成交
async function loadTrade(code) {
    try {
        const response = await fetch(`/api/trade?code=${code}`);
        const result = await response.json();
        
        if (result.code === 0 && result.data) {
            displayTrade(result.data);
        }
    } catch (error) {
        console.error('加载分时成交失败:', error);
    }
}

// 显示分时成交
function displayTrade(data) {
    if (!data.List || data.List.length === 0) {
        document.getElementById('tradeTableBody').innerHTML = '<tr><td colspan="5">暂无数据</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('tradeTableBody');
    tbody.innerHTML = '';
    
    // 只显示最近200条
    const trades = data.List.slice(0, 200);
    
    trades.forEach(item => {
        const time = new Date(item.Time);
        const timeStr = String(time.getHours()).padStart(2, '0') + ':' + 
                       String(time.getMinutes()).padStart(2, '0') + ':' +
                       String(time.getSeconds()).padStart(2, '0');
        const price = (parseFloat(item.Price) / 1000).toFixed(2);
        const volume = item.Volume;
        const amount = formatAmount(parseFloat(item.Price) / 1000 * volume * 100);
        const status = item.Status === 0 ? '买入' : (item.Status === 1 ? '卖出' : '--');
        const statusClass = item.Status === 0 ? 'trade-buy' : (item.Status === 1 ? 'trade-sell' : '');
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${timeStr}</td>
            <td class="${statusClass}">${price}</td>
            <td>${volume}</td>
            <td>${amount}</td>
            <td class="${statusClass}">${status}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 切换标签页
function switchTab(evt, tabName) {
    // 更新标签按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (evt && evt.target) {
        evt.target.classList.add('active');
    }
    
    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const activeTab = document.getElementById(tabName + 'Tab');
    activeTab.classList.add('active');

    // 切换到图表时触发自适应，解决在隐藏容器中初始化导致的宽度问题
    requestAnimationFrame(() => {
        if (tabName === 'kline' && klineChart) {
            setTimeout(() => klineChart.resize(), 50);
        }
        if (tabName === 'minute' && minuteChart) {
            setTimeout(() => minuteChart.resize(), 50);
        }
    });
}

// 监听回车键搜索
document.getElementById('stockCode').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchStock();
    }
});

// 窗口大小改变时重新渲染图表
let resizeTimer;
window.addEventListener('resize', function() {
    // 防抖优化，避免频繁调用
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        if (klineChart) {
            klineChart.resize();
        }
        if (minuteChart) {
            minuteChart.resize();
        }
    }, 100);
});

