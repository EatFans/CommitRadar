from typing import Dict, Any, List, Callable, Optional
import importlib.util
import os
import sys


class CommitHooks:
    """提交数据处理钩子，允许用户自定义处理逻辑"""
    
    def __init__(self, hooks_dir: str = 'hooks'):
        """
        初始化钩子管理器
        
        Args:
            hooks_dir: 钩子脚本目录
        """
        self.hooks_dir = hooks_dir
        self.hooks = {}
        
        # 确保钩子目录存在
        os.makedirs(hooks_dir, exist_ok=True)
        
        # 加载所有钩子
        self.load_hooks()
    
    def load_hooks(self) -> None:
        """加载钩子目录中的所有Python脚本"""
        # 清空现有钩子
        self.hooks = {}
        
        # 检查目录是否存在
        if not os.path.exists(self.hooks_dir):
            return
        
        # 遍历目录中的所有Python文件
        for filename in os.listdir(self.hooks_dir):
            if filename.endswith('.py'):
                hook_name = os.path.splitext(filename)[0]
                hook_path = os.path.join(self.hooks_dir, filename)
                
                try:
                    # 动态加载模块
                    spec = importlib.util.spec_from_file_location(hook_name, hook_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 检查模块是否有process_commits函数
                        if hasattr(module, 'process_commits'):
                            self.hooks[hook_name] = module.process_commits
                            print(f"已加载钩子: {hook_name}")
                except Exception as e:
                    print(f"加载钩子 {hook_name} 时出错: {e}")
    
    def run_hooks(self, commit_data: List[Dict[str, Any]]) -> None:
        """
        运行所有已加载的钩子
        
        Args:
            commit_data: 提交数据列表
        """
        for hook_name, hook_func in self.hooks.items():
            try:
                print(f"运行钩子: {hook_name}")
                hook_func(commit_data)
            except Exception as e:
                print(f"运行钩子 {hook_name} 时出错: {e}")
    
    def run_specific_hook(self, hook_name: str, commit_data: List[Dict[str, Any]]) -> bool:
        """
        运行特定的钩子
        
        Args:
            hook_name: 钩子名称
            commit_data: 提交数据列表
            
        Returns:
            是否成功运行钩子
        """
        if hook_name in self.hooks:
            try:
                self.hooks[hook_name](commit_data)
                return True
            except Exception as e:
                print(f"运行钩子 {hook_name} 时出错: {e}")
                return False
        else:
            print(f"钩子 {hook_name} 不存在")
            return False
    
    def create_example_hook(self) -> str:
        """
        创建示例钩子脚本
        
        Returns:
            创建的钩子文件路径
        """
        example_hook_path = os.path.join(self.hooks_dir, 'example_hook.py')
        
        with open(example_hook_path, 'w', encoding='utf-8') as f:
            f.write('''# 示例钩子脚本
# 当获取到提交数据后，此函数将被自动调用

def process_commits(commit_data):
    """
    处理提交数据的钩子函数
    
    Args:
        commit_data: 包含提交信息的列表，每个元素是一个字典，包含date、count和commits字段
    """
    print("示例钩子被触发!")
    
    # 计算总提交次数
    total_commits = sum(day['count'] for day in commit_data)
    print(f"总提交次数: {total_commits}")
    
    # 找出提交最多的日期
    if commit_data:
        max_day = max(commit_data, key=lambda x: x['count'])
        print(f"提交最多的日期: {max_day['date']}, 提交次数: {max_day['count']}")
    
    # 你可以在这里添加自己的逻辑
    # 例如：发送通知、更新数据库、触发其他脚本等
    
    # 示例：如果某天提交超过5次，打印提醒
    for day in commit_data:
        if day['count'] >= 5:
            print(f"注意: {day['date']} 有 {day['count']} 次提交，可能需要关注!")
    
    return True  # 返回True表示处理成功
''')
        
        return example_hook_path