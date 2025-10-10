# PDF中文乱码修复说明

## 问题描述
在Docker环境中，PDF导出时中文显示为乱码或方框，但本地Windows环境正常。

## 原因分析
- Docker容器基于Linux系统，默认不包含中文字体
- PDF生成器（reportlab）需要中文字体才能正确渲染中文字符
- 原代码只配置了Windows系统的字体路径

## 修复方案

### 已修改的文件

#### 1. `Dockerfile` 
添加了中文字体包安装：
```dockerfile
# 安装Node.js (pywencai需要) 和中文字体 (PDF生成需要)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

安装的字体包：
- **fonts-noto-cjk**: Google Noto CJK字体（支持中日韩文字）
- **fonts-wqy-zenhei**: 文泉驿正黑体
- **fonts-wqy-microhei**: 文泉驿微米黑体
- **fontconfig**: 字体配置工具

#### 2. `pdf_generator.py`
更新了字体注册函数，支持Linux系统：
```python
def register_chinese_fonts():
    """注册中文字体 - 支持Windows和Linux系统"""
    # Windows系统字体路径
    windows_font_paths = [...]
    
    # Linux系统字体路径（Docker环境）
    linux_font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        # ... 更多字体路径
    ]
```

## 重新部署步骤

### 方式一：Docker Compose（推荐）

```bash
# 1. 停止并删除现有容器
docker-compose down

# 2. 删除旧镜像（可选，但推荐）
docker rmi agentsstock1-app

# 3. 重新构建并启动
docker-compose up -d --build

# 4. 查看日志，确认字体加载成功
docker-compose logs -f
```

### 方式二：Docker命令

```bash
# 1. 停止并删除现有容器
docker stop agentsstock1
docker rm agentsstock1

# 2. 删除旧镜像
docker rmi agentsstock1

# 3. 重新构建镜像
docker build -t agentsstock1 .

# 4. 启动新容器
docker run -d -p 8503:8501 \
  -v $(pwd)/.env:/app/.env \
  --name agentsstock1 \
  agentsstock1

# 5. 查看日志
docker logs -f agentsstock1
```

## 验证修复

### 1. 检查字体安装
进入容器检查字体：
```bash
docker exec -it agentsstock1 bash
fc-list :lang=zh  # 列出所有中文字体
```

应该看到类似输出：
```
/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc: WenQuanYi Zen Hei:style=Regular
/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc: Noto Sans CJK SC:style=Regular
...
```

### 2. 查看应用日志
在生成PDF时，日志中应该显示：
```
✅ 成功注册中文字体: /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
```

### 3. 测试PDF导出
1. 在Web界面分析任意股票
2. 点击"生成并下载PDF报告"
3. 打开下载的PDF文件
4. 确认中文正常显示

## 故障排查

### 问题1：构建时字体安装失败
**现象**：构建过程中apt-get install失败

**解决方案**：
```bash
# 清理Docker缓存后重试
docker system prune -a
docker-compose build --no-cache
```

### 问题2：字体未加载
**现象**：日志显示"未找到中文字体"

**检查步骤**：
1. 确认Dockerfile中正确添加了字体包
2. 进入容器检查字体文件是否存在
3. 运行 `fc-cache -fv` 刷新字体缓存

### 问题3：PDF仍然乱码
**现象**：字体已安装但PDF中文仍显示为方框

**可能原因**：
1. 字体文件权限问题
2. reportlab缓存问题
3. 字体格式不兼容

**解决方案**：
```bash
# 重新构建时清理所有缓存
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## 技术说明

### 字体选择
我们安装了3种字体包：
1. **Noto Sans CJK**：Google开发，覆盖范围广，质量高
2. **文泉驿正黑**：开源中文字体，适合阅读
3. **文泉驿微米黑**：适合小字号显示

系统会按优先级自动选择第一个可用的字体。

### 字体文件格式
- **TTC**：TrueType Collection（字体集合文件）
- **TTF**：TrueType Font（单个字体文件）

reportlab的TTFont可以处理这两种格式。

### Docker镜像大小
添加中文字体后，镜像大小会增加约50-100MB：
- fonts-noto-cjk: ~70MB
- fonts-wqy-zenhei: ~10MB
- fonts-wqy-microhei: ~5MB

这是正常的，为了支持完整的中文显示必须付出的空间代价。

## 注意事项

1. **本地环境无影响**：修改后的代码在Windows本地环境仍然正常工作
2. **字体缓存**：首次启动时fontconfig会建立字体缓存，可能需要几秒钟
3. **镜像更新**：已部署的用户需要重新构建镜像才能应用修复
4. **备份数据**：重新部署前请备份数据库文件（.db文件）

## 相关资源

- [ReportLab中文支持文档](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Noto字体项目](https://www.google.com/get/noto/)
- [文泉驿字体项目](http://wenq.org/)
- [Docker字体配置指南](https://docs.docker.com/config/)

## 更新日志

- **2025-10-10**: 初始版本，添加Docker中文字体支持
- **2025-10-10**: 更新pdf_generator.py，支持跨平台字体检测

---

如有问题，请联系：ws3101001@126.com

