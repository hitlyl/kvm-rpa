"""Sophon YOLO检测器

基于Sophon SAIL库的YOLO目标检测器,使用BModel进行硬件加速推理
"""
import time
import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import sophon.sail as sail
    SAIL_AVAILABLE = True
except ImportError:
    SAIL_AVAILABLE = False
    logger.warning("sophon.sail 未安装,无法使用Sophon硬件加速")

# 导入后处理模块
try:
    from detection.postprocess_numpy import PostProcess
    from detection.utils import COCO_CLASSES, COLORS
    POSTPROCESS_AVAILABLE = True
except ImportError:
    POSTPROCESS_AVAILABLE = False
    logger.warning("YOLO后处理模块未找到")


class SophonYOLODetector:
    """Sophon YOLO检测器
    
    使用Sophon SAIL库加载BModel进行YOLO目标检测
    
    Attributes:
        bmodel_path: BModel文件路径
        dev_id: Sophon设备ID
        conf_threshold: 置信度阈值
        nms_threshold: NMS阈值
    """
    
    def __init__(
        self,
        bmodel_path: str,
        dev_id: int = 0,
        conf_threshold: float = 0.25,
        nms_threshold: float = 0.45
    ):
        """初始化Sophon YOLO检测器
        
        Args:
            bmodel_path: BModel文件路径
            dev_id: Sophon设备ID
            conf_threshold: 置信度阈值
            nms_threshold: NMS阈值
        """
        if not SAIL_AVAILABLE:
            raise RuntimeError("sophon.sail 未安装,无法使用Sophon YOLO检测器")
        
        if not POSTPROCESS_AVAILABLE:
            raise RuntimeError("YOLO后处理模块未找到")
        
        self.bmodel_path = bmodel_path
        self.dev_id = dev_id
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        
        # Sophon引擎和相关对象
        self.net: Optional[sail.Engine] = None
        self.handle: Optional[sail.Handle] = None
        self.bmcv: Optional[sail.Bmcv] = None
        self.graph_name: Optional[str] = None
        
        # 模型输入输出信息
        self.input_name: Optional[str] = None
        self.input_dtype = None
        self.img_dtype = None
        self.input_scale = None
        self.input_shape = None
        self.input_shapes = None
        
        self.output_names = []
        self.output_tensors = {}
        self.output_scales = {}
        
        self.batch_size = 1
        self.net_h = 640
        self.net_w = 640
        
        # 预处理参数
        self.use_resize_padding = True
        self.use_vpp = False
        self.ab = None
        
        # 后处理器
        self.postprocess: Optional[PostProcess] = None
        
        # 类别名称
        self.class_names = COCO_CLASSES
        
        # 统计信息
        self.stats = {
            'total_inferences': 0,
            'total_detections': 0,
            'avg_inference_time': 0.0,
            'avg_preprocess_time': 0.0,
            'avg_postprocess_time': 0.0,
            'errors': 0
        }
        
        # 加载模型
        self._load_model()
    
    def _load_model(self) -> bool:
        """加载BModel模型
        
        Returns:
            bool: 是否加载成功
        """
        try:
            logger.info(f"正在加载Sophon BModel: {self.bmodel_path}")
            
            # 创建Engine
            self.net = sail.Engine(self.bmodel_path, self.dev_id, sail.IOMode.SYSO)
            logger.debug(f"BModel加载成功: {self.bmodel_path}")
            
            # 创建Handle和Bmcv
            self.handle = sail.Handle(self.dev_id)
            self.bmcv = sail.Bmcv(self.handle)
            self.graph_name = self.net.get_graph_names()[0]
            
            # 获取输入信息
            self.input_name = self.net.get_input_names(self.graph_name)[0]
            self.input_dtype = self.net.get_input_dtype(self.graph_name, self.input_name)
            self.img_dtype = self.bmcv.get_bm_image_data_format(self.input_dtype)
            self.input_scale = self.net.get_input_scale(self.graph_name, self.input_name)
            self.input_shape = self.net.get_input_shape(self.graph_name, self.input_name)
            self.input_shapes = {self.input_name: self.input_shape}
            
            # 获取输出信息
            self.output_names = self.net.get_output_names(self.graph_name)
            for output_name in self.output_names:
                output_shape = self.net.get_output_shape(self.graph_name, output_name)
                output_dtype = self.net.get_output_dtype(self.graph_name, output_name)
                output_scale = self.net.get_output_scale(self.graph_name, output_name)
                output = sail.Tensor(self.handle, output_shape, output_dtype, True, True)
                self.output_tensors[output_name] = output
                self.output_scales[output_name] = output_scale
                
                # 检查输出格式
                if output_shape[1] < output_shape[2]:
                    raise ValueError('仅支持OPT模型格式')
            
            # 获取网络尺寸
            self.batch_size = self.input_shape[0]
            self.net_h = self.input_shape[2]
            self.net_w = self.input_shape[3]
            
            # 初始化预处理参数
            self.ab = [x * self.input_scale / 255.0 for x in [1, 0, 1, 0, 1, 0]]
            
            # 初始化后处理器
            self.postprocess = PostProcess(
                conf_thresh=self.conf_threshold,
                nms_thresh=self.nms_threshold,
                agnostic=False,
                multi_label=False,
                max_det=300
            )
            
            logger.success(f"Sophon YOLO检测器初始化成功: {self.net_w}x{self.net_h}")
            return True
            
        except Exception as e:
            logger.error(f"加载BModel失败: {e}")
            raise
    
    def detect(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None,
        nms_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """检测图像中的目标
        
        Args:
            frame: 输入图像(BGR格式numpy数组)
            conf_threshold: 置信度阈值(可选,覆盖默认值)
            nms_threshold: NMS阈值(可选,覆盖默认值)
            
        Returns:
            检测结果列表,每个结果包含:
            - label: 类别名称
            - bbox: 边界框[x1, y1, x2, y2]
            - conf: 置信度
            - center: 中心点[cx, cy]
            - class_id: 类别ID
        """
        if self.net is None:
            logger.error("模型未加载")
            return []
        
        start_time = time.time()
        
        try:
            # 更新阈值
            if conf_threshold is not None:
                self.postprocess.conf_thresh = conf_threshold
            if nms_threshold is not None:
                self.postprocess.nms_thresh = nms_threshold
            
            # 预处理
            preprocess_start = time.time()
            bmimg, ratio, txy = self._preprocess(frame)
            preprocess_time = time.time() - preprocess_start
            
            # 推理
            inference_start = time.time()
            outputs = self._inference(bmimg)
            inference_time = time.time() - inference_start
            
            # 后处理
            postprocess_start = time.time()
            detections = self._postprocess(outputs, ratio, txy, frame.shape[:2])
            postprocess_time = time.time() - postprocess_start
            
            # 更新统计信息
            total_time = time.time() - start_time
            self.stats['total_inferences'] += 1
            self.stats['total_detections'] += len(detections)
            
            alpha = 0.1
            self.stats['avg_inference_time'] = (
                alpha * inference_time + (1 - alpha) * self.stats['avg_inference_time']
            )
            self.stats['avg_preprocess_time'] = (
                alpha * preprocess_time + (1 - alpha) * self.stats['avg_preprocess_time']
            )
            self.stats['avg_postprocess_time'] = (
                alpha * postprocess_time + (1 - alpha) * self.stats['avg_postprocess_time']
            )
            
            logger.debug(
                f"YOLO检测完成 - 总耗时: {total_time:.3f}s "
                f"(预处理:{preprocess_time:.3f}s, 推理:{inference_time:.3f}s, "
                f"后处理:{postprocess_time:.3f}s), 检测数: {len(detections)}"
            )
            
            return detections
            
        except Exception as e:
            logger.exception(f"YOLO检测失败: {e}")
            self.stats['errors'] += 1
            return []
    
    def _preprocess(self, frame: np.ndarray):
        """预处理图像
        
        Args:
            frame: 输入BGR图像
            
        Returns:
            (preprocessed_bmimg, ratio, txy)
        """
        # 将numpy数组转换为BMImage
        height, width = frame.shape[:2]
        bmimg = sail.BMImage(self.handle, height, width,
                            sail.Format.FORMAT_BGR_PACKED,
                            sail.DATA_TYPE_EXT_1N_BYTE)
        
        # 复制数据到BMImage
        bmimg_data = bmimg.data()
        np.copyto(bmimg_data, frame.flatten())
        
        # 转换为RGB平面格式
        rgb_planar_img = sail.BMImage(self.handle, height, width,
                                      sail.Format.FORMAT_RGB_PLANAR,
                                      sail.DATA_TYPE_EXT_1N_BYTE)
        self.bmcv.convert_format(bmimg, rgb_planar_img)
        
        # Resize with padding
        resized_img_rgb, ratio, txy = self._resize_bmcv(rgb_planar_img)
        
        # 归一化和类型转换
        preprocessed_bmimg = sail.BMImage(self.handle, self.net_h, self.net_w,
                                         sail.Format.FORMAT_RGB_PLANAR,
                                         self.img_dtype)
        self.bmcv.convert_to(
            resized_img_rgb, preprocessed_bmimg,
            ((self.ab[0], self.ab[1]), (self.ab[2], self.ab[3]), (self.ab[4], self.ab[5]))
        )
        
        return preprocessed_bmimg, ratio, txy
    
    def _resize_bmcv(self, bmimg):
        """使用BMCV调整图像大小(带padding)
        
        Args:
            bmimg: 输入BMImage
            
        Returns:
            (resized_bmimg, ratio, txy)
        """
        img_w = bmimg.width()
        img_h = bmimg.height()
        
        if self.use_resize_padding:
            # 计算缩放比例
            r_w = self.net_w / img_w
            r_h = self.net_h / img_h
            r = min(r_w, r_h)
            tw = int(round(r * img_w))
            th = int(round(r * img_h))
            tx1, ty1 = self.net_w - tw, self.net_h - th
            
            tx1 /= 2
            ty1 /= 2
            
            ratio = (r, r)
            txy = (tx1, ty1)
            
            # 设置padding属性
            attr = sail.PaddingAtrr()
            attr.set_stx(int(round(tx1 - 0.1)))
            attr.set_sty(int(round(ty1 - 0.1)))
            attr.set_w(tw)
            attr.set_h(th)
            attr.set_r(114)
            attr.set_g(114)
            attr.set_b(114)
            
            # Resize with padding
            resized_img_rgb = self.bmcv.crop_and_resize_padding(
                bmimg, 0, 0, img_w, img_h, self.net_w, self.net_h, attr,
                sail.bmcv_resize_algorithm.BMCV_INTER_LINEAR
            )
        else:
            r_w = self.net_w / img_w
            r_h = self.net_h / img_h
            ratio = (r_w, r_h)
            txy = (0, 0)
            resized_img_rgb = self.bmcv.resize(bmimg, self.net_w, self.net_h)
        
        return resized_img_rgb, ratio, txy
    
    def _inference(self, bmimg):
        """执行推理
        
        Args:
            bmimg: 预处理后的BMImage
            
        Returns:
            输出字典
        """
        # 将BMImage转换为Tensor
        input_tensor = sail.Tensor(self.handle, self.input_shape, self.input_dtype, False, False)
        self.bmcv.bm_image_to_tensor(bmimg, input_tensor)
        
        # 执行推理
        input_tensors = {self.input_name: input_tensor}
        self.net.process(self.graph_name, input_tensors, self.input_shapes, self.output_tensors)
        
        # 获取输出
        outputs_dict = {}
        for name in self.output_names:
            outputs_dict[name] = self.output_tensors[name].asnumpy(self.output_scales[name])
        
        return outputs_dict
    
    def _postprocess(self, outputs_dict, ratio, txy, img_shape):
        """后处理推理结果
        
        Args:
            outputs_dict: 推理输出字典
            ratio: 缩放比例
            txy: padding偏移
            img_shape: 原始图像尺寸(h, w)
            
        Returns:
            检测结果列表
        """
        # 使用PostProcess进行后处理
        results = self.postprocess(outputs_dict, [img_shape], [ratio], [txy])
        
        # 转换为标准格式
        detections = []
        if results and len(results) > 0:
            for det in results[0]:  # 只处理第一张图
                x1, y1, x2, y2, score, class_id = det
                
                # 计算中心点
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                
                # 获取类别名称
                label = self.class_names[int(class_id)] if int(class_id) < len(self.class_names) else str(int(class_id))
                
                detection = {
                    'label': label,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'conf': float(score),
                    'center': [float(cx), float(cy)],
                    'class_id': int(class_id)
                }
                
                detections.append(detection)
        
        return detections
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        return self.stats.copy()
    
    def reload_model(self, new_bmodel_path: str) -> bool:
        """热更新模型
        
        Args:
            new_bmodel_path: 新BModel文件路径
            
        Returns:
            bool: 是否更新成功
        """
        logger.info(f"热更新BModel: {new_bmodel_path}")
        
        try:
            # 保存旧路径
            old_path = self.bmodel_path
            self.bmodel_path = new_bmodel_path
            
            # 重新加载
            self._load_model()
            
            logger.success(f"BModel热更新成功: {new_bmodel_path}")
            return True
            
        except Exception as e:
            logger.error(f"BModel热更新失败: {e}")
            # 恢复旧路径
            self.bmodel_path = old_path
            return False





















