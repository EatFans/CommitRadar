# -*- coding: utf-8 -*-
"""
工具函数模块，提供各种辅助功能
"""
import os
import datetime
from typing import Dict, Any, List, Optional

def format_date(date_str: str, format_str: str = '%Y-%m-%d') -> str:
    """
    格式化日期字符串
    
    Args:
        date_str: 原始日期字符串
        format_str: 目标格式
        
    Returns:
        格式化后的日期字符串
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime(format_str)
    except ValueError:
        return date_str

def get_template_path(template_name: str) -> str:
    """
    获取模板文件的绝对路径
    
    Args:
        template_name: 模板文件名
        
    Returns:
        模板文件的绝对路径
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'resources', 'templates')
    return os.path.join(template_dir, template_name)

def ensure_dir_exists(directory: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def format_commit_count(count: int) -> str:
    """
    格式化提交次数，添加适当的单位
    
    Args:
        count: 提交次数
        
    Returns:
        格式化后的字符串
    """
    if count == 0:
        return "无提交"
    elif count == 1:
        return "1次提交"
    else:
        return f"{count}次提交"