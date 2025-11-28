"""OCR 识别模块

支持PP-OCR Sophon硬件加速和模拟模式。
优先使用PP-OCR Sophon引擎,如果不可用则回退到模拟模式。
"""
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from loguru import logger

# 尝试导入PP-OCR Sophon引擎
try:
    from ocr.ppocr_sophon import PPOCRSophon
    PPOCR_SOPHON_AVAILABLE = True
except ImportError:
    PPOCR_SOPHON_AVAILABLE = False
    logger.debug("PP-OCR Sophon引擎不可用,将使用模拟模式")


class OCREngine:
    """OCR 识别引擎
    
    支持PP-OCR Sophon硬件加速和模拟模式。
    自动检测并选择可用的后端。
    
    Attributes:
        lang: 语言列表
        conf_threshold: 最小置信度阈值
        use_angle_cls: 是否使用方向分类器
        use_gpu: 是否使用 GPU
        backend: 使用的后端('sophon'或'mock')
        mock_mode: 是否为模拟模式
        det_model: 检测模型路径
        rec_model: 识别模型路径
        cls_model: 分类模型路径
        char_dict_path: 字符字典路径
        dev_id: Sophon设备ID
    """
    
    def __init__(
        self,
        lang: List[str] = None,
        conf_threshold: float = 0.5,
        use_angle_cls: bool = False,
        use_gpu: bool = False,
        backend: str = "auto",
        det_model: str = None,
        rec_model: str = None,
        cls_model: str = None,
        char_dict_path: str = None,
        dev_id: int = 0
    ):
        """初始化 OCR 引擎
        
        Args:
            lang: 语言列表,如 ['ch', 'en']
            conf_threshold: 最小置信度阈值
            use_angle_cls: 是否使用方向分类器
            use_gpu: 是否使用 GPU
            backend: 后端选择('auto','sophon','mock')
            det_model: 检测模型BModel路径
            rec_model: 识别模型BModel路径
            cls_model: 分类模型BModel路径
            char_dict_path: 字符字典路径(ppocr_keys_v1.txt)
            dev_id: Sophon设备ID
        """
        self.lang = lang or ['ch', 'en']
        self.conf_threshold = conf_threshold
        self.use_angle_cls = use_angle_cls
        self.use_gpu = use_gpu
        self.backend = backend
        self.det_model = det_model
        self.rec_model = rec_model
        self.cls_model = cls_model
        self.char_dict_path = char_dict_path or "models/ppocr_keys_v1.txt"
        self.dev_id = dev_id
        self.mock_mode = True
        
        # 实际OCR引擎实例
        self.ocr_engine = None
        
        # 模拟的文本样本
        self.sample_texts = [
            '确认', '取消', '下一步', '上一步', '提交', '保存',
            'OK', 'Cancel', 'Next', 'Previous', 'Submit', 'Save',
            '登录', '注册', '搜索', '设置', '帮助',
            'Login', 'Register', 'Search', 'Settings', 'Help'
        ]
        
        # OCR 引擎
        self.ocr = None
        self._init_engine()
        
        # 统计信息
        self.stats = {
            'total_recognitions': 0,
            'total_texts': 0,
            'avg_recognition_time': 0.0,
            'errors': 0
        }
    
    def _init_engine(self) -> bool:
        """初始化 OCR 引擎
        
        Returns:
            bool: 是否初始化成功
        """
        # 确定使用的后端
        use_sophon = False
        
        if self.backend == "sophon":
            use_sophon = True
        elif self.backend == "mock":
            use_sophon = False
        elif self.backend == "auto":
            # 自动检测:如果指定了模型路径且PP-OCR Sophon可用,则使用Sophon
            if PPOCR_SOPHON_AVAILABLE and self.det_model and self.rec_model:
                if Path(self.det_model).exists() and Path(self.rec_model).exists():
                    use_sophon = True
        
        # 尝试使用Sophon后端
        if use_sophon:
            try:
                logger.info(f"尝试使用PP-OCR Sophon后端")
                logger.info(f"检测模型: {self.det_model}")
                logger.info(f"识别模型: {self.rec_model}")
                logger.info(f"字符字典: {self.char_dict_path}")
                self.ocr_engine = PPOCRSophon(
                    det_model=self.det_model,
                    rec_model=self.rec_model,
                    cls_model=self.cls_model,
                    char_dict_path=self.char_dict_path,
                    use_angle_cls=self.use_angle_cls,
                    rec_thresh=self.conf_threshold,
                    dev_id=self.dev_id
                )
                self.mock_mode = False
                self.backend = "sophon"
                logger.success(f"OCR引擎初始化成功(PP-OCR Sophon后端)")
                return True
            except Exception as e:
                logger.warning(f"PP-OCR Sophon后端初始化失败: {e}, 回退到模拟模式")
        
        # 回退到模拟模式
        logger.info(f"初始化 OCR 引擎(模拟模式)")
        logger.warning("当前使用模拟模式,不会加载真实OCR引擎")
        logger.info(f"配置 - 语言: {self.lang}, 置信度阈值: {self.conf_threshold}")
        
        self.mock_mode = True
        self.backend = "mock"
        self.ocr = "mock_ocr"
        logger.success("OCR 引擎初始化成功(模拟模式)")
        return True
    
    def recognize(
        self,
        frame_or_roi: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """识别图像中的文字
        
        Args:
            frame_or_roi: 输入图像或 ROI (BGR格式)
            conf_threshold: 置信度阈值(可选,覆盖默认值)
            
        Returns:
            识别结果列表,每个结果包含:
            - text: 识别的文本
            - conf: 置信度
            - bbox: 文本边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - bbox_rect: 矩形边界框 [x, y, w, h]
        """
        # 使用PP-OCR Sophon后端
        if not self.mock_mode and self.ocr_engine is not None:
            try:
                return self.ocr_engine.recognize(frame_or_roi, conf_threshold)
            except Exception as e:
                logger.error(f"PP-OCR识别失败: {e}, 回退到模拟模式")
                # 继续执行模拟模式
        
        # 模拟模式
        if self.ocr is None and self.ocr_engine is None:
            logger.error("OCR 引擎未初始化")
            return []
        
        start_time = time.time()
        
        try:
            # 使用配置的阈值或参数传入的阈值
            conf = conf_threshold if conf_threshold is not None else self.conf_threshold
            
            # 获取图像尺寸
            if isinstance(frame_or_roi, np.ndarray):
                height, width = frame_or_roi.shape[:2]
            else:
                # 如果不是 numpy 数组，使用默认尺寸
                height, width = 720, 1280
            
            # 生成模拟识别结果（1-4 个随机文本）
            recognitions = []
            num_texts = random.randint(1, 4)
            
            for i in range(num_texts):
                # 随机选择文本
                text = random.choice(self.sample_texts)
                
                # 随机生成边界框（四边形）
                x = random.randint(0, width - 150)
                y = random.randint(0, height - 50)
                w = random.randint(60, 150)
                h = random.randint(20, 50)
                
                # 四边形边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                bbox = [
                    [float(x), float(y)],
                    [float(x + w), float(y)],
                    [float(x + w), float(y + h)],
                    [float(x), float(y + h)]
                ]
                
                # 随机生成置信度（高于阈值）
                confidence = random.uniform(conf, 0.98)
                
                recognition = {
                    'text': text,
                    'conf': float(confidence),
                    'bbox': bbox,
                    'bbox_rect': [x, y, w, h]
                }
                
                recognitions.append(recognition)
            
            # 更新统计信息
            recognition_time = time.time() - start_time
            self.stats['total_recognitions'] += 1
            self.stats['total_texts'] += len(recognitions)
            
            # 更新平均识别时间（移动平均）
            alpha = 0.1
            self.stats['avg_recognition_time'] = (
                alpha * recognition_time +
                (1 - alpha) * self.stats['avg_recognition_time']
            )
            
            logger.debug(
                f"OCR 识别完成（模拟） - 耗时: {recognition_time:.3f}s, "
                f"识别数: {len(recognitions)}"
            )
            
            return recognitions
            
        except Exception as e:
            logger.exception(f"OCR 识别失败: {e}")
            self.stats['errors'] += 1
            return []
    
    def recognize_region(
        self,
        frame: np.ndarray,
        bbox: List[int],
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """识别图像中指定区域的文字
        
        Args:
            frame: 完整图像
            bbox: 区域边界框 [x, y, w, h]
            conf_threshold: 置信度阈值
            
        Returns:
            识别结果列表
        """
        x, y, w, h = bbox
        
        # 边界检查
        height, width = frame.shape[:2]
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        # 裁剪 ROI
        roi = frame[y:y+h, x:x+w]
        
        # 识别 ROI
        recognitions = self.recognize(roi, conf_threshold)
        
        # 调整坐标到原图
        for rec in recognitions:
            # 调整多边形边界框
            rec['bbox'] = [[pt[0] + x, pt[1] + y] for pt in rec['bbox']]
            # 调整矩形边界框
            rec['bbox_rect'][0] += x
            rec['bbox_rect'][1] += y
        
        return recognitions
    
    def find_text(
        self,
        frame: np.ndarray,
        target_text: str,
        match_mode: str = "contains",
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """查找包含特定文本的识别结果
        
        Args:
            frame: 输入图像
            target_text: 目标文本
            match_mode: 匹配模式 ("contains", "equals", "startswith", "endswith")
            case_sensitive: 是否区分大小写
            
        Returns:
            匹配的识别结果列表
        """
        all_recognitions = self.recognize(frame)
        
        matches = []
        for rec in all_recognitions:
            text = rec['text']
            
            # 大小写处理
            if not case_sensitive:
                text = text.lower()
                target = target_text.lower()
            else:
                target = target_text
            
            # 匹配判断
            is_match = False
            if match_mode == "contains":
                is_match = target in text
            elif match_mode == "equals":
                is_match = text == target
            elif match_mode == "startswith":
                is_match = text.startswith(target)
            elif match_mode == "endswith":
                is_match = text.endswith(target)
            
            if is_match:
                matches.append(rec)
        
        return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        # 如果使用PP-OCR Sophon后端,返回Sophon统计信息
        if not self.mock_mode and self.ocr_engine is not None:
            try:
                stats = self.ocr_engine.get_stats()
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
    
    def draw_recognitions(
        self,
        frame: np.ndarray,
        recognitions: List[Dict[str, Any]],
        color: tuple = (0, 0, 255),
        thickness: int = 2,
        show_text: bool = True,
        show_conf: bool = True
    ) -> np.ndarray:
        """在图像上绘制识别结果（用于可视化，模拟版本）
        
        Args:
            frame: 输入图像
            recognitions: 识别结果列表
            color: 边界框颜色 (B, G, R)
            thickness: 线条粗细
            show_text: 是否显示文本
            show_conf: 是否显示置信度
            
        Returns:
            绘制后的图像（模拟版本返回原图）
        """
        try:
            import cv2
            
            result_frame = frame.copy()
            
            for rec in recognitions:
                # 绘制多边形边界框
                bbox = rec['bbox']
                points = np.array(bbox, dtype=np.int32)
                cv2.polylines(result_frame, [points], True, color, thickness)
                
                # 绘制文本和置信度
                if show_text or show_conf:
                    label_parts = []
                    if show_text:
                        label_parts.append(rec['text'])
                    if show_conf:
                        label_parts.append(f"{rec['conf']:.2f}")
                    
                    label_text = " ".join(label_parts)
                    
                    # 文本位置（左上角）
                    x, y = int(bbox[0][0]), int(bbox[0][1])
                    
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
                        (x, y - text_height - baseline - 5),
                        (x + text_width, y),
                        color,
                        -1
                    )
                    
                    # 绘制文本
                    cv2.putText(
                        result_frame,
                        label_text,
                        (x, y - baseline - 2),
                        font,
                        font_scale,
                        (255, 255, 255),
                        font_thickness
                    )
            
            return result_frame
        except ImportError:
            logger.warning("opencv-python 未安装，跳过绘制识别结果")
            return frame

