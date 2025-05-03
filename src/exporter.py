import pandas as pd
from typing import List, Dict, Any, Optional
import os
import datetime


class CommitDataExporter:
    """提交数据导出工具，支持导出为Excel等格式"""
    
    def __init__(self, export_dir: str = 'exports'):
        """
        初始化导出工具
        
        Args:
            export_dir: 导出文件保存目录
        """
        self.export_dir = export_dir
        # 确保导出目录存在
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_excel(self, data: List[Dict[str, Any]], username: str, 
                        filename: Optional[str] = None) -> str:
        """
        将提交数据导出为Excel文件
        
        Args:
            data: 提交数据列表
            username: GitHub用户名
            filename: 自定义文件名（可选）
            
        Returns:
            导出文件的路径
        """
        # 如果没有提供文件名，生成默认文件名
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{username}_commits_{timestamp}.xlsx"
        
        # 确保文件名有.xlsx后缀
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        # 完整文件路径
        file_path = os.path.join(self.export_dir, filename)
        
        # 准备数据
        # 1. 提交汇总数据
        summary_data = []
        for day_data in data:
            summary_data.append({
                '日期': day_data['date'],
                '提交次数': day_data['count']
            })
        
        # 2. 提交详情数据
        details_data = []
        for day_data in data:
            date = day_data['date']
            for commit in day_data['commits']:
                details_data.append({
                    '日期': date,
                    '仓库': commit['repo'],
                    '提交标题': commit['title'],
                    '提交时间': commit['time'],
                    '提交URL': commit['url']
                })
        
        # 创建Excel写入器
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 写入汇总表
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='提交汇总', index=False)
            
            # 写入详情表
            if details_data:
                details_df = pd.DataFrame(details_data)
                details_df.to_excel(writer, sheet_name='提交详情', index=False)
        
        return file_path
    
    def export_to_csv(self, data: List[Dict[str, Any]], username: str, 
                      filename: Optional[str] = None) -> str:
        """
        将提交数据导出为CSV文件
        
        Args:
            data: 提交数据列表
            username: GitHub用户名
            filename: 自定义文件名（可选）
            
        Returns:
            导出文件的路径
        """
        # 如果没有提供文件名，生成默认文件名
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{username}_commits_{timestamp}.csv"
        
        # 确保文件名有.csv后缀
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 完整文件路径
        file_path = os.path.join(self.export_dir, filename)
        
        # 准备数据
        summary_data = []
        for day_data in data:
            summary_data.append({
                '日期': day_data['date'],
                '提交次数': day_data['count'],
                '提交详情': ', '.join([f"{c['repo']}: {c['title']}" for c in day_data['commits']])
            })
        
        # 创建DataFrame并导出
        df = pd.DataFrame(summary_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # 使用带BOM的UTF-8编码，以便Excel正确显示中文
        
        return file_path