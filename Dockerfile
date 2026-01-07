# 1. 使用官方 Python 轻量级镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 换源：加速 apt 包下载（使用清华镜像源）
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list

# 4. 安装系统依赖 (bcrypt 需要编译，需要 build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖文件并安装（使用清华大学 PyPI 镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt

# 5. 复制所有项目代码
COPY . .

# 6. 暴露后端端口
EXPOSE 8088

# 7. 启动后端服务
CMD ["python", "run.py"]