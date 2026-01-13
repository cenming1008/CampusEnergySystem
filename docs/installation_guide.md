# 安装指南

## 🐍 Python 环境说明

你的系统已安装 Python 3.9.6，但需要注意：

### macOS 上的 Python 命令

在 macOS 上，通常需要使用：
- `python3` 而不是 `python`
- `pip3` 而不是 `pip`

或者使用模块方式：
- `python3 -m pip` 而不是 `pip`

## 📦 安装依赖的三种方法

### 方法1：使用虚拟环境（推荐）

项目已经有虚拟环境 `venv/`，按以下步骤操作：

```bash
# 1. 进入项目目录
cd /Users/todo/MineEnergySystem

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖（现在可以使用 pip 了）
pip install -r requirements.txt
```

激活虚拟环境后，命令提示符会显示 `(venv)`，这时可以直接使用 `pip`。

### 方法2：使用 pip3（不激活虚拟环境）

```bash
# 直接使用 pip3
pip3 install -r requirements.txt

# 或者使用 python3 -m pip
python3 -m pip install -r requirements.txt
```

### 方法3：重新创建虚拟环境

如果虚拟环境有问题，可以重新创建：

```bash
# 1. 删除旧虚拟环境（可选）
rm -rf venv

# 2. 创建新虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级 pip
pip install --upgrade pip

# 5. 安装依赖
pip install -r requirements.txt
```

## 🔍 检查安装

安装完成后，检查关键包：

```bash
# 激活虚拟环境后
source venv/bin/activate

# 检查包
python3 -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python3 -c "import tensorflow; print('TensorFlow:', tensorflow.__version__)"
python3 -c "import sklearn; print('scikit-learn:', sklearn.__version__)"
```

## ⚠️ 常见问题

### 问题1：command not found: pip

**原因**：macOS 默认没有 `pip` 命令，只有 `pip3`

**解决**：
```bash
# 使用 pip3
pip3 install -r requirements.txt

# 或激活虚拟环境后使用 pip
source venv/bin/activate
pip install -r requirements.txt
```

### 问题2：权限错误

**错误**：`Permission denied` 或 `Could not install packages`

**解决**：
```bash
# 不要使用 sudo，而是使用虚拟环境
source venv/bin/activate
pip install -r requirements.txt

# 或者使用 --user 标志
pip3 install --user -r requirements.txt
```

### 问题3：TensorFlow 安装失败

**原因**：TensorFlow 较大，可能需要较长时间

**解决**：
```bash
# 使用国内镜像加速
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple tensorflow

# 或激活虚拟环境后
source venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 问题4：虚拟环境激活失败

**错误**：`source: no such file or directory`

**解决**：
```bash
# 确保在项目根目录
cd /Users/todo/MineEnergySystem

# 使用完整路径
source ./venv/bin/activate

# 或使用点号
. venv/bin/activate
```

## 📝 快速安装脚本

创建 `scripts/install_dependencies.sh`：

```bash
#!/bin/bash
# 安装依赖脚本

cd "$(dirname "$0")/.."

echo "🔍 检查 Python 环境..."
python3 --version

echo "📦 激活虚拟环境..."
source venv/bin/activate

echo "⬆️ 升级 pip..."
pip install --upgrade pip

echo "📥 安装依赖..."
pip install -r requirements.txt

echo "✅ 安装完成！"
echo ""
echo "检查安装："
python3 -c "import fastapi; print('✓ FastAPI 已安装')" 2>/dev/null || echo "✗ FastAPI 未安装"
python3 -c "import tensorflow; print('✓ TensorFlow 已安装')" 2>/dev/null || echo "✗ TensorFlow 未安装"
```

使用：
```bash
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
```

## 🎯 推荐工作流程

### 日常开发

```bash
# 1. 进入项目目录
cd /Users/todo/MineEnergySystem

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 开发工作...

# 4. 退出虚拟环境（可选）
deactivate
```

### 安装新包

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装新包
pip install 包名

# 更新 requirements.txt
pip freeze > requirements.txt
```

## 💡 提示

1. **始终使用虚拟环境**：避免污染系统 Python 环境
2. **激活虚拟环境**：每次开发前记得激活
3. **使用 pip3**：如果不想激活虚拟环境，使用 `pip3`
4. **检查安装**：安装后验证关键包是否成功

## 🔗 相关命令

```bash
# 查看已安装的包
pip list

# 查看特定包
pip show 包名

# 卸载包
pip uninstall 包名

# 更新包
pip install --upgrade 包名

# 导出依赖
pip freeze > requirements.txt
```
