#!/bin/bash

# 安装 funasr 完整依赖脚本
# 用法: ./install_funasr.sh

set -e  # 遇到错误时停止

echo "🚀 开始安装 funasr 及其所有依赖..."
echo "=========================================="

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境，请先激活虚拟环境"
    echo "如果使用 venv: source .venv/bin/activate"
    exit 1
else
    echo "✅ 检测到虚拟环境: $VIRTUAL_ENV"
fi

# 更新 pip
echo "🔄 更新 pip..."
python -m pip install --upgrade pip setuptools wheel

# 安装 PyTorch (CPU版本，如果需要GPU请修改)
echo "🔧 安装 PyTorch..."
pip install torch torchaudio

# 安装基本依赖（按顺序）
echo "📦 安装基本依赖..."
BASIC_DEPS=(
    "librosa"
    "soundfile>=0.12.1"
    "sentencepiece"
    "tensorboardX"
    "umap-learn"
    "editdistance>=0.5.2"
    "hydra-core>=1.3.2"
    "jaconv"
    "jamo"
    "jieba"
    "torch_complex"
)

for dep in "${BASIC_DEPS[@]}"; do
    echo "正在安装: $dep"
    pip install "$dep" || echo "⚠️  $dep 安装可能有问题，继续..."
done

# 安装可能困难的依赖
echo "🔧 安装可能困难的依赖..."
DIFFICULT_DEPS=(
    "kaldiio>=2.17.0"
    "oss2"
    "pytorch-wpe"
)

for dep in "${DIFFICULT_DEPS[@]}"; do
    echo "正在安装: $dep"
    
    # 特殊处理某些包
    case $dep in
        kaldiio*)
            echo "安装 kaldiio 依赖..."
            pip install h5py
            pip install "$dep" || {
                echo "尝试从源码安装 kaldiio..."
                pip install "git+https://github.com/nttcslab-sp/kaldiio.git"
            }
            ;;
        oss2*)
            pip install "$dep" || echo "⚠️  oss2 安装失败，跳过..."
            ;;
        pytorch-wpe*)
            pip install "$dep" || {
                echo "尝试从 GitHub 安装 pytorch-wpe..."
                pip install "git+https://github.com/fgnt/pytorch_wpe.git"
            }
            ;;
        *)
            pip install "$dep" || echo "⚠️  $dep 安装失败"
            ;;
    esac
done

# 最后安装 funasr
echo "🎯 安装 funasr..."
pip install funasr==1.3.0

# 验证安装
echo "✅ 安装完成！开始验证..."
python -c "
import sys
print('Python 版本:', sys.version)

print('\n✅ 已安装的包:')
packages = [
    'torch', 'torchaudio', 'librosa', 'soundfile', 
    'sentencepiece', 'editdistance', 'hydra',
    'jieba', 'torch_complex', 'funasr'
]

for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        version = __import__(pkg.replace('-', '_')).__version__ if hasattr(__import__(pkg.replace('-', '_')), '__version__') else 'unknown'
        print(f'  {pkg:20} {version}')
    except ImportError:
        print(f'  ❌ {pkg:20} 未安装')
    except Exception as e:
        print(f'  ⚠️  {pkg:20} 导入错误: {str(e)[:50]}...')

print('\n🎉 funasr 测试导入...')
try:
    from funasr import AutoModel
    print('✅ AutoModel 导入成功！')
    
    # 尝试加载一个轻量模型
    print('尝试加载模型...')
    model = AutoModel(model='iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
    print('✅ 模型加载成功！')
except Exception as e:
    print(f'❌ 错误: {e}')
"

echo "=========================================="
echo "📝 安装总结:"
echo "1. 基本依赖已安装"
echo "2. funasr 已安装"
echo "3. 如有警告，部分功能可能受限"
echo ""
echo "🚀 现在可以运行你的应用了:"
echo "   streamlit run web_app.py"
echo "=========================================="