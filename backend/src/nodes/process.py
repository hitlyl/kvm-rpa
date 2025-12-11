"""处理节点

包含图像预处理、YOLO 检测、OCR 识别等处理节点。
节点使用流程上下文中的缓存实例，避免重复初始化。
"""
from typing import Dict, Any, Optional, List
from loguru import logger

from nodes.base import BaseNode, NodeConfig, NodePropertyDef
from nodes import register_node
from api.sse_service import send_debug


@register_node
class ImageCropNode(BaseNode):
    """图像裁剪节点
    
    将当前帧裁剪为指定区域，用于后续处理（如 OCR）。
    裁剪后的图像会替换 context.current_frame。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="image_crop",
            label="图像裁剪",
            category="process",
            icon="Crop",
            color="#91CC75",
            description="裁剪图像到指定区域",
            properties=[
                NodePropertyDef(
                    key="x",
                    label="X 坐标",
                    type="number",
                    default=0,
                    description="裁剪区域左上角 X 坐标"
                ),
                NodePropertyDef(
                    key="y",
                    label="Y 坐标",
                    type="number",
                    default=0,
                    description="裁剪区域左上角 Y 坐标"
                ),
                NodePropertyDef(
                    key="width",
                    label="宽度",
                    type="number",
                    default=640,
                    description="裁剪区域宽度（0 表示到图像右边缘）"
                ),
                NodePropertyDef(
                    key="height",
                    label="高度",
                    type="number",
                    default=480,
                    description="裁剪区域高度（0 表示到图像下边缘）"
                ),
                NodePropertyDef(
                    key="save_original",
                    label="保留原图",
                    type="boolean",
                    default=True,
                    description="是否将原图保存到 context.original_frame"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行图像裁剪"""
        flow_id = getattr(context, 'flow_id', '')
        loop_count = getattr(context, 'loop_count', 0)
        
        if context.current_frame is None:
            logger.warning("当前帧为空，无法进行裁剪")
            if flow_id:
                send_debug(flow_id, f"❌ 裁剪[{loop_count}]: 当前帧为空")
            return False
        
        try:
            import numpy as np
            
            frame = context.current_frame
            h, w = frame.shape[:2]
            
            # 获取裁剪参数
            x = int(properties.get('x', 0))
            y = int(properties.get('y', 0))
            crop_width = int(properties.get('width', 0))
            crop_height = int(properties.get('height', 0))
            save_original = properties.get('save_original', True)
            
            # 确保坐标有效
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            
            # 计算实际裁剪区域
            if crop_width <= 0:
                crop_width = w - x
            if crop_height <= 0:
                crop_height = h - y
            
            # 确保不超出边界
            x2 = min(x + crop_width, w)
            y2 = min(y + crop_height, h)
            
            # 保存原图
            if save_original:
                context.original_frame = frame.copy()
            
            # 裁剪
            cropped = frame[y:y2, x:x2]
            
            # 更新当前帧
            context.current_frame = cropped
            
            # 记录裁剪信息（用于坐标转换）
            context.crop_offset = (x, y)
            context.crop_size = (x2 - x, y2 - y)
            
            crop_h, crop_w = cropped.shape[:2]
            logger.debug(f"图像裁剪完成: ({x}, {y}) -> {crop_w}x{crop_h}")
            
            if flow_id:
                send_debug(flow_id, f"✂️ 裁剪[{loop_count}]: ({x},{y}) {crop_w}x{crop_h}")
            
            return True
            
        except Exception as e:
            logger.error(f"图像裁剪失败: {e}")
            if flow_id:
                send_debug(flow_id, f"❌ 裁剪[{loop_count}]: 失败 - {e}")
            return False


@register_node
class PreprocessingNode(BaseNode):
    """图像预处理节点"""
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="preprocessing",
            label="图像预处理",
            category="process",
            icon="MagicStick",
            color="#91CC75",
            description="对图像进行预处理",
            properties=[
                NodePropertyDef(
                    key="resize",
                    label="是否缩放",
                    type="boolean",
                    default=False
                ),
                NodePropertyDef(
                    key="target_width",
                    label="目标宽度",
                    type="number",
                    default=1280
                ),
                NodePropertyDef(
                    key="target_height",
                    label="目标高度",
                    type="number",
                    default=720
                ),
                NodePropertyDef(
                    key="denoise",
                    label="是否去噪",
                    type="boolean",
                    default=False
                ),
                NodePropertyDef(
                    key="sharpen",
                    label="是否锐化",
                    type="boolean",
                    default=False
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行图像预处理"""
        if context.current_frame is None:
            logger.warning("当前帧为空，无法进行预处理")
            return False
        
        try:
            import cv2
            
            processed_frame = context.current_frame
            
            if properties.get('resize', False):
                target_width = int(properties.get('target_width', 1280))
                target_height = int(properties.get('target_height', 720))
                processed_frame = cv2.resize(
                    processed_frame, 
                    (target_width, target_height)
                )
                logger.debug(f"图像已缩放到: {target_width}x{target_height}")
            
            if properties.get('denoise', False):
                processed_frame = cv2.fastNlMeansDenoisingColored(
                    processed_frame, None, 10, 10, 7, 21
                )
                logger.debug("图像已去噪")
            
            if properties.get('sharpen', False):
                import numpy as np
                kernel = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
                processed_frame = cv2.filter2D(processed_frame, -1, kernel)
                logger.debug("图像已锐化")
            
            context.current_frame = processed_frame
            logger.debug("图像预处理完成")
            return True
            
        except ImportError:
            logger.warning("opencv-python 未安装，跳过预处理")
            return True
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            return False


@register_node
class YOLODetectionNode(BaseNode):
    """YOLO 检测节点
    
    使用流程上下文中缓存的检测器实例。
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="yolo_detection",
            label="YOLO 检测",
            category="process",
            icon="View",
            color="#91CC75",
            description="使用 YOLO 进行目标检测",
            properties=[
                NodePropertyDef(
                    key="model_path",
                    label="模型路径",
                    type="text",
                    default="models/yolov8n.bmodel",
                    placeholder="BModel 文件路径"
                ),
                NodePropertyDef(
                    key="backend",
                    label="后端",
                    type="select",
                    default="auto",
                    options=[
                        {"label": "自动选择", "value": "auto"},
                        {"label": "Sophon硬件", "value": "sophon"},
                        {"label": "模拟模式", "value": "mock"}
                    ]
                ),
                NodePropertyDef(
                    key="dev_id",
                    label="设备ID",
                    type="number",
                    default=0
                ),
                NodePropertyDef(
                    key="conf_threshold",
                    label="置信度阈值",
                    type="number",
                    default=0.25
                ),
                NodePropertyDef(
                    key="iou_threshold",
                    label="IOU阈值",
                    type="number",
                    default=0.45
                ),
                NodePropertyDef(
                    key="target_labels",
                    label="目标标签",
                    type="textarea",
                    placeholder="多个标签用逗号分隔（留空表示不过滤）"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行 YOLO 检测"""
        flow_id = getattr(context, 'flow_id', '')
        
        if context.current_frame is None:
            logger.warning("当前帧为空，无法进行检测")
            if flow_id:
                send_debug(flow_id, "YOLO: 当前帧为空，无法进行检测")
            return False
        
        try:
            detector = self._get_or_create_detector(context, properties)
            if detector is None:
                logger.error("无法创建 YOLO 检测器")
                if flow_id:
                    send_debug(flow_id, "YOLO: 无法创建检测器")
                return False
            
            conf_threshold = float(properties.get('conf_threshold', 0.25))
            iou_threshold = float(properties.get('iou_threshold', 0.45))
            
            # 发送调试信息
            if flow_id:
                frame_shape = context.current_frame.shape if hasattr(context.current_frame, 'shape') else 'unknown'
                send_debug(flow_id, f"YOLO: 开始检测，图像尺寸={frame_shape}，置信度={conf_threshold}")
            
            results = detector.detect(
                context.current_frame,
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold
            )
            
            context.detection_results = results
            result_count = len(results) if results else 0
            logger.debug(f"YOLO检测完成，检测到 {result_count} 个目标")
            
            # 发送检测结果到前端
            if flow_id:
                send_debug(flow_id, f"YOLO: 检测完成，共 {result_count} 个目标")
                # 发送前几个检测结果
                if results:
                    for i, r in enumerate(results[:5]):
                        label = r.get('label', 'unknown')
                        conf = r.get('confidence', 0)
                        bbox = r.get('bbox', [])
                        send_debug(flow_id, f"YOLO [{i+1}]: {label} conf={conf:.2f} bbox={bbox}")
            
            target_labels = properties.get('target_labels', '')
            if target_labels and results:
                labels = [label.strip() for label in target_labels.split(',') if label.strip()]
                if labels:
                    filtered_results = [r for r in results if r.get('label') in labels]
                    context.detection_results = filtered_results
                    logger.debug(f"过滤后剩余 {len(filtered_results)} 个目标")
                    if flow_id:
                        send_debug(flow_id, f"YOLO: 过滤标签 {labels}，剩余 {len(filtered_results)} 个目标")
            
            return True
            
        except Exception as e:
            logger.error(f"YOLO检测失败: {e}")
            if flow_id:
                send_debug(flow_id, f"YOLO: 检测失败 - {str(e)}")
            return False
    
    def _get_or_create_detector(self, context: Any, properties: Dict[str, Any]):
        """获取或创建 YOLO 检测器"""
        from detection.yolo_detector import YOLODetector
        
        node_id = getattr(context, 'current_node_id', 'default')
        
        if not hasattr(context, 'yolo_detectors'):
            context.yolo_detectors = {}
        
        config_key = f"{node_id}_{properties.get('model_path')}_{properties.get('backend')}"
        
        if config_key not in context.yolo_detectors:
            try:
                detector = YOLODetector(
                    model_path=properties.get('model_path', 'models/yolov8n.bmodel'),
                    conf_threshold=float(properties.get('conf_threshold', 0.25)),
                    iou_threshold=float(properties.get('iou_threshold', 0.45)),
                    backend=properties.get('backend', 'auto'),
                    dev_id=int(properties.get('dev_id', 0))
                )
                context.yolo_detectors[config_key] = detector
                logger.info(f"YOLO检测器已创建: {properties.get('model_path')}")
            except Exception as e:
                logger.error(f"创建YOLO检测器失败: {e}")
                return None
        
        return context.yolo_detectors[config_key]


@register_node
class OCRRecognitionNode(BaseNode):
    """OCR 识别节点
    
    识别图像中的文字，输出包含文字、坐标、置信度的结构化结果。
    
    输出结果格式:
    context.ocr_results: [
        {
            'text': '识别的文字',
            'confidence': 0.95,
            'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 四个角点
            'center': (cx, cy),  # 中心坐标
            'rect': [x, y, w, h]  # 外接矩形
        },
        ...
    ]
    """
    
    @classmethod
    def get_config(cls) -> NodeConfig:
        return NodeConfig(
            type="ocr_recognition",
            label="OCR 识别",
            category="process",
            icon="Reading",
            color="#91CC75",
            description="识别图像中的文字",
            properties=[
                NodePropertyDef(
                    key="backend",
                    label="后端",
                    type="select",
                    default="auto",
                    options=[
                        {"label": "自动选择", "value": "auto"},
                        {"label": "PP-OCR Sophon", "value": "sophon"},
                        {"label": "模拟模式", "value": "mock"}
                    ]
                ),
                NodePropertyDef(
                    key="det_model",
                    label="检测模型路径",
                    type="text",
                    default="models/ch_PP-OCRv4_det_fp16.bmodel",
                    placeholder="检测模型 BModel 路径"
                ),
                NodePropertyDef(
                    key="rec_model",
                    label="识别模型路径",
                    type="text",
                    default="models/ch_PP-OCRv4_rec_fp16.bmodel",
                    placeholder="识别模型 BModel 路径"
                ),
                NodePropertyDef(
                    key="char_dict_path",
                    label="字符字典路径",
                    type="text",
                    default="models/ppocr_keys_v1.txt",
                    placeholder="字符字典文件路径"
                ),
                NodePropertyDef(
                    key="cls_model",
                    label="分类模型路径",
                    type="text",
                    default="",
                    placeholder="可选，方向分类模型"
                ),
                NodePropertyDef(
                    key="dev_id",
                    label="设备ID",
                    type="number",
                    default=0
                ),
                NodePropertyDef(
                    key="conf_threshold",
                    label="置信度阈值",
                    type="number",
                    default=0.5,
                    description="识别结果置信度阈值（0.3-0.8）"
                ),
                NodePropertyDef(
                    key="use_angle_cls",
                    label="使用方向分类",
                    type="boolean",
                    default=False,
                    description="是否使用文字方向分类"
                ),
                NodePropertyDef(
                    key="img_size_w",
                    label="识别宽度",
                    type="number",
                    default=640,
                    description="识别模型输入宽度（推荐 320-640）"
                ),
                NodePropertyDef(
                    key="img_size_h",
                    label="识别高度",
                    type="number",
                    default=48,
                    description="识别模型输入高度（必须为 48，与模型匹配）"
                ),
                NodePropertyDef(
                    key="use_beam_search",
                    label="使用 Beam Search",
                    type="boolean",
                    default=False,
                    description="Beam Search 可提高识别准确性但更慢"
                ),
                NodePropertyDef(
                    key="beam_size",
                    label="Beam Size",
                    type="number",
                    default=5,
                    description="Beam Search 宽度（仅在启用时有效）"
                )
            ]
        )
    
    def execute(self, context: Any, properties: Dict[str, Any]) -> Any:
        """执行 OCR 识别"""
        flow_id = getattr(context, 'flow_id', '')
        loop_count = getattr(context, 'loop_count', 0)
        
        if context.current_frame is None:
            logger.warning("当前帧为空，无法进行OCR识别")
            if flow_id:
                send_debug(flow_id, f"❌ OCR[{loop_count}]: 当前帧为空，无法进行识别")
            return False
        
        try:
            ocr_engine = self._get_or_create_engine(context, properties)
            if ocr_engine is None:
                logger.error("无法创建 OCR 引擎")
                if flow_id:
                    send_debug(flow_id, f"❌ OCR[{loop_count}]: 无法创建 OCR 引擎")
                return False
            
            conf_threshold = float(properties.get('conf_threshold', 0.6))
            
            # 发送调试信息
            frame_shape = context.current_frame.shape if hasattr(context.current_frame, 'shape') else 'unknown'
            if flow_id:
                send_debug(flow_id, f"🔍 OCR[{loop_count}]: 开始识别 {frame_shape[1]}x{frame_shape[0]}...")
            
            # 执行 OCR 识别
            raw_results = ocr_engine.recognize(
                context.current_frame,
                conf_threshold=conf_threshold
            )
            
            # 标准化输出格式
            normalized_results = self._normalize_results(raw_results)
            
            # 存入上下文
            context.ocr_results = normalized_results
            
            # 清除之前的匹配结果
            if hasattr(context, 'ocr_matched_results'):
                context.ocr_matched_results = []
            if hasattr(context, 'ocr_target_found'):
                context.ocr_target_found = False
            if hasattr(context, 'matched_text_position'):
                context.matched_text_position = None
            
            logger.debug(f"OCR识别完成，识别到 {len(normalized_results)} 个文本")
            
            # 发送识别结果到前端
            if flow_id:
                send_debug(flow_id, f"✅ OCR[{loop_count}]: 识别完成，共 {len(normalized_results)} 个文本")
                # 发送前几个识别结果的详情
                if normalized_results:
                    texts_preview = [r['text'] for r in normalized_results[:5]]
                    send_debug(flow_id, f"📝 OCR[{loop_count}]: {texts_preview}")
            
            # 打印识别结果到日志
            for r in normalized_results[:5]:  # 只打印前5个
                logger.debug(f"  - '{r['text']}' @ {r['center']}, conf={r['confidence']:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            if flow_id:
                send_debug(flow_id, f"OCR: 识别失败 - {str(e)}")
            return False
    
    def _normalize_results(self, raw_results: List[Dict]) -> List[Dict[str, Any]]:
        """标准化 OCR 结果格式"""
        normalized = []
        
        if not raw_results:
            return normalized
        
        for result in raw_results:
            text = result.get('text', '')
            confidence = result.get('confidence', 0.0)
            
            # 获取边界框
            bbox = result.get('bbox')
            rect = result.get('rect') or result.get('bbox_rect')
            
            # 计算中心点
            center = result.get('center')
            
            if not center:
                if bbox and len(bbox) >= 4:
                    if isinstance(bbox[0], (list, tuple)):
                        # bbox 格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        x_coords = [p[0] for p in bbox]
                        y_coords = [p[1] for p in bbox]
                        cx = sum(x_coords) / len(x_coords)
                        cy = sum(y_coords) / len(y_coords)
                        center = (cx, cy)
                        
                        # 计算外接矩形
                        if not rect:
                            x_min, x_max = min(x_coords), max(x_coords)
                            y_min, y_max = min(y_coords), max(y_coords)
                            rect = [x_min, y_min, x_max - x_min, y_max - y_min]
                    else:
                        # bbox 格式: [x, y, w, h]
                        rect = bbox
                        cx = bbox[0] + bbox[2] / 2
                        cy = bbox[1] + bbox[3] / 2
                        center = (cx, cy)
                elif rect:
                    cx = rect[0] + rect[2] / 2
                    cy = rect[1] + rect[3] / 2
                    center = (cx, cy)
            
            normalized.append({
                'text': text,
                'confidence': confidence,
                'bbox': bbox,
                'center': center,
                'rect': rect
            })
        
        return normalized
    
    def _get_or_create_engine(self, context: Any, properties: Dict[str, Any]):
        """获取或创建 OCR 引擎"""
        from ocr.ocr_engine import OCREngine
        
        node_id = getattr(context, 'current_node_id', 'default')
        
        if not hasattr(context, 'ocr_engines'):
            context.ocr_engines = {}
        
        # 计算配置 key（包含影响引擎初始化的参数）
        # 注意：img_size_h 必须为 48，与 PP-OCR 模型匹配
        img_size_w = int(properties.get('img_size_w', 640))
        img_size_h = int(properties.get('img_size_h', 48))
        use_beam_search = properties.get('use_beam_search', False)
        beam_size = int(properties.get('beam_size', 5))
        
        config_key = (f"{node_id}_{properties.get('backend')}_{properties.get('det_model')}_"
                      f"{img_size_w}x{img_size_h}_beam{use_beam_search}")
        
        if config_key not in context.ocr_engines:
            try:
                # 构建 img_size 参数
                # 支持多个尺寸用于不同长度的文本
                img_size = [[img_size_w, img_size_h]]
                # 如果宽度较大，添加一个较小的尺寸用于短文本
                if img_size_w > 400:
                    img_size.insert(0, [320, img_size_h])
                
                engine = OCREngine(
                    lang=['ch', 'en'],  # 默认中英文
                    conf_threshold=float(properties.get('conf_threshold', 0.5)),
                    use_angle_cls=properties.get('use_angle_cls', False),
                    backend=properties.get('backend', 'auto'),
                    det_model=properties.get('det_model'),
                    rec_model=properties.get('rec_model'),
                    cls_model=properties.get('cls_model') or None,
                    char_dict_path=properties.get('char_dict_path'),
                    dev_id=int(properties.get('dev_id', 0)),
                    img_size=img_size,
                    use_beam_search=use_beam_search,
                    beam_size=beam_size
                )
                context.ocr_engines[config_key] = engine
                logger.info(f"OCR引擎已创建: backend={properties.get('backend')}, "
                           f"img_size={img_size}, beam_search={use_beam_search}")
            except Exception as e:
                logger.error(f"创建OCR引擎失败: {e}")
                return None
        
        return context.ocr_engines[config_key]
