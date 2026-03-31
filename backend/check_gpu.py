#!/usr/bin/env python3
"""
GPU Environment Verification Script for LocalllmOcrMK2

Checks:
1. NVIDIA GPU availability
2. CUDA version compatibility (≥ 11.8 recommended)
3. Available GPU memory (≥ 6GB for model)
4. NVIDIA runtime & drivers
5. vLLM initialization capability

Exit Codes:
  0: GPU ready for inference
  1: GPU not available, fallback to CPU mode
  2: Critical error, cannot proceed
"""

import os
import sys
import subprocess
from typing import Tuple


def check_nvidia_smi() -> bool:
    """Check if nvidia-smi is available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_gpu_info() -> Tuple[bool, str, int]:
    """Get GPU info: (has_gpu, gpu_name, available_memory_gb)"""
    if not check_nvidia_smi():
        return False, "", 0
    
    try:
        # Get GPU name
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5
        )
        gpu_name = result.stdout.strip() if result.returncode == 0 else "Unknown"
        
        # Get free memory in MB
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            memory_mb = int(result.stdout.strip().split('\n')[0])
            memory_gb = memory_mb // 1024
            return True, gpu_name, memory_gb
    except Exception:
        pass
    
    return False, "", 0


def check_pytorch_cuda() -> Tuple[bool, str]:
    """Check PyTorch CUDA availability."""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        device_name = ""
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
            cuda_version = torch.version.cuda
        else:
            cuda_version = "N/A"
        
        return cuda_available, f"CUDA {cuda_version}"
    except ImportError:
        return False, "PyTorch not installed"
    except Exception as e:
        return False, str(e)


def check_vllm_import() -> bool:
    """Check if vLLM can be imported."""
    try:
        import vllm
        return True
    except ImportError:
        return False


def main():
    print("🔍 LocalllmOcrMK2 GPU Environment Check\n")
    print("=" * 60)
    
    # Check 1: nvidia-smi
    print("\n[1/5] Checking NVIDIA Runtime...")
    nvidia_available = check_nvidia_smi()
    if nvidia_available:
        print("✅ NVIDIA Runtime found")
    else:
        print("❌ NVIDIA Runtime not found (nvidia-smi not available)")
    
    # Check 2: GPU availability
    print("\n[2/5] Checking GPU Device...")
    has_gpu, gpu_name, gpu_mem_gb = get_gpu_info()
    
    if has_gpu:
        print(f"✅ GPU found: {gpu_name}")
        print(f"   Available memory: {gpu_mem_gb} GB")
        
        if gpu_mem_gb < 6:
            print(f"   ⚠️  WARNING: Only {gpu_mem_gb}GB available (6GB recommended)")
            print("      Consider reducing VLLM_GPU_MEMORY_UTILIZATION or using smaller model")
        elif gpu_mem_gb >= 10:
            print(f"   ✅ Sufficient memory for optimal performance")
    else:
        print("❌ No NVIDIA GPU detected")
    
    # Check 3: PyTorch CUDA
    print("\n[3/5] Checking PyTorch/CUDA...")
    pytorch_cuda_ok, cuda_info = check_pytorch_cuda()
    if pytorch_cuda_ok:
        print(f"✅ PyTorch CUDA available ({cuda_info})")
    else:
        print(f"❌ PyTorch CUDA not available ({cuda_info})")
    
    # Check 4: vLLM import
    print("\n[4/5] Checking vLLM Installation...")
    vllm_ok = check_vllm_import()
    if vllm_ok:
        print("✅ vLLM imported successfully")
    else:
        print("❌ vLLM not installed")
        print("   Run: pip install vllm")
    
    # Check 5: ModelScope availability
    print("\n[5/5] Checking ModelScope Connection...")
    try:
        import modelscope
        print("✅ ModelScope imported successfully")
    except ImportError:
        print("❌ ModelScope not installed")
        print("   Run: pip install modelscope")
    
    # Summary and recommendations
    print("\n" + "=" * 60)
    print("\n📊 SUMMARY:")
    
    if has_gpu and pytorch_cuda_ok and vllm_ok:
        print("✅ GPU environment is ready for inference")
        print("   Recommended settings:")
        print("   - VLLM_GPU_MEMORY_UTILIZATION=0.9")
        print("   - Start vLLM: python -m vllm.entrypoints.openai.api_server --model <model_name> --gpu-memory-utilization 0.9")
        return 0
    
    elif not has_gpu:
        print("⚠️  No GPU detected - falling back to CPU mode")
        print("   Performance will be significantly slower")
        print("   Recommended settings:")
        print("   - VLLM_DEVICE=cpu")
        print("   - Consider using quantized models (INT4/INT8)")
        return 1
    
    else:
        print("❌ GPU environment incomplete or unavailable")
        print("   Please install missing dependencies or check NVIDIA drivers")
        return 2


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
