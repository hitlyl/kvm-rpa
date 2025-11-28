"""图像预处理模块

提供图像处理功能，包括缩放、增强、去噪、ROI 裁剪等。
"""
from typing import Optional, Tuple
import cv2
import numpy as np
from loguru import logger


class ImageProcessor:
    """图像处理器
    
    提供各种图像预处理功能，优化后续的检测和识别效果。
    """
    
    def __init__(self):
        """初始化图像处理器"""
        pass
    
    def resize(
        self,
        frame: np.ndarray,
        target_size: Tuple[int, int],
        interpolation: int = cv2.INTER_LINEAR
    ) -> np.ndarray:
        """调整图像尺寸
        
        Args:
            frame: 输入图像
            target_size: 目标尺寸 (宽, 高)
            interpolation: 插值方法
            
        Returns:
            调整后的图像
        """
        if frame.shape[1] == target_size[0] and frame.shape[0] == target_size[1]:
            return frame
        
        return cv2.resize(frame, target_size, interpolation=interpolation)
    
    def enhance(
        self,
        frame: np.ndarray,
        contrast: float = 1.0,
        brightness: int = 0
    ) -> np.ndarray:
        """增强图像对比度和亮度
        
        Args:
            frame: 输入图像
            contrast: 对比度因子（1.0 表示不变）
            brightness: 亮度调整值（0 表示不变）
            
        Returns:
            增强后的图像
        """
        # 对比度和亮度调整公式: output = contrast * input + brightness
        enhanced = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
        return enhanced
    
    def denoise(
        self,
        frame: np.ndarray,
        method: str = "gaussian",
        **kwargs
    ) -> np.ndarray:
        """图像去噪
        
        Args:
            frame: 输入图像
            method: 去噪方法 ("gaussian", "bilateral", "median", "nlm")
            **kwargs: 方法特定参数
            
        Returns:
            去噪后的图像
        """
        if method == "gaussian":
            # 高斯滤波
            ksize = kwargs.get("ksize", (5, 5))
            sigma = kwargs.get("sigma", 0)
            return cv2.GaussianBlur(frame, ksize, sigma)
        
        elif method == "bilateral":
            # 双边滤波（保边去噪）
            d = kwargs.get("d", 9)
            sigma_color = kwargs.get("sigma_color", 75)
            sigma_space = kwargs.get("sigma_space", 75)
            return cv2.bilateralFilter(frame, d, sigma_color, sigma_space)
        
        elif method == "median":
            # 中值滤波
            ksize = kwargs.get("ksize", 5)
            return cv2.medianBlur(frame, ksize)
        
        elif method == "nlm":
            # 非局部均值去噪（较慢但效果好）
            h = kwargs.get("h", 10)
            template_window_size = kwargs.get("template_window_size", 7)
            search_window_size = kwargs.get("search_window_size", 21)
            return cv2.fastNlMeansDenoisingColored(
                frame, None, h, h,
                template_window_size, search_window_size
            )
        
        else:
            logger.warning(f"未知的去噪方法: {method}，返回原图")
            return frame
    
    def crop_roi(
        self,
        frame: np.ndarray,
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """裁剪 ROI（感兴趣区域）
        
        Args:
            frame: 输入图像
            roi: ROI 坐标 (x, y, width, height)
            
        Returns:
            裁剪后的图像
        """
        x, y, w, h = roi
        
        # 边界检查
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        return frame[y:y+h, x:x+w]
    
    def to_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """转换为灰度图
        
        Args:
            frame: 输入图像
            
        Returns:
            灰度图像
        """
        if len(frame.shape) == 2:
            # 已经是灰度图
            return frame
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def adaptive_threshold(
        self,
        frame: np.ndarray,
        method: int = cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        threshold_type: int = cv2.THRESH_BINARY,
        block_size: int = 11,
        c: int = 2
    ) -> np.ndarray:
        """自适应阈值二值化（适用于光照不均匀的场景）
        
        Args:
            frame: 输入图像（灰度图）
            method: 自适应方法
            threshold_type: 阈值类型
            block_size: 邻域大小（奇数）
            c: 常数偏移
            
        Returns:
            二值化图像
        """
        if len(frame.shape) == 3:
            frame = self.to_grayscale(frame)
        
        return cv2.adaptiveThreshold(
            frame, 255, method, threshold_type, block_size, c
        )
    
    def sharpen(self, frame: np.ndarray, amount: float = 1.0) -> np.ndarray:
        """图像锐化（增强边缘）
        
        Args:
            frame: 输入图像
            amount: 锐化强度（0-2）
            
        Returns:
            锐化后的图像
        """
        # 使用 Unsharp Mask 锐化
        blurred = cv2.GaussianBlur(frame, (0, 0), 3)
        sharpened = cv2.addWeighted(frame, 1.0 + amount, blurred, -amount, 0)
        return sharpened
    
    def adjust_gamma(self, frame: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Gamma 校正（调整整体亮度）
        
        Args:
            frame: 输入图像
            gamma: Gamma 值（< 1 变亮，> 1 变暗）
            
        Returns:
            校正后的图像
        """
        # 构建查找表
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in range(256)
        ]).astype("uint8")
        
        # 应用查找表
        return cv2.LUT(frame, table)
    
    def equalize_histogram(self, frame: np.ndarray) -> np.ndarray:
        """直方图均衡化（增强对比度）
        
        Args:
            frame: 输入图像
            
        Returns:
            均衡化后的图像
        """
        if len(frame.shape) == 2:
            # 灰度图直接均衡化
            return cv2.equalizeHist(frame)
        else:
            # 彩色图在 YCrCb 空间均衡化 Y 通道
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    
    def preprocess_for_ocr(
        self,
        frame: np.ndarray,
        denoise: bool = True,
        sharpen: bool = True,
        binarize: bool = False
    ) -> np.ndarray:
        """OCR 预处理流程
        
        Args:
            frame: 输入图像
            denoise: 是否去噪
            sharpen: 是否锐化
            binarize: 是否二值化
            
        Returns:
            预处理后的图像
        """
        processed = frame.copy()
        
        # 去噪
        if denoise:
            processed = self.denoise(processed, method="bilateral")
        
        # 锐化
        if sharpen:
            processed = self.sharpen(processed, amount=0.5)
        
        # 二值化（可选，某些场景下可提高识别率）
        if binarize:
            gray = self.to_grayscale(processed)
            processed = self.adaptive_threshold(gray)
        
        return processed
    
    def preprocess_for_detection(
        self,
        frame: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None,
        enhance_contrast: bool = False
    ) -> np.ndarray:
        """YOLO 检测预处理流程
        
        Args:
            frame: 输入图像
            target_size: 目标尺寸（如果提供则缩放）
            enhance_contrast: 是否增强对比度
            
        Returns:
            预处理后的图像
        """
        processed = frame.copy()
        
        # 缩放到目标尺寸
        if target_size:
            processed = self.resize(processed, target_size)
        
        # 增强对比度（可选）
        if enhance_contrast:
            processed = self.enhance(processed, contrast=1.2)
        
        return processed

