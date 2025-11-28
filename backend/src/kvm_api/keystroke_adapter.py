"""键鼠 API 适配层

提供键盘和鼠标控制的统一接口，支持通过第三方 API 发送控制指令。
当前为模拟实现，可替换为真实的 KVM 控制器 API 调用。
"""
import time
from typing import List, Optional, Dict, Any
import requests
from loguru import logger


class KeystrokeAdapter:
    """键鼠控制适配器
    
    封装键盘和鼠标操作，通过 REST API 发送到 KVM 控制器。
    支持重试机制和错误处理。
    
    Attributes:
        api_url: API 地址
        token: 认证 Token
        timeout: 请求超时（秒）
        retry_attempts: 重试次数
        retry_delay: 重试延迟（秒）
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8080/v1/exec",
        token: str = "",
        timeout: float = 5.0,
        retry_attempts: int = 2,
        retry_delay: float = 0.5,
        mock_mode: bool = True
    ):
        """初始化键鼠控制适配器
        
        Args:
            api_url: API 地址
            token: 认证 Token
            timeout: 请求超时（秒）
            retry_attempts: 重试次数
            retry_delay: 重试延迟（秒）
            mock_mode: 是否启用模拟模式（不发送真实请求）
        """
        self.api_url = api_url
        self.token = token
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.mock_mode = mock_mode
        
        # 统计信息
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_retries': 0
        }
        
        logger.info(
            f"键鼠适配器初始化 - URL: {self.api_url}, "
            f"模拟模式: {self.mock_mode}"
        )
    
    def _call_api(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 API（内部方法）
        
        Args:
            action: 动作类型
            params: 动作参数
            
        Returns:
            API 响应结果
        """
        # 模拟模式：不发送真实请求，仅记录日志
        if self.mock_mode:
            logger.info(f"[模拟] 键鼠操作 - 动作: {action}, 参数: {params}")
            return {
                'status': 'success',
                'action': action,
                'params': params,
                'message': '模拟执行成功',
                'mock': True
            }
        
        # 真实模式：发送 HTTP 请求
        payload = {
            'action': action,
            'params': params
        }
        
        headers = {}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 调用失败: {e}")
            raise
    
    def _execute_with_retry(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """带重试的 API 调用
        
        Args:
            action: 动作类型
            params: 动作参数
            
        Returns:
            API 响应结果
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                result = self._call_api(action, params)
                
                # 更新统计
                duration = time.time() - start_time
                self.stats['total_calls'] += 1
                self.stats['successful_calls'] += 1
                if attempt > 1:
                    self.stats['total_retries'] += (attempt - 1)
                
                logger.debug(
                    f"键鼠操作成功 - 动作: {action}, "
                    f"耗时: {duration:.3f}s, 尝试: {attempt}"
                )
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"键鼠操作失败（尝试 {attempt}/{self.retry_attempts}）: {e}"
                )
                
                if attempt < self.retry_attempts:
                    # 指数回退延迟
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
        
        # 所有重试都失败
        self.stats['total_calls'] += 1
        self.stats['failed_calls'] += 1
        self.stats['total_retries'] += (self.retry_attempts - 1)
        
        logger.error(f"键鼠操作最终失败 - 动作: {action}, 错误: {last_error}")
        raise Exception(f"键鼠操作失败: {last_error}")
    
    def send_mouse_move(
        self,
        x: int,
        y: int,
        mode: str = "absolute"
    ) -> Dict[str, Any]:
        """发送鼠标移动指令
        
        Args:
            x: X 坐标
            y: Y 坐标
            mode: 移动模式 ("absolute" 绝对坐标, "relative" 相对移动)
            
        Returns:
            API 响应结果
        """
        params = {
            'x': x,
            'y': y,
            'mode': mode
        }
        return self._execute_with_retry('mouse_move', params)
    
    def send_mouse_click(
        self,
        button: str = "left",
        clicks: int = 1,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """发送鼠标点击指令
        
        Args:
            button: 按钮 ("left", "right", "middle")
            clicks: 点击次数（双击为 2）
            x: X 坐标（可选，如提供则先移动再点击）
            y: Y 坐标（可选）
            
        Returns:
            API 响应结果
        """
        # 如果提供坐标，先移动鼠标
        if x is not None and y is not None:
            self.send_mouse_move(x, y)
        
        params = {
            'button': button,
            'clicks': clicks
        }
        return self._execute_with_retry('mouse_click', params)
    
    def send_mouse_drag(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        button: str = "left"
    ) -> Dict[str, Any]:
        """发送鼠标拖拽指令
        
        Args:
            x1: 起始 X 坐标
            y1: 起始 Y 坐标
            x2: 结束 X 坐标
            y2: 结束 Y 坐标
            button: 拖拽按钮 ("left", "right")
            
        Returns:
            API 响应结果
        """
        params = {
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'button': button
        }
        return self._execute_with_retry('mouse_drag', params)
    
    def send_key_input(self, text: str) -> Dict[str, Any]:
        """发送文本输入指令
        
        Args:
            text: 要输入的文本
            
        Returns:
            API 响应结果
        """
        params = {
            'text': text
        }
        return self._execute_with_retry('key_input', params)
    
    def send_key_combination(self, keys: List[str]) -> Dict[str, Any]:
        """发送组合键指令
        
        Args:
            keys: 按键列表，如 ['CTRL', 'C'] 或 ['ALT', 'F4']
            
        Returns:
            API 响应结果
        """
        params = {
            'keys': keys
        }
        return self._execute_with_retry('key_combination', params)
    
    def send_key_press(self, key: str) -> Dict[str, Any]:
        """发送单键按下指令
        
        Args:
            key: 按键名称 (如 'ENTER', 'ESC', 'TAB', 'A', etc.)
            
        Returns:
            API 响应结果
        """
        params = {
            'key': key
        }
        return self._execute_with_retry('key_press', params)
    
    def send_key_down(self, key: str) -> Dict[str, Any]:
        """发送按键按下（持续）指令
        
        Args:
            key: 按键名称
            
        Returns:
            API 响应结果
        """
        params = {
            'key': key
        }
        return self._execute_with_retry('key_down', params)
    
    def send_key_up(self, key: str) -> Dict[str, Any]:
        """发送按键释放指令
        
        Args:
            key: 按键名称
            
        Returns:
            API 响应结果
        """
        params = {
            'key': key
        }
        return self._execute_with_retry('key_up', params)
    
    def send_scroll(
        self,
        dx: int = 0,
        dy: int = 0,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """发送鼠标滚轮指令
        
        Args:
            dx: 水平滚动量
            dy: 垂直滚动量（正数向上，负数向下）
            x: 滚动位置 X 坐标（可选）
            y: 滚动位置 Y 坐标（可选）
            
        Returns:
            API 响应结果
        """
        # 如果提供坐标，先移动鼠标
        if x is not None and y is not None:
            self.send_mouse_move(x, y)
        
        params = {
            'dx': dx,
            'dy': dy
        }
        return self._execute_with_retry('scroll', params)
    
    def wait(self, duration: float) -> None:
        """等待指定时间
        
        Args:
            duration: 等待时长（秒）
        """
        logger.debug(f"等待 {duration:.2f} 秒")
        time.sleep(duration)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.stats.copy()
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_retries': 0
        }
        logger.info("统计信息已重置")

