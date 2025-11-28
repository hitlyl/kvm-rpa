"""YOLO 目标检测模块

支持Sophon硬件加速和模拟模式。
优先使用Sophon BModel,如果不可用则回退到模拟模式。
"""
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from loguru import logger

# 尝试导入Sophon YOLO检测器
try:
    from detection.yolo_sophon import SophonYOLODetector
    SOPHON_AVAILABLE = True
except ImportError:
    SOPHON_AVAILABLE = False
    logger.debug("Sophon YOLO检测器不可用,将使用模拟模式")


class YOLODetector:
    """YOLO 检测器
    
    支持Sophon硬件加速(BModel)和模拟模式。
    自动检测并选择可用的后端。
    
    Attributes:
        model_path: 模型文件路径(BModel或其他)
        conf_threshold: 置信度阈值
        iou_threshold: NMS IOU 阈值
        device: 推理设备(Sophon设备ID或其他)
        img_size: 输入图像尺寸
        backend: 使用的后端('sophon'或'mock')
        mock_mode: 是否为模拟模式
    """
    
    def __init__(
        self,
        model_path: str = "models/yolov8n.pt",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "cpu",
        img_size: int = 640,
        backend: str = "auto",
        dev_id: int = 0
    ):
        """初始化 YOLO 检测器
        
        Args:
            model_path: 模型文件路径(BModel文件或其他)
            conf_threshold: 置信度阈值
            iou_threshold: NMS IOU 阈值
            device: 推理设备
            img_size: 输入图像尺寸
            backend: 后端选择('auto','sophon','mock')
            dev_id: Sophon设备ID
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.img_size = img_size
        self.dev_id = dev_id
        self.backend = backend
        self.mock_mode = True
        
        # 实际检测器实例
        self.detector = None
        
        # 模拟的类别名称
        self.class_names = ['button', 'input', 'checkbox', 'dropdown', 'text', 'icon']
        
        # 加载模型
        self.model = None
        self._load_model()
        
        # 统计信息
        self.stats = {
            'total_inferences': 0,
            'total_detections': 0,
            'avg_inference_time': 0.0,
            'errors': 0
        }
    
    def _load_model(self) -> bool:
        """加载 YOLO 模型
        
        Returns:
            bool: 是否加载成功
        """
        # 确定使用的后端
        use_sophon = False
        
        if self.backend == "sophon":
            use_sophon = True
        elif self.backend == "mock":
            use_sophon = False
        elif self.backend == "auto":
            # 自动检测:如果模型路径是.bmodel且Sophon可用,则使用Sophon
            if SOPHON_AVAILABLE and self.model_path.endswith('.bmodel') and Path(self.model_path).exists():
                use_sophon = True
        
        # 尝试使用Sophon后端
        if use_sophon:
            try:
                logger.info(f"尝试使用Sophon后端加载BModel: {self.model_path}")
                self.detector = SophonYOLODetector(
                    bmodel_path=self.model_path,
                    dev_id=self.dev_id,
                    conf_threshold=self.conf_threshold,
                    nms_threshold=self.iou_threshold
                )
                self.mock_mode = False
                self.backend = "sophon"
                logger.success(f"YOLO检测器初始化成功(Sophon后端)")
                return True
            except Exception as e:
                logger.warning(f"Sophon后端初始化失败: {e}, 回退到模拟模式")
        
        # 回退到模拟模式
        logger.info(f"初始化 YOLO 检测器(模拟模式)")
        logger.warning("当前使用模拟模式,不会加载真实模型")
        logger.info(f"配置 - 置信度阈值: {self.conf_threshold}, IOU阈值: {self.iou_threshold}")
        
        self.mock_mode = True
        self.backend = "mock"
        self.model = "mock_model"
        logger.success("YOLO 检测器初始化成功(模拟模式)")
        return True
    
    def detect(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """检测图像中的目标
        
        Args:
            frame: 输入图像 (BGR 格式或任意格式)
            conf_threshold: 置信度阈值(可选,覆盖默认值)
            iou_threshold: IOU 阈值(可选,覆盖默认值)
            
        Returns:
            检测结果列表,每个结果包含:
            - label: 类别名称
            - bbox: 边界框 [x1, y1, x2, y2]
            - conf: 置信度
            - center: 中心点 [cx, cy]
            - class_id: 类别 ID
        """
        # 使用Sophon后端
        if not self.mock_mode and self.detector is not None:
            try:
                return self.detector.detect(frame, conf_threshold, iou_threshold)
            except Exception as e:
                logger.error(f"Sophon检测失败: {e}, 回退到模拟模式")
                # 继续执行模拟模式
        
        # 模拟模式
        if self.model is None and self.detector is None:
            logger.error("模型未加载")
            return []
        
        start_time = time.time()
        
        try:
            # 使用配置的阈值或参数传入的阈值
            conf = conf_threshold if conf_threshold is not None else self.conf_threshold
            
            # 获取图像尺寸
            if isinstance(frame, np.ndarray):
                height, width = frame.shape[:2]
            else:
                # 如果不是 numpy 数组，使用默认尺寸
                height, width = 720, 1280
            
            # 生成模拟检测结果（2-5 个随机检测框）
            detections = []
            num_detections = random.randint(2, 5)
            
            for i in range(num_detections):
                # 随机生成边界框
                x1 = random.randint(0, width - 200)
                y1 = random.randint(0, height - 100)
                w = random.randint(80, 200)
                h = random.randint(40, 100)
                x2 = min(x1 + w, width)
                y2 = min(y1 + h, height)
                
                # 随机生成置信度（高于阈值）
                confidence = random.uniform(conf, 0.95)
                
                # 随机选择类别
                class_id = random.randint(0, len(self.class_names) - 1)
                label = self.class_names[class_id]
                
                # 计算中心点
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                
                detection = {
                    'label': label,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'conf': float(confidence),
                    'center': [float(cx), float(cy)],
                    'class_id': class_id
                }
                
                detections.append(detection)
            
            # 更新统计信息
            inference_time = time.time() - start_time
            self.stats['total_inferences'] += 1
            self.stats['total_detections'] += len(detections)
            
            # 更新平均推理时间（移动平均）
            alpha = 0.1
            self.stats['avg_inference_time'] = (
                alpha * inference_time +
                (1 - alpha) * self.stats['avg_inference_time']
            )
            
            logger.debug(
                f"YOLO 检测完成（模拟） - 耗时: {inference_time:.3f}s, "
                f"检测数: {len(detections)}"
            )
            
            return detections
            
        except Exception as e:
            logger.exception(f"YOLO 检测失败: {e}")
            self.stats['errors'] += 1
            return []
    
    def reload_model(self, new_model_path: str) -> bool:
        """热更新模型
        
        Args:
            new_model_path: 新模型文件路径
            
        Returns:
            bool: 是否更新成功
        """
        logger.info(f"热更新模型: {new_model_path}")
        
        # 如果使用Sophon后端
        if not self.mock_mode and self.detector is not None:
            try:
                return self.detector.reload_model(new_model_path)
            except Exception as e:
                logger.error(f"Sophon模型热更新失败: {e}")
                return False
        
        # 模拟模式
        old_model_path = self.model_path
        self.model_path = new_model_path
        logger.success(f"模型热更新成功(模拟): {new_model_path}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        # 如果使用Sophon后端,返回Sophon统计信息
        if not self.mock_mode and self.detector is not None:
            try:
                stats = self.detector.get_stats()
                stats['backend'] = 'sophon'
                stats['mock_mode'] = False
                return stats
            except:
                pass
        
        # 模拟模式统计信息
        stats = self.stats.copy()
        stats['backend'] = 'mock'
        stats['mock_mode'] = True
        return stats
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        color: tuple = (0, 255, 0),
        thickness: int = 2,
        show_label: bool = True,
        show_conf: bool = True
    ) -> np.ndarray:
        """在图像上绘制检测框（用于可视化，模拟版本）
        
        Args:
            frame: 输入图像
            detections: 检测结果列表
            color: 边界框颜色 (B, G, R)
            thickness: 线条粗细
            show_label: 是否显示标签
            show_conf: 是否显示置信度
            
        Returns:
            绘制后的图像（模拟版本返回原图）
        """
        try:
            import cv2
            
            result_frame = frame.copy()
            
            for det in detections:
                bbox = det['bbox']
                x1, y1, x2, y2 = map(int, bbox)
                
                # 绘制边界框
                cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, thickness)
                
                # 绘制标签和置信度
                if show_label or show_conf:
                    label_parts = []
                    if show_label:
                        label_parts.append(det['label'])
                    if show_conf:
                        label_parts.append(f"{det['conf']:.2f}")
                    
                    label_text = " ".join(label_parts)
                    
                    # 计算文本大小
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.5
                    font_thickness = 1
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label_text, font, font_scale, font_thickness
                    )
                    
                    # 绘制文本背景
                    cv2.rectangle(
                        result_frame,
                        (x1, y1 - text_height - baseline - 5),
                        (x1 + text_width, y1),
                        color,
                        -1
                    )
                    
                    # 绘制文本
                    cv2.putText(
                        result_frame,
                        label_text,
                        (x1, y1 - baseline - 2),
                        font,
                        font_scale,
                        (255, 255, 255),
                        font_thickness
                    )
                
                # 绘制中心点
                center = det['center']
                cx, cy = map(int, center)
                cv2.circle(result_frame, (cx, cy), 3, color, -1)
            
            return result_frame
        except ImportError:
            logger.warning("opencv-python 未安装，跳过绘制检测框")
            return frame

