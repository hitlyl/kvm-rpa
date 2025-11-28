"""监控指标模块

基于 Prometheus 提供系统监控指标收集功能。
"""
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from loguru import logger


class MetricsCollector:
    """监控指标收集器
    
    收集和暴露系统运行指标，支持 Prometheus 格式。
    """
    
    def __init__(self):
        """初始化指标收集器"""
        # RTSP 相关指标
        self.rtsp_frames_total = Counter(
            'rtsp_frames_total',
            'RTSP 总帧数'
        )
        self.rtsp_dropped_frames_total = Counter(
            'rtsp_dropped_frames_total',
            'RTSP 丢帧总数'
        )
        self.rtsp_reconnect_total = Counter(
            'rtsp_reconnect_total',
            'RTSP 重连次数'
        )
        self.rtsp_fps = Gauge(
            'rtsp_fps',
            '当前帧率'
        )
        self.rtsp_latency = Gauge(
            'rtsp_latency_seconds',
            'RTSP 拉流延迟（秒）'
        )
        
        # YOLO 检测指标
        self.yolo_inference_duration = Histogram(
            'yolo_inference_duration_seconds',
            'YOLO 推理耗时（秒）',
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        self.yolo_detections_total = Counter(
            'yolo_detections_total',
            'YOLO 检测总数',
            ['label']
        )
        self.yolo_inference_errors_total = Counter(
            'yolo_inference_errors_total',
            'YOLO 推理错误总数'
        )
        
        # OCR 识别指标
        self.ocr_inference_duration = Histogram(
            'ocr_inference_duration_seconds',
            'OCR 推理耗时（秒）',
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
        )
        self.ocr_recognitions_total = Counter(
            'ocr_recognitions_total',
            'OCR 识别总数'
        )
        self.ocr_errors_total = Counter(
            'ocr_errors_total',
            'OCR 识别错误总数'
        )
        
        # 键鼠 API 调用指标
        self.kvm_api_calls_total = Counter(
            'kvm_api_calls_total',
            '键鼠 API 调用总数',
            ['action', 'status']
        )
        self.kvm_api_duration = Histogram(
            'kvm_api_duration_seconds',
            '键鼠 API 调用耗时（秒）',
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
        )
        self.kvm_api_retries_total = Counter(
            'kvm_api_retries_total',
            '键鼠 API 重试总数'
        )
        
        # 端到端处理指标
        self.pipeline_duration = Histogram(
            'pipeline_duration_seconds',
            '端到端处理耗时（秒）',
            buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0)
        )
        self.pipeline_executions_total = Counter(
            'pipeline_executions_total',
            '流程执行总数',
            ['status']
        )
        
        # 规则引擎指标
        self.rule_triggers_total = Counter(
            'rule_triggers_total',
            '规则触发总数',
            ['rule_name']
        )
        self.rule_execution_duration = Histogram(
            'rule_execution_duration_seconds',
            '规则执行耗时（秒）',
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0)
        )
        
        logger.info("监控指标收集器已初始化")
    
    def update_rtsp_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新 RTSP 相关指标
        
        Args:
            metrics: RTSP 指标字典
        """
        if 'current_fps' in metrics:
            self.rtsp_fps.set(metrics['current_fps'])
        if 'stream_latency' in metrics:
            self.rtsp_latency.set(metrics['stream_latency'])
    
    def record_yolo_inference(self, duration: float, detections: list) -> None:
        """记录 YOLO 推理
        
        Args:
            duration: 推理耗时（秒）
            detections: 检测结果列表
        """
        self.yolo_inference_duration.observe(duration)
        for det in detections:
            if 'label' in det:
                self.yolo_detections_total.labels(label=det['label']).inc()
    
    def record_yolo_error(self) -> None:
        """记录 YOLO 推理错误"""
        self.yolo_inference_errors_total.inc()
    
    def record_ocr_inference(self, duration: float, recognitions: list) -> None:
        """记录 OCR 推理
        
        Args:
            duration: 推理耗时（秒）
            recognitions: 识别结果列表
        """
        self.ocr_inference_duration.observe(duration)
        self.ocr_recognitions_total.inc(len(recognitions))
    
    def record_ocr_error(self) -> None:
        """记录 OCR 识别错误"""
        self.ocr_errors_total.inc()
    
    def record_kvm_api_call(
        self,
        action: str,
        status: str,
        duration: float,
        retries: int = 0
    ) -> None:
        """记录键鼠 API 调用
        
        Args:
            action: 动作类型 (click, move, key_input, etc.)
            status: 调用状态 (success, error)
            duration: 调用耗时（秒）
            retries: 重试次数
        """
        self.kvm_api_calls_total.labels(action=action, status=status).inc()
        self.kvm_api_duration.observe(duration)
        if retries > 0:
            self.kvm_api_retries_total.inc(retries)
    
    def record_pipeline_execution(self, duration: float, status: str) -> None:
        """记录端到端流程执行
        
        Args:
            duration: 执行耗时（秒）
            status: 执行状态 (success, error)
        """
        self.pipeline_duration.observe(duration)
        self.pipeline_executions_total.labels(status=status).inc()
    
    def record_rule_trigger(self, rule_name: str, duration: float) -> None:
        """记录规则触发
        
        Args:
            rule_name: 规则名称
            duration: 执行耗时（秒）
        """
        self.rule_triggers_total.labels(rule_name=rule_name).inc()
        self.rule_execution_duration.observe(duration)


# 全局指标收集器实例
_metrics_collector: MetricsCollector = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例
    
    Returns:
        MetricsCollector: 指标收集器实例
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metrics_server(port: int = 9090) -> None:
    """启动 Prometheus 指标服务器
    
    Args:
        port: 监听端口
    """
    try:
        start_http_server(port)
        logger.info(f"Prometheus 指标服务器已启动，端口: {port}")
    except Exception as e:
        logger.error(f"启动 Prometheus 指标服务器失败: {e}")

