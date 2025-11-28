"""PP-OCR Sophon引擎

基于Sophon SAIL库的PP-OCR文字识别引擎,集成检测、分类、识别三个模型
"""
import time
import copy
import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import sophon.sail as sail
    SAIL_AVAILABLE = True
except ImportError:
    SAIL_AVAILABLE = False
    logger.warning("sophon.sail 未安装,无法使用Sophon硬件加速")

# 导入PP-OCR模块
try:
    import sys
    from pathlib import Path
    
    # 确保能导入ocr目录下的模块
    ocr_dir = Path(__file__).parent
    if str(ocr_dir) not in sys.path:
        sys.path.insert(0, str(ocr_dir))
    
    import ppocr_det_opencv as predict_det
    import ppocr_rec_opencv as predict_rec
    import ppocr_cls_opencv as predict_cls
    PPOCR_AVAILABLE = True
except ImportError as e:
    PPOCR_AVAILABLE = False
    logger.warning(f"PP-OCR模块未找到: {e}")


def get_rotate_crop_image(img, points):
    """从图像中裁剪并旋转文本区域
    
    Args:
        img: 输入图像
        points: 四个角点坐标
        
    Returns:
        裁剪后的图像
    """
    import cv2
    
    assert len(points) == 4, "points必须是4个点"
    img_crop_width = int(
        max(
            np.linalg.norm(points[0] - points[1]),
            np.linalg.norm(points[2] - points[3]))
    )
    img_crop_height = int(
        max(
            np.linalg.norm(points[0] - points[3]),
            np.linalg.norm(points[1] - points[2]))
    )
    
    # 对齐到16的倍数(用于Sophon加速)
    img_crop_width = max(16, img_crop_width)
    img_crop_height = max(16, img_crop_height)
    
    pts_std = np.float32([
        [0, 0],
        [img_crop_width, 0],
        [img_crop_width, img_crop_height],
        [0, img_crop_height]
    ])
    M = cv2.getPerspectiveTransform(points, pts_std)
    dst_img = cv2.warpPerspective(
        img,
        M,
        (img_crop_width, img_crop_height),
        borderMode=cv2.BORDER_REPLICATE,
        flags=cv2.INTER_CUBIC
    )
    dst_img_height, dst_img_width = dst_img.shape[0:2]
    if dst_img_height * 1.0 / dst_img_width >= 1.5:
        dst_img = np.rot90(dst_img)
    return dst_img


class Args:
    """参数类,用于兼容sample代码
    
    根据 ppocr_det_opencv.py 和 ppocr_rec_opencv.py 的要求:
    - bmodel_det: 检测模型路径
    - bmodel_rec: 识别模型路径
    - bmodel_cls: 分类模型路径
    - dev_id: 设备ID
    - char_dict_path: 字符字典路径
    - img_size: 识别模型输入尺寸列表
    - use_space_char: 是否使用空格字符
    - use_beam_search: 是否使用 beam search
    - beam_size: beam search 宽度
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class PPOCRSophon:
    """PP-OCR Sophon引擎
    
    集成检测(det)、分类(cls)、识别(rec)三个模型
    
    Attributes:
        det_model: 检测模型路径
        rec_model: 识别模型路径
        cls_model: 分类模型路径
        char_dict_path: 字符字典路径
        use_angle_cls: 是否使用方向分类
        rec_thresh: 识别置信度阈值
        dev_id: Sophon设备ID
    """
    
    def __init__(
        self,
        det_model: str,
        rec_model: str,
        cls_model: str = None,
        char_dict_path: str = None,
        use_angle_cls: bool = False,
        rec_thresh: float = 0.5,
        dev_id: int = 0,
        img_size: list = None,
        use_space_char: bool = True,
        use_beam_search: bool = False,
        beam_size: int = 5
    ):
        """初始化PP-OCR Sophon引擎
        
        Args:
            det_model: 检测模型BModel路径
            rec_model: 识别模型BModel路径
            cls_model: 分类模型BModel路径(可选)
            char_dict_path: 字符字典路径(ppocr_keys_v1.txt)
            use_angle_cls: 是否使用方向分类
            rec_thresh: 识别置信度阈值
            dev_id: Sophon设备ID
            img_size: 识别模型输入尺寸列表,如 [[320, 48], [640, 48]]
            use_space_char: 是否使用空格字符
            use_beam_search: 是否使用 beam search
            beam_size: beam search 宽度
        """
        if not SAIL_AVAILABLE:
            raise RuntimeError("sophon.sail 未安装,无法使用PP-OCR Sophon引擎")
        
        if not PPOCR_AVAILABLE:
            raise RuntimeError("PP-OCR模块未找到")
        
        self.det_model = det_model
        self.rec_model = rec_model
        self.cls_model = cls_model
        self.char_dict_path = char_dict_path or "models/ppocr_keys_v1.txt"
        self.use_angle_cls = use_angle_cls
        self.rec_thresh = rec_thresh
        self.dev_id = dev_id
        self.img_size = img_size or [[320, 48], [640, 48]]
        self.use_space_char = use_space_char
        self.use_beam_search = use_beam_search
        self.beam_size = beam_size
        
        # 初始化各个模块
        self.text_detector = None
        self.text_recognizer = None
        self.text_classifier = None
        
        # 统计信息
        self.stats = {
            'total_recognitions': 0,
            'total_texts': 0,
            'avg_recognition_time': 0.0,
            'avg_det_time': 0.0,
            'avg_rec_time': 0.0,
            'avg_cls_time': 0.0,
            'errors': 0
        }
        
        # 裁剪统计
        self.crop_num = 0
        self.crop_time = 0.0
        
        # 加载模型
        self._load_models()
    
    def _load_models(self) -> None:
        """加载所有模型"""
        try:
            logger.info("正在加载PP-OCR Sophon模型...")
            logger.info(f"检测模型: {self.det_model}")
            logger.info(f"识别模型: {self.rec_model}")
            logger.info(f"字符字典: {self.char_dict_path}")
            
            # 创建检测器参数 (使用 bmodel_det 作为参数名)
            det_args = Args(
                bmodel_det=self.det_model,
                dev_id=self.dev_id,
                det_limit_side_len=[640],  # 检测器会从模型获取实际尺寸
                det_limit_type='max'
            )
            self.text_detector = predict_det.PPOCRv2Det(det_args)
            logger.info(f"检测模型加载成功: {self.det_model}")
            
            # 创建识别器参数 (使用 bmodel_rec 作为参数名)
            rec_args = Args(
                bmodel_rec=self.rec_model,
                dev_id=self.dev_id,
                char_dict_path=self.char_dict_path,
                img_size=self.img_size,
                use_space_char=self.use_space_char,
                use_beam_search=self.use_beam_search,
                beam_size=self.beam_size
            )
            self.text_recognizer = predict_rec.PPOCRv2Rec(rec_args)
            logger.info(f"识别模型加载成功: {self.rec_model}")
            
            # 如果需要,加载分类器
            if self.use_angle_cls and self.cls_model:
                cls_args = Args(
                    bmodel_cls=self.cls_model,
                    dev_id=self.dev_id,
                    label_list=['0', '180'],
                    cls_thresh=0.9
                )
                self.text_classifier = predict_cls.PPOCRv2Cls(cls_args)
                logger.info(f"分类模型加载成功: {self.cls_model}")
            
            logger.success("PP-OCR Sophon引擎初始化成功")
            
        except Exception as e:
            logger.error(f"加载PP-OCR模型失败: {e}")
            raise
    
    def recognize(
        self,
        frame_or_roi: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """识别图像中的文字
        
        Args:
            frame_or_roi: 输入图像(BGR格式)
            conf_threshold: 置信度阈值(可选,覆盖默认值)
            
        Returns:
            识别结果列表,每个结果包含:
            - text: 识别的文本
            - conf: 置信度
            - bbox: 文本边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - bbox_rect: 矩形边界框 [x, y, w, h]
        """
        if self.text_detector is None or self.text_recognizer is None:
            logger.error("模型未加载")
            return []
        
        start_time = time.time()
        
        try:
            # 使用阈值
            thresh = conf_threshold if conf_threshold is not None else self.rec_thresh
            
            # 准备输入(单张图片)
            img_list = [frame_or_roi]
            
            # 检测文本框
            det_start = time.time()
            dt_boxes_list = self.text_detector(img_list)
            det_time = time.time() - det_start
            
            # 准备裁剪图像字典
            img_dict = {"imgs": [], "dt_boxes": [], "pic_ids": []}
            
            for id, dt_boxes in enumerate(dt_boxes_list):
                self.crop_num += len(dt_boxes)
                start_crop = time.time()
                for bno in range(len(dt_boxes)):
                    tmp_box = copy.deepcopy(dt_boxes[bno])
                    img_crop = get_rotate_crop_image(img_list[id], tmp_box)
                    img_dict["imgs"].append(img_crop)
                    img_dict["dt_boxes"].append(dt_boxes[bno])
                    img_dict["pic_ids"].append(id)
                self.crop_time += time.time() - start_crop
            
            # 方向分类
            cls_time = 0.0
            if self.use_angle_cls and self.text_classifier and len(img_dict["imgs"]) > 0:
                cls_start = time.time()
                img_dict["imgs"], cls_res = self.text_classifier(img_dict["imgs"])
                cls_time = time.time() - cls_start
            
            # 文本识别
            rec_start = time.time()
            rec_res = self.text_recognizer(img_dict["imgs"])
            rec_time = time.time() - rec_start
            
            # 组装结果
            recognitions = []
            for i, id in enumerate(rec_res.get("ids")):
                text, score = rec_res["res"][i]
                if score >= thresh:
                    dt_box = img_dict["dt_boxes"][id]
                    
                    # 计算矩形边界框
                    x_coords = [pt[0] for pt in dt_box]
                    y_coords = [pt[1] for pt in dt_box]
                    x = min(x_coords)
                    y = min(y_coords)
                    w = max(x_coords) - x
                    h = max(y_coords) - y
                    
                    recognition = {
                        'text': text,
                        'conf': float(score),
                        'bbox': [[float(pt[0]), float(pt[1])] for pt in dt_box],
                        'bbox_rect': [float(x), float(y), float(w), float(h)]
                    }
                    
                    recognitions.append(recognition)
            
            # 更新统计
            total_time = time.time() - start_time
            self.stats['total_recognitions'] += 1
            self.stats['total_texts'] += len(recognitions)
            
            alpha = 0.1
            self.stats['avg_recognition_time'] = (
                alpha * total_time + (1 - alpha) * self.stats['avg_recognition_time']
            )
            self.stats['avg_det_time'] = (
                alpha * det_time + (1 - alpha) * self.stats['avg_det_time']
            )
            self.stats['avg_rec_time'] = (
                alpha * rec_time + (1 - alpha) * self.stats['avg_rec_time']
            )
            self.stats['avg_cls_time'] = (
                alpha * cls_time + (1 - alpha) * self.stats['avg_cls_time']
            )
            
            logger.debug(
                f"OCR识别完成 - 总耗时: {total_time:.3f}s "
                f"(检测:{det_time:.3f}s, 分类:{cls_time:.3f}s, "
                f"识别:{rec_time:.3f}s), 识别数: {len(recognitions)}"
            )
            
            return recognitions
            
        except Exception as e:
            logger.exception(f"OCR识别失败: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.stats.copy()
        stats['crop_num'] = self.crop_num
        stats['crop_time'] = self.crop_time
        return stats





