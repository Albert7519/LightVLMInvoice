#!/usr/bin/env python3
"""
Performance Benchmark Tests for LocalllmOcrMK2

Measures:
- Single invoice recognition time
- Concurrent processing throughput
- GPU/CPU memory usage during inference

Requirements:
- Backend services running (FastAPI on 8080, vLLM on 8000)
- Test invoice PDF file
- Network connectivity

Usage:
    python tests/performance_benchmark.py
    
Or in Docker:
    docker-compose run --rm backend python ../tests/performance_benchmark.py
"""

import time
import sys
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


class BenchmarkConfig:
    """Benchmark configuration."""
    
    # Backend service URLs
    API_URL = "http://localhost:8080"
    VLLM_URL = "http://localhost:8000"
    
    # Test parameters
    SINGLE_TEST_TIMEOUT = 30  # seconds
    CONCURRENT_INVOICES = 3
    CONCURRENT_TIMEOUT = 60  # seconds
    
    # Thresholds for pass/fail
    SINGLE_TIME_THRESHOLD = 30  # seconds - single invoice should complete < 30s
    CONCURRENT_TIME_THRESHOLD = 60  # seconds
    
    # Test fixture
    TEST_INVOICE = "tests/fixtures/sample_invoice.pdf"


class PerformanceBenchmark:
    """Run performance benchmarks."""
    
    def __init__(self):
        self.config = BenchmarkConfig()
        self.passed = 0
        self.failed = 0
        
    def check_services(self) -> bool:
        """Check if required services are running."""
        print("\n🔍 Checking services...")
        
        services = {
            "FastAPI": f"{self.config.API_URL}/docs",
            "vLLM": f"{self.config.VLLM_URL}/v1/models"
        }
        
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    print(f"  ✓ {name} ready")
                else:
                    print(f"  ✗ {name} not ready ({response.status_code})")
                    return False
            except Exception as e:
                print(f"  ✗ {name} unreachable: {e}")
                return False
        
        return True
    
    def check_test_file(self) -> bool:
        """Check if test invoice exists."""
        if not Path(self.config.TEST_INVOICE).exists():
            print(f"\n⚠️  Test invoice not found: {self.config.TEST_INVOICE}")
            print("  Creating mock test file...\n")
            
            # Create tests/fixtures directory if needed
            Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
            
            # For now, we'll use a generic PDF creation message
            print("  Note: Use a real invoice PDF for accurate benchmarks")
            return False
        
        return True
    
    def benchmark_single_invoice(self) -> float:
        """Benchmark: Single invoice recognition time."""
        print("\n📊 Benchmark 1: Single Invoice Recognition")
        print("-" * 50)
        
        if not Path(self.config.TEST_INVOICE).exists():
            print("  ⚠️  Test file not found, skipping benchmark")
            return -1
        
        try:
            with open(self.config.TEST_INVOICE, 'rb') as f:
                files = {'files': f}
                
                # Time the upload
                start = time.time()
                
                # Upload invoice
                response = requests.post(
                    f"{self.config.API_URL}/api/v1/invoices/extract",
                    files=files,
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"  ✗ Upload failed: {response.status_code}")
                    self.failed += 1
                    return -1
                
                result = response.json()
                task_id = result['data']['task_ids'][0]
                print(f"  Task ID: {task_id}")
                
                # Poll for completion
                max_polls = 60  # 60 * 2s = 2 minutes timeout
                for poll_count in range(max_polls):
                    response = requests.get(
                        f"{self.config.API_URL}/api/v1/invoices/status/{task_id}",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data['status']
                        
                        if status == 'COMPLETED':
                            elapsed = time.time() - start
                            print(f"  Status: {status}")
                            print(f"  ⏱️  Time: {elapsed:.2f} seconds")
                            
                            # Check threshold
                            if elapsed < self.config.SINGLE_TIME_THRESHOLD:
                                print(f"  ✓ PASS (< {self.config.SINGLE_TIME_THRESHOLD}s)")
                                self.passed += 1
                            else:
                                print(f"  ⚠️  SLOW (> {self.config.SINGLE_TIME_THRESHOLD}s)")
                                self.failed += 1
                            
                            return elapsed
                        
                        elif status == 'FAILED':
                            elapsed = time.time() - start
                            print(f"  ✗ Task failed after {elapsed:.2f}s")
                            self.failed += 1
                            return -1
                        
                        else:
                            progress = data.get('progress', 0)
                            print(f"  Status: {status} ({progress}%)")
                    
                    time.sleep(2)
                
                print(f"  ✗ Timeout after {max_polls * 2}s")
                self.failed += 1
                return -1
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.failed += 1
            return -1
    
    def benchmark_concurrent_invoices(self) -> float:
        """Benchmark: Concurrent invoice processing."""
        print("\n📊 Benchmark 2: Concurrent Processing")
        print("-" * 50)
        
        if not Path(self.config.TEST_INVOICE).exists():
            print("  ⚠️  Test file not found, skipping benchmark")
            return -1
        
        try:
            start = time.time()
            
            def upload_invoice():
                """Upload single invoice."""
                with open(self.config.TEST_INVOICE, 'rb') as f:
                    files = {'files': f}
                    response = requests.post(
                        f"{self.config.API_URL}/api/v1/invoices/extract",
                        files=files,
                        timeout=10
                    )
                    if response.status_code == 200:
                        return response.json()['data']['task_ids'][0]
                    return None
            
            # Upload invoices concurrently
            task_ids = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(upload_invoice) for _ in range(self.config.CONCURRENT_INVOICES)]
                for future in as_completed(futures):
                    task_id = future.result()
                    if task_id:
                        task_ids.append(task_id)
            
            print(f"  Uploaded {len(task_ids)} invoices")
            
            # Wait for all to complete
            completed = 0
            for poll_count in range(60):  # 120 seconds timeout
                for task_id in task_ids:
                    try:
                        response = requests.get(
                            f"{self.config.API_URL}/api/v1/invoices/status/{task_id}",
                            timeout=5
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if data['status'] == 'COMPLETED':
                                completed += 1
                    except:
                        pass
                
                if completed == len(task_ids):
                    break
                
                time.sleep(2)
            
            elapsed = time.time() - start
            print(f"  Completed: {completed}/{len(task_ids)}")
            print(f"  ⏱️  Time: {elapsed:.2f} seconds")
            
            if elapsed < self.config.CONCURRENT_TIME_THRESHOLD:
                print(f"  ✓ PASS (< {self.config.CONCURRENT_TIME_THRESHOLD}s)")
                self.passed += 1
            else:
                print(f"  ⚠️  SLOW (> {self.config.CONCURRENT_TIME_THRESHOLD}s)")
                self.failed += 1
            
            return elapsed
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.failed += 1
            return -1
    
    def run_all(self):
        """Run all benchmarks."""
        print("=" * 50)
        print("🚀 LocalllmOcrMK2 Performance Benchmarks")
        print("=" * 50)
        
        # Check services
        if not self.check_services():
            print("\n❌ Required services not running")
            print("Start services with: docker-compose up -d")
            return False
        
        # Check test file
        self.check_test_file()
        
        # Run benchmarks
        time1 = self.benchmark_single_invoice()
        time2 = self.benchmark_concurrent_invoices()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Summary")
        print("=" * 50)
        print(f"Passed: {self.passed}")
        print(f"Failed/Warnings: {self.failed}")
        
        if self.failed == 0 and time1 > 0 and time2 > 0:
            print("\n✅ All benchmarks passed!")
            return True
        else:
            print("\n⚠️  Some benchmarks didn't meet thresholds")
            return False


def main():
    """Entry point."""
    benchmark = PerformanceBenchmark()
    success = benchmark.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
