import os
import sys

# Makes core library available without extra installation steps
# 插入路径，使主库可得
sys.path.insert(0, './external/')
sys.path.insert(1, './')

# Custom
from gui.callbacks import GUIState

# 在Windows系统上修复模糊字体
if 'Windows' in os.environ.get('OS',''):
    # https://stackoverflow.com/a/43046744
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

if __name__ == '__main__':

    # 初始化GUI状态
    state = GUIState()

    # 开始事件循环
    state.event_loop()

    # 销毁GUI状态
    del state
    