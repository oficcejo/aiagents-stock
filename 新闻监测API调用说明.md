# 每日热点新闻 API - 调用说明文档

## 📋 目录
- [基础信息](#基础信息)
- [快速开始](#快速开始)
- [接口说明](#接口说明)
- [支持的平台](#支持的平台)
- [调用示例](#调用示例)
- [错误处理](#错误处理)
- [注意事项](#注意事项)
- [常见问题](#常见问题)

---

## 基础信息

### API 地址
```
生产环境：https://newsapi.ws4.cn/api/v1/dailynews/
```

### 接口说明
获取各大平台的热点新闻数据，包括微博热搜、百度热搜、知乎热榜等20+个平台。

### 特性
- ✅ 支持多种主流平台
- ✅ 实时更新数据
- ✅ 无需认证即可使用
- ✅ JSON 格式返回
- ✅ 支持跨平台聚合查询

---

## 快速开始

### 最简单的调用
```bash
curl "https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu"
```

### Python 快速示例
```python
import requests

response = requests.get("https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu")
data = response.json()

print(f"获取到 {len(data['data'])} 条新闻")
```

---

## 接口说明

### 请求信息
- **方法**: GET
- **Content-Type**: application/json
- **编码**: UTF-8

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| platform | String | 是 | 平台代码，支持多个平台用逗号分隔 | `baidu` 或 `baidu,weibo,zhihu` |

### 返回格式

#### 成功响应
```json
{
  "status": "200",
  "data": [
    {
      "title": "新闻标题",
      "url": "新闻链接",
      "content": "新闻内容或描述",
      "source": "平台名称",
      "publish_time": "2026-01-24 11:52:52"
    }
  ],
  "msg": "success"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | String | 状态码，200 表示成功 |
| data | Array | 新闻数据列表 |
| data[].title | String | 新闻标题 |
| data[].url | String | 新闻链接 |
| data[].content | String | 新闻内容或描述 |
| data[].source | String | 平台来源 |
| data[].publish_time | String | 发布时间 |
| msg | String | 响应消息 |

---

## 支持的平台

| 序号 | 平台名称 | 平台代码 | 说明 |
|------|----------|----------|------|
| 1 | 百度热搜 | `baidu` | 社会热点、娱乐、事件 |
| 2 | 少数派 | `sspai` | 科技、数码、生活方式 |
| 3 | 微博热搜 | `weibo` | 社交媒体热点 |
| 4 | 知乎热榜 | `zhihu` | 问答、深度内容 |
| 5 | 36氪 | `tskr` | 科技创业、商业资讯 |
| 6 | 吾爱破解 | `ftpojie` | 技术、软件、安全 |
| 7 | 哔哩哔哩 | `bilibili` | 视频、动漫、游戏 |
| 8 | 豆瓣 | `douban` | 书影音、文化 |
| 9 | 虎扑 | `hupu` | 体育、游戏 |
| 10 | 百度贴吧 | `tieba` | 兴趣社区 |
| 11 | 掘金 | `juejin` | 编程、技术 |
| 12 | 抖音 | `douyin` | 短视频热点 |
| 13 | V2EX | `v2ex` | 技术、编程 |
| 14 | 今日头条 | `jinritoutiao` | 新闻热点 |
| 15 | Stack Overflow | `stackoverflow` | 编程问答 |
| 16 | GitHub Trending | `github` | 开源项目 |
| 17 | Hacker News | `hackernews` | 科技新闻 |
| 18 | 新浪财经 | `sina_finance` | 财经新闻 |
| 19 | 东方财富 | `eastmoney` | 财经资讯 |
| 20 | 雪球 | `xueqiu` | 股票投资 |
| 21 | 财联社 | `cls` | 财经快讯 |
| 22 | 腾讯网 | `tenxunwang` | 综合新闻 |

---

## 调用示例

### 1. cURL

#### 获取单个平台
```bash
curl "https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu"
```

#### 获取多个平台
```bash
curl "https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu,weibo,zhihu"
```

#### 完整示例
```bash
curl -X GET "https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu" \
  -H "Content-Type: application/json"
```

---

### 2. Python

#### 使用 requests 库
```python
import requests

def get_news(platform="baidu"):
    url = "https://newsapi.ws4.cn/api/v1/dailynews/"
    params = {"platform": platform}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == '200':
            print(f"获取到 {len(data['data'])} 条新闻")
            return data['data']
        else:
            print(f"请求失败: {data['msg']}")
            return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []

# 使用示例
news_list = get_news("baidu")
for news in news_list[:5]:
    print(f"标题: {news['title']}")
    print(f"链接: {news['url']}")
    print(f"时间: {news['publish_time']}\n")
```

#### 获取多个平台
```python
def get_multiple_news(platforms):
    platforms_str = ",".join(platforms)
    url = f"https://newsapi.ws4.cn/api/v1/dailynews/?platform={platforms_str}"

    response = requests.get(url)
    return response.json()

# 使用示例
data = get_multiple_news(["baidu", "weibo", "zhihu"])
print(f"总共获取到 {len(data['data'])} 条新闻")
```

#### 异步请求（多个平台）
```python
import asyncio
import aiohttp

async def fetch_news(session, platform):
    url = "https://newsapi.ws4.cn/api/v1/dailynews/"
    async with session.get(url, params={"platform": platform}) as response:
        return await response.json()

async def get_news_async(platforms):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_news(session, p) for p in platforms]
        results = await asyncio.gather(*tasks)
        return results

# 使用示例
import asyncio
platforms = ["baidu", "weibo", "zhihu"]
results = asyncio.run(get_news_async(platforms))

for i, result in enumerate(results):
    print(f"{platforms[i]}: {len(result['data'])} 条新闻")
```

---

### 3. JavaScript / Node.js

#### 使用 fetch（浏览器或现代 Node.js）
```javascript
async function getNews(platform = 'baidu') {
  const url = `https://newsapi.ws4.cn/api/v1/dailynews/?platform=${platform}`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    if (data.status === '200') {
      console.log(`获取到 ${data.data.length} 条新闻`);
      return data.data;
    } else {
      console.log('请求失败:', data.msg);
      return [];
    }
  } catch (error) {
    console.log('发生错误:', error);
    return [];
  }
}

// 使用示例
getNews('baidu').then(newsList => {
  newsList.slice(0, 5).forEach(news => {
    console.log(`标题: ${news.title}`);
    console.log(`链接: ${news.url}\n`);
  });
});
```

#### 使用 axios
```javascript
const axios = require('axios');

async function getNews(platform) {
  try {
    const response = await axios.get('https://newsapi.ws4.cn/api/v1/dailynews/', {
      params: { platform }
    });

    console.log(`获取到 ${response.data.data.length} 条新闻`);
    return response.data.data;
  } catch (error) {
    console.error('发生错误:', error);
    return [];
  }
}

// 使用示例
getNews('baidu').then(newsList => {
  newsList.forEach((news, index) => {
    console.log(`${index + 1}. ${news.title}`);
  });
});
```

#### Node.js 使用 https 模块
```javascript
const https = require('https');

function getNews(platform, callback) {
  const url = `https://newsapi.ws4.cn/api/v1/dailynews/?platform=${platform}`;

  https.get(url, (res) => {
    let data = '';

    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        callback(null, result);
      } catch (error) {
        callback(error, null);
      }
    });
  }).on('error', (error) => {
    callback(error, null);
  });
}

// 使用示例
getNews('baidu', (error, result) => {
  if (error) {
    console.error('请求失败:', error);
    return;
  }

  console.log(`获取到 ${result.data.length} 条新闻`);
});
```

---

### 4. Java

#### 使用 HttpURLConnection
```java
import java.io.*;
import java.net.*;
import java.util.*;

public class NewsApiClient {

    public static String getNews(String platform) {
        try {
            String url = "https://newsapi.ws4.cn/api/v1/dailynews/?platform=" + platform;
            URL urlObj = new URL(url);
            HttpURLConnection conn = (HttpURLConnection) urlObj.openConnection();

            conn.setRequestMethod("GET");
            conn.setRequestProperty("Content-Type", "application/json");

            int responseCode = conn.getResponseCode();
            BufferedReader in = new BufferedReader(
                new InputStreamReader(conn.getInputStream())
            );

            String inputLine;
            StringBuilder response = new StringBuilder();

            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();

            return response.toString();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static void main(String[] args) {
        String jsonResponse = getNews("baidu");
        System.out.println(jsonResponse);
    }
}
```

#### 使用 OkHttp
```java
import okhttp3.*;
import java.io.IOException;

public class NewsApi {

    private static final OkHttpClient client = new OkHttpClient();

    public static void getNews(String platform) throws IOException {
        HttpUrl url = HttpUrl.parse("https://newsapi.ws4.cn/api/v1/dailynews/")
                .newBuilder()
                .addQueryParameter("platform", platform)
                .build();

        Request request = new Request.Builder()
                .url(url)
                .get()
                .build();

        try (Response response = client.newCall(request).execute()) {
            String jsonData = response.body().string();
            System.out.println(jsonData);
        }
    }

    public static void main(String[] args) throws IOException {
        getNews("baidu");
    }
}
```

---

### 5. Go

```go
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

type News struct {
    Title       string `json:"title"`
    URL         string `json:"url"`
    Content     string `json:"content"`
    Source      string `json:"source"`
    PublishTime string `json:"publish_time"`
}

type Response struct {
    Status string `json:"status"`
    Data   []News `json:"data"`
    Msg    string `json:"msg"`
}

func getNews(platform string) (*Response, error) {
    url := fmt.Sprintf("https://newsapi.ws4.cn/api/v1/dailynews/?platform=%s", platform)

    resp, err := http.Get(url)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }

    var result Response
    if err := json.Unmarshal(body, &result); err != nil {
        return nil, err
    }

    return &result, nil
}

func main() {
    data, err := getNews("baidu")
    if err != nil {
        fmt.Println("Error:", err)
        return
    }

    fmt.Printf("获取到 %d 条新闻\n", len(data.Data))
    for i, news := range data.Data {
        if i >= 5 {
            break
        }
        fmt.Printf("%d. %s\n", i+1, news.Title)
    }
}
```

---

### 6. PHP

```php
<?php

function getNews($platform = 'baidu') {
    $url = 'https://newsapi.ws4.cn/api/v1/dailynews/?platform=' . $platform;

    $response = file_get_contents($url);

    if ($response === false) {
        return null;
    }

    return json_decode($response, true);
}

// 使用示例
$newsData = getNews('baidu');

if ($newsData && $newsData['status'] === '200') {
    echo "获取到 " . count($newsData['data']) . " 条新闻\n";

    foreach (array_slice($newsData['data'], 0, 5) as $news) {
        echo "标题: " . $news['title'] . "\n";
        echo "链接: " . $news['url'] . "\n\n";
    }
}
?>
```

---

### 7. Ruby

```ruby
require 'net/http'
require 'json'
require 'uri'

def get_news(platform = 'baidu')
  uri = URI.parse("https://newsapi.ws4.cn/api/v1/dailynews/?platform=#{platform}")
  response = Net::HTTP.get_response(uri)

  if response.is_a?(Net::HTTPSuccess)
    data = JSON.parse(response.body)
    return data
  else
    puts "请求失败: #{response.code}"
    return nil
  end
end

# 使用示例
result = get_news('baidu')

if result && result['status'] == '200'
  puts "获取到 #{result['data'].size} 条新闻"

  result['data'].first(5).each_with_index do |news, index|
    puts "#{index + 1}. #{news['title']}"
  end
end
```

---

## 错误处理

### 常见错误码

| 状态码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | 正常处理数据 |
| 404 | 平台代码错误 | 检查平台代码是否正确 |
| 500 | 服务器内部错误 | 稍后重试 |

### 错误处理示例（Python）

```python
import requests
import time

def get_news_with_retry(platform, max_retries=3):
    url = "https://newsapi.ws4.cn/api/v1/dailynews/"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params={"platform": platform}, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '200':
                    return data.get('data', [])
                else:
                    print(f"API返回错误: {data.get('msg')}")
                    return []
            elif response.status_code == 404:
                print(f"平台代码错误: {platform}")
                return []
            elif response.status_code == 500:
                print(f"服务器错误，第 {attempt + 1} 次重试...")
                time.sleep(2)
            else:
                print(f"未知错误: {response.status_code}")
                return []

        except requests.exceptions.Timeout:
            print(f"请求超时，第 {attempt + 1} 次重试...")
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f"连接错误，第 {attempt + 1} 次重试...")
            time.sleep(2)
        except Exception as e:
            print(f"发生未知错误: {e}")
            return []

    print("达到最大重试次数，请求失败")
    return []
```

---

## 注意事项

### 1. 数据时效性
- 数据实时更新，建议不要频繁请求
- 推荐缓存时间：5-10 分钟
- 不同平台更新频率不同

### 2. 请求频率限制
- 目前没有明确的速率限制
- 建议合理使用，避免过度请求
- 生产环境建议加入请求队列

### 3. 数据准确性
- 数据仅供参考，不应作为新闻的主要来源
- 建议与官方平台数据交叉验证

### 4. 合法使用
- API 仅供合法使用
- 任何非法使用均不受支持
- 用户需自行承担使用责任

### 5. HTTPS 要求
- 必须使用 HTTPS 协议
- HTTP 请求可能会被拒绝

---

## 常见问题

### Q1: 如何获取多个平台的数据？
**A**: 使用逗号分隔多个平台代码
```bash
curl "https://newsapi.ws4.cn/api/v1/dailynews/?platform=baidu,weibo,zhihu"
```

### Q2: 数据多久更新一次？
**A**: 不同平台更新频率不同，一般为 30 分钟到 2 小时不等。建议缓存数据，避免频繁请求。

### Q3: 是否需要 API 密钥？
**A**: 目前不需要，接口可以直接调用。

### Q4: 支持哪些编程语言？
**A**: 支持所有支持 HTTP 请求的编程语言，本文档提供了 Python、JavaScript、Java、Go、PHP、Ruby 等示例。

### Q5: 接口限流吗？
**A**: 目前没有明确的限流策略，但建议合理使用。

### Q6: 如何处理中文编码？
**A**: 接口返回的是 UTF-8 编码的 JSON，大多数现代语言都能自动处理。如果遇到乱码，请确保使用 UTF-8 解码。

### Q7: 如何获取新闻的详细内容？
**A**: API 只返回标题和链接，详细内容需要访问链接页面获取。

### Q8: 数据可以商用吗？
**A**: 数据来源于各公开平台，使用时请遵守各平台的使用协议和相关法律法规。

---

## 技术支持

- **API 文档**: https://newsapi.ws4.cn/docs
- **健康检查**: https://newsapi.ws4.cn/health

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-24 | 1.0.0 | 初始版本，支持 20+ 个平台 |

---

**免责声明**: 本 API 提供的信息仅供参考，使用者应从其他平台验证信息的准确性和时效性。
