# 1. 使用官方 Python 轻量级镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 安装系统依赖 (bcrypt 需要编译，需要 build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖文件并安装 (保留 pip 加速)
COPY requirements.txt .
# 使用阿里云或清华镜像加速 pip
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 5. 复制所有项目代码
COPY . .

# 6. 暴露后端端口
EXPOSE 8088

# 7. 启动后端服务
CMD ["python", "run.py"]