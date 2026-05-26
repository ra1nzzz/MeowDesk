"""
动画管理器
"""

import os
from typing import Dict, List, Optional
from PIL import Image


class AnimationManager:
    """APNG 动画管理器"""
    
    # 状态常量
    IDLE = 0
    HOVER = 1
    RECEIVING = 2
    CARRYING = 3
    HAPPY = 4
    SLEEPING = 5
    SHY = 6
    SURPRISED = 7
    
    # 状态对应的文件
    STATE_FILES = {
        IDLE: 'idle.apng',
        HOVER: 'idle.apng',
        RECEIVING: 'receiving.apng',
        CARRYING: 'receiving.apng',
        HAPPY: 'happy.apng',
        SLEEPING: 'sleeping.apng',
        SHY: 'shy.apng',
        SURPRISED: 'surprised.apng',
    }
    
    def __init__(self, assets_dir: str, scale: float = 0.5):
        self.assets_dir = assets_dir
        self.scale = scale
        self.frames_cache: Dict[int, List[Image.Image]] = {}
        self.durations_cache: Dict[int, List[int]] = {}
        
        # 预加载所有动画
        self._preload_all()
    
    def _preload_all(self):
        """预加载所有动画"""
        for state, filename in self.STATE_FILES.items():
            filepath = os.path.join(self.assets_dir, filename)
            if os.path.exists(filepath):
                self._load_apng(state, filepath)
    
    def _load_apng(self, state: int, filepath: str):
        """加载 APNG 文件"""
        try:
            img = Image.open(filepath)
            frames = []
            durations = []
            
            # 提取所有帧
            frame_index = 0
            while True:
                try:
                    # 复制当前帧
                    frame = img.copy().convert('RGBA')
                    
                    # 缩放
                    if self.scale != 1.0:
                        new_size = (
                            int(frame.width * self.scale),
                            int(frame.height * self.scale)
                        )
                        frame = frame.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # 预乘 alpha：消除 ULW (AC_SRC_ALPHA) 下的白色边缘锯齿
                    # 必须在 resize 之后做，否则插值会破坏预乘关系
                    frame = self._premultiply_alpha(frame)
                    
                    frames.append(frame)
                    
                    # 获取帧延迟（毫秒）
                    duration = img.info.get('duration', 100)
                    durations.append(duration)
                    
                    # 移动到下一帧
                    frame_index += 1
                    img.seek(frame_index)
                    
                except EOFError:
                    break  # 到达最后一帧
                except Exception as e:
                    print(f"加载帧 {frame_index} 失败: {e}")
                    break
            
            if frames:
                self.frames_cache[state] = frames
                self.durations_cache[state] = durations
            else:
                raise ValueError("没有加载到任何帧")
            
        except Exception as e:
            print(f"加载动画失败 {filepath}: {e}")
            # 创建默认帧
            self.frames_cache[state] = [self._create_default_frame()]
            self.durations_cache[state] = [100]
    
    @staticmethod
    def _premultiply_alpha(image: Image.Image) -> Image.Image:
        """预乘 alpha 通道，消除 ULW 渲染时的白色边缘"""
        from PIL import ImageMath
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        r, g, b, a = image.split()
        r = ImageMath.unsafe_eval('convert(R * A / 255, "I")', R=r, A=a).convert('L')
        g = ImageMath.unsafe_eval('convert(G * A / 255, "I")', G=g, A=a).convert('L')
        b = ImageMath.unsafe_eval('convert(B * A / 255, "I")', B=b, A=a).convert('L')
        return Image.merge("RGBA", (r, g, b, a))
    
    def _create_default_frame(self) -> Image.Image:
        """创建默认帧（纯色方块）"""
        size = int(128 * self.scale)
        img = Image.new('RGBA', (size, size), (100, 100, 100, 200))
        return img
    
    def get_frame(self, state: int, frame_index: int) -> Optional[Image.Image]:
        """获取指定状态的指定帧"""
        frames = self.frames_cache.get(state, [])
        if not frames:
            return None
        
        # 循环索引
        index = frame_index % len(frames)
        return frames[index]
    
    def get_frame_count(self, state: int) -> int:
        """获取指定状态的帧数"""
        return len(self.frames_cache.get(state, []))
    
    def get_frame_duration(self, state: int, frame_index: int) -> int:
        """获取指定帧的延迟时间（毫秒）"""
        durations = self.durations_cache.get(state, [100])
        if not durations:
            return 100
        
        index = frame_index % len(durations)
        return durations[index]
    
    def get_frame_size(self, state: int) -> tuple:
        """获取帧的尺寸"""
        frames = self.frames_cache.get(state, [])
        if frames:
            return frames[0].size
        return (int(128 * self.scale), int(128 * self.scale))
