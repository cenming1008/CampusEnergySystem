# 虚拟环境问题修复指南

## 🔍 问题诊断

你的虚拟环境显示 `(venv)` 已激活，但 `pip` 命令找不到。检查后发现：

**问题原因**：虚拟环境中的脚本包含错误的绝对路径
```
#!/www/wwwroot/MineEnergySystem/venv/bin/python3
```

这说明虚拟环境是从其他位置复制或移动过来的。虚拟环境的脚本（pip、python等）包含绝对路径，当项目路径改变时就会失效。

## ✅ 解决方案

### 方法1：使用修复脚本（推荐）

```bash
cd /Users/todo/MineEnergySystem
./scripts/fix_venv.sh
```

这个脚本会：
1. 备份旧虚拟环境
2. 创建新的虚拟环境
3. 安装所有依赖

### 方法2：手动重新创建

```bash
# 1. 进入项目目录
cd /Users/todo/MineEnergySystem

# 2. 备份旧虚拟环境（可选）
mv venv venv.backup

# 3. 删除旧虚拟环境
rm -rf venv

# 4. 创建新虚拟环境
python3 -m venv venv

# 5. 激活虚拟环境
source venv/bin/activate

# 6. 升级 pip
python -m pip install --upgrade pip

# 7. 安装依赖
python -m pip install -r requirements.txt
```

### 方法3：直接使用系统 Python（临时方案）

如果暂时不想修复虚拟环境，可以直接使用系统 Python：

```bash
# 不使用虚拟环境，直接安装到用户目录
python3 -m pip install --user -r requirements.txt
```

## 🔧 验证修复

修复后，验证虚拟环境：

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查 Python
python --version
# 应该显示：Python 3.9.6 或类似

# 检查 pip
python -m pip --version
# 应该显示 pip 版本

# 检查路径
which python
# 应该显示：/Users/todo/MineEnergySystem/venv/bin/python

which pip
# 应该显示：/Users/todo/MineEnergySystem/venv/bin/pip
```

## 📝 为什么会出现这个问题？

虚拟环境创建时，会在脚本中写入 Python 解释器的绝对路径。如果：
- 项目被移动
- 虚拟环境被复制
- 在不同机器间同步

这些脚本中的路径就会失效。

## 💡 预防措施

1. **不要复制虚拟环境**：总是重新创建
2. **使用相对路径**：如果可能，使用 `python -m venv --relocatable venv`（已废弃，不推荐）
3. **使用 .gitignore**：确保 `venv/` 在 `.gitignore` 中
4. **文档化**：在 README 中说明如何创建虚拟环境

## 🚀 快速修复命令

```bash
cd /Users/todo/MineEnergySystem && \
rm -rf venv && \
python3 -m venv venv && \
source venv/bin/activate && \
python -m pip install --upgrade pip && \
python -m pip install -r requirements.txt
```

## ✅ 修复后

修复完成后，你应该能够：

```bash
# 激活虚拟环境
source venv/bin/activate

# 使用 pip
pip install 包名

# 使用 python
python run.py

# 退出虚拟环境
deactivate
```
