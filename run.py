import uvicorn

if __name__ == "__main__":
    # 这里直接配置好所有的启动参数
    # 这样你就不用每次都在命令行里敲 --host 0.0.0.0 --port 8088 了
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8088, 
        reload=True  # 开发模式下开启热重载
    )