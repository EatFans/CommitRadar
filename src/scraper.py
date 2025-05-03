# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import datetime
import re
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_scraper')

class GitHubCommitScraper:
    """GitHub 提交扫描器，通过网页抓取获取特定用户在特定日期的提交次数"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })
    
    def get_commits_for_date(self, username: str, date: str) -> Dict[str, Any]:
        """
        获取特定用户在特定日期的提交次数和详情
        
        Args:
            username: GitHub 用户名
            date: 要查询的日期 (YYYY-MM-DD 格式)
            
        Returns:
            包含用户名、日期、提交次数和提交详情的字典
        """
        # 首先尝试从贡献页面获取数据
        count = self.get_contributions_count(username, date)
        
        # 获取提交详情
        _, commits = self.get_commits_details(username, date)
        
        return {
            'username': username,
            'date': date,
            'count': count,
            'commits': commits
        }
    
    def get_commits_for_range(self, username: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        获取特定用户在日期范围内的提交数据
        
        Args:
            username: GitHub 用户名
            start_date: 开始日期 (YYYY-MM-DD 格式)
            end_date: 结束日期 (YYYY-MM-DD 格式)
            
        Returns:
            包含每天提交数据的列表
        """
        # 解析日期
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        
        # 确保开始日期不晚于结束日期
        if start > end:
            start, end = end, start
        
        # 计算日期范围
        date_range = (end - start).days + 1
        
        # 如果范围太大，给出警告
        if date_range > 31:
            logger.warning(f"日期范围较大 ({date_range} 天)，请求可能需要较长时间")
        
        results = []
        current = start
        
        # 遍历日期范围
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            logger.info(f"正在获取 {username} 在 {date_str} 的提交数据")
            
            try:
                # 获取当天的提交数据
                result = self.get_commits_for_date(username, date_str)
                results.append(result)
                
                # 添加延迟，避免请求过于频繁
                if current < end:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"获取 {date_str} 的数据时出错: {e}")
            
            # 移动到下一天
            current += datetime.timedelta(days=1)
        
        return results
    
    def get_commits_for_week(self, username: str, date: str) -> List[Dict[str, Any]]:
        """
        获取特定用户在指定日期所在周的提交数据
        
        Args:
            username: GitHub 用户名
            date: 周内任意一天 (YYYY-MM-DD 格式)
            
        Returns:
            包含一周提交数据的列表
        """
        # 解析日期
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        
        # 计算周一和周日
        weekday = date_obj.weekday()
        monday = date_obj - datetime.timedelta(days=weekday)
        sunday = monday + datetime.timedelta(days=6)
        
        # 获取一周的数据
        return self.get_commits_for_range(
            username, 
            monday.strftime('%Y-%m-%d'), 
            sunday.strftime('%Y-%m-%d')
        )
    
    def get_commits_for_month(self, username: str, year: int, month: int) -> List[Dict[str, Any]]:
        """
        获取特定用户在指定月份的提交数据
        
        Args:
            username: GitHub 用户名
            year: 年份
            month: 月份 (1-12)
            
        Returns:
            包含一个月提交数据的列表
        """
        # 计算月份的第一天和最后一天
        first_day = datetime.date(year, month, 1)
        
        # 计算下个月的第一天，然后减去一天
        if month == 12:
            last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        # 获取一个月的数据
        return self.get_commits_for_range(
            username, 
            first_day.strftime('%Y-%m-%d'), 
            last_day.strftime('%Y-%m-%d')
        )
    
    def get_contributions_count(self, username: str, date: str) -> int:
        """
        从GitHub贡献页面获取特定日期的提交次数
        
        Args:
            username: GitHub 用户名
            date: 要查询的日期 (YYYY-MM-DD 格式)
            
        Returns:
            该日期的提交次数
        """
        # 解析日期
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        
        # 构建贡献页面URL - 使用年份范围
        year = date_obj.year
        contributions_url = f"https://github.com/users/{username}/contributions?from={year}-01-01&to={year}-12-31"
        
        try:
            logger.info(f"正在请求: {contributions_url}")
            # 发送请求获取贡献页面
            response = self.session.get(contributions_url)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找特定日期的贡献数据
            target_date_str = date_obj.strftime('%Y-%m-%d')
            logger.info(f"正在查找日期: {target_date_str}")
            
            # 尝试多种方法获取贡献数
            
            # 1. 从工具提示文本中提取
            tooltip_pattern = f"{date_obj.day} contributions on {date_obj.strftime('%b')} {date_obj.day}"
            html_text = response.text
            tooltip_index = html_text.find(tooltip_pattern)
            
            if tooltip_index != -1:
                # 提取数字
                tooltip_text = html_text[max(0, tooltip_index-20):min(len(html_text), tooltip_index+50)]
                count_match = re.search(r'(\d+)\s+contribution', tooltip_text)
                if count_match:
                    count = int(count_match.group(1))
                    logger.info(f"从工具提示文本中找到提交次数: {count}")
                    return count
            
            # 2. 从日历单元格中提取
            day_cells = soup.select('td.ContributionCalendar-day')
            for cell in day_cells:
                if cell.get('data-date') == target_date_str:
                    count_text = cell.get('data-count') or cell.get('data-level') or '0'
                    count = int(count_text)
                    logger.info(f"从日历单元格中找到提交次数: {count}")
                    return count
            
            # 3. 从SVG元素中提取
            svg_cells = soup.select('rect.ContributionCalendar-day')
            for cell in svg_cells:
                if cell.get('data-date') == target_date_str:
                    count = int(cell.get('data-count') or cell.get('data-level') or '0')
                    logger.info(f"从SVG元素中找到提交次数: {count}")
                    return count
            
            # 4. 直接在HTML中搜索data-date和data-count属性
            date_attr = f'data-date="{target_date_str}"'
            date_index = html_text.find(date_attr)
            if date_index != -1:
                search_range = html_text[max(0, date_index-100):min(len(html_text), date_index+100)]
                count_match = re.search(r'data-count="(\d+)"', search_range)
                if count_match:
                    count = int(count_match.group(1))
                    logger.info(f"从data-count属性中找到提交次数: {count}")
                    return count
            
            # 如果所有方法都失败，尝试使用搜索页面
            logger.warning(f"无法从贡献页面找到日期 {target_date_str} 的数据，尝试使用搜索页面")
            count, _ = self.get_commits_details(username, date)
            return count
            
        except Exception as e:
            logger.error(f"获取贡献数据时出错: {e}")
            # 尝试使用搜索页面作为备选方案
            try:
                count, _ = self.get_commits_details(username, date)
                return count
            except:
                return 0
    
    def get_commits_details(self, username: str, date: str) -> Tuple[int, List[Dict[str, Any]]]:
        """
        使用GitHub搜索页面获取提交详情
        
        Args:
            username: GitHub 用户名
            date: 要查询的日期 (YYYY-MM-DD 格式)
            
        Returns:
            提交次数和提交详情列表
        """
        # 构建 GitHub 搜索 URL
        search_url = f"https://github.com/search?q=author%3A{username}+committer-date%3A{date}&type=commits"
        
        try:
            logger.info(f"正在请求: {search_url}")
            # 发送请求获取搜索页面
            response = self.session.get(search_url)
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找提交计数信息
            count_text = soup.select_one('.codesearch-results h3')
            if not count_text:
                return 0, []
            
            # 提取提交数量
            count_match = re.search(r'(\d+)', count_text.text)
            count = int(count_match.group(1)) if count_match else 0
            
            # 提取提交详情
            commits = []
            commit_items = soup.select('.commit-list-item')
            
            for item in commit_items:
                repo_name = item.select_one('.f4 a')
                commit_title = item.select_one('.commit-title a')
                commit_time = item.select_one('relative-time')
                
                if repo_name and commit_title and commit_time:
                    commits.append({
                        'repo': repo_name.text.strip(),
                        'title': commit_title.text.strip(),
                        'url': 'https://github.com' + commit_title['href'] if commit_title.has_attr('href') else '',
                        'time': commit_time.text.strip()
                    })
            
            return count, commits
            
        except Exception as e:
            logger.error(f"获取提交详情时出错: {e}")
            return 0, []