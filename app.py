from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import datetime
import re
import os
import json
from flask import send_file

app = Flask(__name__)

class GitHubCommitScraper:
    """GitHub 提交扫描器，通过网页抓取获取特定用户在特定日期的提交次数"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })
    
    def get_commits_count(self, username, date):
        """
        获取特定用户在特定日期的提交次数
        
        Args:
            username: GitHub 用户名
            date: 要查询的日期 (YYYY-MM-DD 格式)
            
        Returns:
            该日期的提交次数和提交详情列表
        """
        # 首先尝试从贡献页面获取数据
        count = self.get_contributions_count(username, date)
        if count > 0:
            # 如果找到贡献，再尝试获取详细信息
            _, commits = self.get_commits_details(username, date)
            return count, commits
        
        # 如果贡献页面没有数据，尝试搜索页面
        return self.get_commits_details(username, date)
    
    def get_contributions_count(self, username, date):
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
            print(f"正在请求: {contributions_url}")
            # 发送请求获取贡献页面
            response = self.session.get(contributions_url)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找特定日期的贡献数据
            target_date_str = date_obj.strftime('%Y-%m-%d')
            print(f"正在查找日期: {target_date_str}")
            
            # 首先尝试直接从工具提示文本中提取贡献数
            # 这是最准确的方法，因为它与用户在界面上看到的一致
            tooltip_texts = soup.select('tool-tip')
            for tooltip in tooltip_texts:
                tooltip_text = tooltip.text
                if f"on {date_obj.strftime('%b')} {date_obj.day}" in tooltip_text or f"on {date_obj.strftime('%B')} {date_obj.day}" in tooltip_text:
                    # 提取数字
                    count_match = re.search(r'(\d+)\s+contribution', tooltip_text)
                    if count_match:
                        count = int(count_match.group(1))
                        print(f"从工具提示中找到提交次数: {count}")
                        return count
            
            # 如果没有找到工具提示，尝试从图像中提取
            # 查找包含日期的单元格
            day_cells = soup.select('td.ContributionCalendar-day')
            for cell in day_cells:
                if cell.get('data-date') == target_date_str:
                    # 获取提交次数
                    count_text = cell.get('data-count') or cell.get('data-level') or '0'
                    count = int(count_text)
                    print(f"从日历单元格中找到提交次数: {count}")
                    return count
            
            # 如果仍然找不到，尝试解析HTML文本
            html_text = response.text
            
            # 1. 查找包含日期和贡献数的工具提示文本
            month_name = date_obj.strftime('%B')  # 完整月份名称
            short_month = date_obj.strftime('%b')  # 缩写月份名称
            day_num = date_obj.day
            
            # 尝试多种格式的日期表示
            date_patterns = [
                f"{month_name} {day_num}, {year}",
                f"{short_month} {day_num}, {year}",
                f"{month_name} {day_num}",
                f"{short_month} {day_num}"
            ]
            
            for pattern in date_patterns:
                # 查找包含日期的文本
                pattern_index = html_text.find(pattern)
                if pattern_index != -1:
                    # 在日期前后200个字符范围内查找贡献数
                    search_range = html_text[max(0, pattern_index-100):min(len(html_text), pattern_index+100)]
                    count_match = re.search(r'(\d+)\s+contribution', search_range)
                    if count_match:
                        count = int(count_match.group(1))
                        print(f"从HTML文本中找到提交次数: {count}")
                        return count
            
            # 2. 查找data-date和data-count属性
            date_attr = f'data-date="{target_date_str}"'
            date_index = html_text.find(date_attr)
            if date_index != -1:
                # 在日期属性前后150个字符范围内查找data-count
                search_range = html_text[max(0, date_index-100):min(len(html_text), date_index+100)]
                count_match = re.search(r'data-count="(\d+)"', search_range)
                if count_match:
                    count = int(count_match.group(1))
                    print(f"从data-count属性中找到提交次数: {count}")
                    return count
            
            # 3. 尝试查找包含日期的SVG元素
            svg_cells = soup.select('rect.ContributionCalendar-day')
            for cell in svg_cells:
                if cell.get('data-date') == target_date_str:
                    count = int(cell.get('data-count') or cell.get('data-level') or '0')
                    print(f"从SVG元素中找到提交次数: {count}")
                    return count
            
            # 如果所有方法都失败，尝试使用搜索页面
            print(f"无法从贡献页面找到日期 {target_date_str} 的数据，尝试使用搜索页面")
            
            # 尝试直接解析第一张图片中显示的那种工具提示
            tooltip_pattern = f"{day_num} contributions on {short_month} {day_num}"
            tooltip_index = html_text.find(tooltip_pattern)
            if tooltip_index != -1:
                # 提取数字
                tooltip_text = html_text[max(0, tooltip_index-20):min(len(html_text), tooltip_index+20)]
                count_match = re.search(r'(\d+)\s+contribution', tooltip_text)
                if count_match:
                    count = int(count_match.group(1))
                    print(f"从工具提示文本中找到提交次数: {count}")
                    return count
            
            return 0
            
        except Exception as e:
            print(f"获取贡献数据时出错: {e}")
            # 保存HTML用于调试
            try:
                with open('debug_contributions.html', 'w', encoding='utf-8') as f:
                    f.write(response.text if 'response' in locals() else "请求失败，无HTML内容")
                print("已保存调试HTML到debug_contributions.html")
            except:
                pass
            return 0
    
    def get_commits_details(self, username, date):
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
            print(f"错误: {e}")
            return 0, []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/commits', methods=['POST'])
def get_commits():
    data = request.json
    username = data.get('username')
    date = data.get('date')
    
    if not username or not date:
        return jsonify({'error': '用户名和日期都是必需的'}), 400
    
    try:
        # 验证日期格式
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': '日期格式无效，请使用 YYYY-MM-DD 格式'}), 400
    
    scraper = GitHubCommitScraper()
    count, commits = scraper.get_commits_count(username, date)
    
    return jsonify({
        'username': username,
        'date': date,
        'count': count,
        'commits': commits
    })


@app.route('/api/test-parse', methods=['POST'])
def test_parse():
    """测试路由，用于直接解析提供的HTML"""
    data = request.json
    html_content = data.get('html')
    target_date = data.get('date')
    
    if not html_content or not target_date:
        return jsonify({'error': 'HTML内容和日期都是必需的'}), 400
    
    try:
        # 验证日期格式
        datetime.datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': '日期格式无效，请使用 YYYY-MM-DD 格式'}), 400
    
    scraper = GitHubCommitScraper()
    count = scraper.parse_contributions_html(html_content, target_date)
    
    return jsonify({
        'date': target_date,
        'count': count
    })


@app.route('/api/export-json', methods=['POST'])
def export_json():
    """导出提交数据为JSON文件"""
    data = request.json
    commit_data = data.get('data')
    custom_path = data.get('path')
    
    if not commit_data:
        return jsonify({'error': '没有提供数据'}), 400
    
    try:
        # 创建导出目录
        export_dir = os.path.join(app.root_path, 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        # 生成文件名
        username = commit_data.get('username', 'user')
        date = commit_data.get('date', 'date')
        default_filename = f"commits_{username}_{date}.json"
        
        # 处理自定义路径
        if custom_path:
            # 确保路径安全，防止目录遍历攻击
            custom_path = os.path.normpath(custom_path)
            if custom_path.startswith('/') or '..' in custom_path:
                return jsonify({'error': '无效的文件路径'}), 400
                
            # 如果只提供了目录，添加默认文件名
            if not custom_path.endswith('.json'):
                if not os.path.splitext(custom_path)[1]:
                    if not custom_path.endswith('/'):
                        custom_path += '/'
                    custom_path += default_filename
                else:
                    # 确保扩展名为.json
                    custom_path = os.path.splitext(custom_path)[0] + '.json'
            
            # 创建自定义目录（如果需要）
            custom_dir = os.path.dirname(custom_path)
            if custom_dir:
                full_dir_path = os.path.join(export_dir, custom_dir)
                if not os.path.exists(full_dir_path):
                    os.makedirs(full_dir_path)
            
            filepath = os.path.join(export_dir, custom_path)
            filename = os.path.basename(custom_path)
        else:
            filepath = os.path.join(export_dir, default_filename)
            filename = default_filename
        
        # 写入JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(commit_data, f, ensure_ascii=False, indent=2)
        
        # 生成下载URL
        download_url = f"/exports/{os.path.relpath(filepath, export_dir)}"
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'filename': filename,
            'download_url': download_url
        })
    
    except Exception as e:
        logger.error(f"导出JSON时出错: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

# 添加静态文件路由
@app.route('/exports/<path:filename>')
def download_file(filename):
    """下载导出的文件"""
    return send_file(os.path.join(app.root_path, 'exports', filename), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)


def parse_contributions_html(self, html_content, target_date):
    """
    直接解析提供的HTML内容，获取特定日期的提交次数
    
    Args:
        html_content: GitHub贡献页面的HTML内容
        target_date: 目标日期 (YYYY-MM-DD 格式)
        
    Returns:
        该日期的提交次数
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 首先尝试获取总贡献数
        contributions_header = soup.select_one('.js-yearly-contributions h2')
        if contributions_header:
            total_match = re.search(r'(\d+)\s+contributions', contributions_header.text)
            if total_match:
                print(f"总贡献数: {total_match.group(1)}")
        
        # 直接使用CSS选择器查找特定日期的单元格
        day_cell = soup.select_one(f'td[data-date="{target_date}"]')
        if day_cell:
            count = day_cell.get('data-count') or day_cell.get('data-level') or '0'
            return int(count)
        
        # 如果没有找到，尝试使用更通用的选择器
        all_day_cells = soup.select('td.ContributionCalendar-day, rect.ContributionCalendar-day')
        for cell in all_day_cells:
            if cell.get('data-date') == target_date:
                count = cell.get('data-count') or cell.get('data-level') or '0'
                return int(count)
        
        # 如果仍然找不到，尝试在HTML文本中直接搜索
        date_pattern = f'data-date="{target_date}"'
        date_index = html_content.find(date_pattern)
        
        if date_index != -1:
            # 在找到的日期附近查找data-count属性
            count_pattern = r'data-count="(\d+)"'
            # 在日期前后300个字符范围内查找
            search_range = html_content[max(0, date_index-150):min(len(html_content), date_index+150)]
            count_match = re.search(count_pattern, search_range)
            if count_match:
                return int(count_match.group(1))
            
            # 如果没有找到data-count，尝试查找data-level
            level_pattern = r'data-level="(\d+)"'
            level_match = re.search(level_pattern, search_range)
            if level_match:
                return int(level_match.group(1))
        
        # 记录调试信息
        print(f"无法找到日期 {target_date} 的贡献数据")
        
        return 0
        
    except Exception as e:
        print(f"解析HTML时出错: {e}")
        return 0