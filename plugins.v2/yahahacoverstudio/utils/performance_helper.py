"""
性能优化工具类
用于优化图像处理性能，减少CPU和内存占用
"""
import time
import threading
import os
from typing import Tuple, Optional, Callable, Any
from PIL import Image, ImageFilter
import numpy as np
from app.log import logger


_GC_LOCK = threading.Lock()
_LAST_FULL_GC = 0.0
_FULL_GC_INTERVAL = 300.0


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"开始执行: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if duration > 1.0:  # 只记录耗时超过1秒的操作
            logger.info(f"完成执行: {self.operation_name}, 耗时: {duration:.2f}秒")
        else:
            logger.debug(f"完成执行: {self.operation_name}, 耗时: {duration:.3f}秒")


class OptimizedImageProcessor:
    """优化的图像处理器"""

    @staticmethod
    def optimized_gaussian_blur(image: Image.Image, radius: int,
                               max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
        """
        优化的高斯模糊，对大图像先缩小再放大以提高性能

        Args:
            image: 输入图像
            radius: 模糊半径
            max_size: 处理时的最大尺寸

        Returns:
            模糊后的图像
        """
        with PerformanceMonitor(f"高斯模糊 (半径={radius})"):
            original_size = image.size

            # 如果图像很大，先缩小处理
            if original_size[0] > max_size[0] or original_size[1] > max_size[1]:
                # 计算缩放比例
                scale_x = max_size[0] / original_size[0]
                scale_y = max_size[1] / original_size[1]
                scale = min(scale_x, scale_y)

                # 缩小图像
                small_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                small_image = image.resize(small_size, Image.Resampling.LANCZOS)

                # 调整模糊半径
                adjusted_radius = max(1, int(radius * scale))

                # 对小图像应用模糊
                blurred_small = small_image.filter(ImageFilter.GaussianBlur(radius=adjusted_radius))

                # 放大回原始尺寸
                blurred_image = blurred_small.resize(original_size, Image.Resampling.LANCZOS)

                return blurred_image
            else:
                # 图像不大，直接处理
                return image.filter(ImageFilter.GaussianBlur(radius=radius))

    @staticmethod
    def optimized_color_analysis(image: Image.Image, num_colors: int = 6,
                                max_size: Tuple[int, int] = (200, 200)) -> list:
        """
        优化的颜色分析，使用缩小的图像进行分析

        Args:
            image: 输入图像
            num_colors: 需要提取的颜色数量
            max_size: 分析时的最大尺寸

        Returns:
            提取的颜色列表
        """
        with PerformanceMonitor("颜色分析"):
            # 缩小图像以加速分析
            analysis_image = image.copy()
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                analysis_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 转换为RGB数组
            img_array = np.array(analysis_image)
            pixels = img_array.reshape(-1, 3)

            # 使用简化的颜色提取
            return OptimizedImageProcessor._simple_color_extraction(pixels, num_colors)

    @staticmethod
    def _simple_color_extraction(pixels: np.ndarray, num_colors: int) -> list:
        """
        简化的颜色提取方法（不依赖sklearn）
        """
        # 量化颜色空间
        quantized = (pixels // 32) * 32  # 将颜色量化到32的倍数

        # 统计颜色频率
        unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)

        # 按频率排序
        sorted_indices = np.argsort(counts)[::-1]

        # 返回最常见的颜色
        top_colors = unique_colors[sorted_indices[:num_colors]]
        return [tuple(color) for color in top_colors]


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total_steps: int, operation_name: str = "操作"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self._lock = threading.Lock()

    def update(self, step_name: str = ""):
        """更新进度"""
        with self._lock:
            self.current_step += 1
            current_time = time.time()

            # 每5秒或完成时报告一次进度
            if (current_time - self.last_report_time > 5.0 or
                self.current_step == self.total_steps):

                progress = (self.current_step / self.total_steps) * 100
                elapsed = current_time - self.start_time

                if self.current_step < self.total_steps:
                    eta = (elapsed / self.current_step) * (self.total_steps - self.current_step)
                    logger.info(f"{self.operation_name}进度: {progress:.1f}% "
                              f"({self.current_step}/{self.total_steps}) "
                              f"预计剩余: {eta:.1f}秒 - {step_name}")
                else:
                    logger.info(f"{self.operation_name}完成: 100% "
                              f"总耗时: {elapsed:.1f}秒")

                self.last_report_time = current_time

    def is_complete(self) -> bool:
        """检查是否完成"""
        return self.current_step >= self.total_steps


def memory_efficient_operation(func):
    """
    装饰器：内存高效操作
    避免在每张封面生成前后强制全量垃圾回收。

    Pillow 渲染会短时间创建不少临时对象，但 Python 的全量 gc.collect()
    在 MoviePilot 进程对象较多时可能阻塞几十秒，表现为“生成卡死”。这里
    只做年轻代轻量回收；全量回收默认关闭，可通过 MCG_FORCE_FULL_GC=1
    开启，并且最多每 5 分钟执行一次。
    """
    def wrapper(*args, **kwargs):
        import gc

        try:
            gc.collect(0)
        except Exception:
            pass

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            try:
                gc.collect(0)
            except Exception:
                pass

            if os.environ.get("MCG_FORCE_FULL_GC") == "1":
                global _LAST_FULL_GC
                now = time.time()
                if now - _LAST_FULL_GC >= _FULL_GC_INTERVAL:
                    with _GC_LOCK:
                        now = time.time()
                        if now - _LAST_FULL_GC >= _FULL_GC_INTERVAL:
                            gc_start = time.time()
                            gc.collect()
                            _LAST_FULL_GC = time.time()
                            duration = _LAST_FULL_GC - gc_start
                            if duration > 1:
                                logger.info("YahahaCoverStudio 全量 GC 完成，耗时 %.2fs", duration)

    return wrapper
