# 使用官方Python镜像作为基础镜像
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim

# 设置时区环境变量
ENV TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 安装Node.js (pywencai需要)、中文字体 (PDF生成需要) 和时区数据
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 验证安装
RUN node --version && npm --version

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖 - 修改后的部分
# 永久配置pip使用国内镜像源并增加超时时间[1](@ref)[2](@ref)
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data && chmod 777 /app/data

# 暴露Streamlit默认端口
EXPOSE 8501

# 设置健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动应用
CMD ["python", "run.py"]

