# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_file
import os
import datetime
import logging
from typing import Dict, Any, List

from .scraper import GitHubCommitScraper
from .exporters import CommitDataExporter
from .hooks import CommitHooks

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# 创建Flask应用
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'static')
)

# 初始化钩子系统
hooks = CommitHooks()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/batch')
def batch():
    """批量查询页面"""
    return render_template('batch.html')

@app.route('/api/commits', methods=['POST'])
def get_commits():
    """获取单日提交数据"""
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
    
    # 获取提交数据
    scraper = GitHubCommitScraper()
    result = scraper.get_commits_for_date(username, date)
    
    # 运行钩子
    try:
        hooks.run_hooks([result])
    except Exception as e:
        logger.error(f"运行钩子时出错: {e}")
    
    return jsonify(result)

@app.route('/api/batch-commits', methods=['POST'])
def batch_commits():
    """批量获取提交数据"""
    data = request.json
    username = data.get('username')
    mode = data.get('mode', 'range')  # range, week, month
    
    if not username:
        return jsonify({'error': '用户名是必需的'}), 400
    
    scraper = GitHubCommitScraper()
    results = []
    
    try:
        if mode == 'range':
            # 日期范围模式
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            
            if not start_date or not end_date:
                return jsonify({'error': '开始日期和结束日期都是必需的'}), 400
            
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            results = scraper.get_commits_for_range(username, start_date, end_date)
            
        elif mode == 'week':
            # 周模式
            date = data.get('date')
            
            if not date:
                return jsonify({'error': '日期是必需的'}), 400
            
            # 验证日期格式
            datetime.datetime.strptime(date, '%Y-%m-%d')
            
            results = scraper.get_commits_for_week(username, date)
            
        elif mode == 'month':
            # 月模式
            year = data.get('year')
            month = data.get('month')
            
            if not year or not month:
                return jsonify({'error': '年份和月份都是必需的'}), 400
            
            results = scraper.get_commits_for_month(username, int(year), int(month))
            
        else:
            return jsonify({'error': '无效的模式'}), 400
        
        # 运行钩子
        try:
            hooks.run_hooks(results)
        except Exception as e:
            logger.error(f"运行钩子时出错: {e}")
        
        return jsonify({
            'username': username,
            'mode': mode,
            'results': results,
            'total_commits': sum(day['count'] for day in results)
        })
        
    except Exception as e:
        logger.error(f"批量获取提交数据时出错: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    """导出提交数据"""
    data = request.json
    results = data.get('results', [])
    format_type = data.get('format', 'excel')  # excel, csv, json
    
    if not results:
        return jsonify({'error': '没有数据可导出'}), 400
    
    exporter = CommitDataExporter()
    
    try:
        if format_type == 'excel':
            filepath = exporter.export_to_excel(results)
        elif format_type == 'csv':
            filepath = exporter.export_to_csv(results)
        elif format_type == 'json':
            filepath = exporter.export_to_json(results)
        else:
            return jsonify({'error': '无效的导出格式'}), 400
        
        # 返回文件下载URL
        filename = os.path.basename(filepath)
        download_url = f"/api/download/{filename}"
        
        return jsonify({
            'success': True,
            'message': f'数据已导出为{format_type.upper()}格式',
            'download_url': download_url
        })
        
    except Exception as e:
        logger.error(f"导出数据时出错: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载导出的文件"""
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    return send_file(os.path.join(export_dir, filename), as_attachment=True)

@app.route('/api/hooks', methods=['GET'])
def list_hooks():
    """列出所有可用的钩子"""
    return jsonify({
        'hooks': list(hooks.hooks.keys())
    })

@app.route('/api/hooks/create-example', methods=['POST'])
def create_example_hook():
    """创建示例钩子"""
    try:
        hook_path = hooks.create_example_hook()
        hooks.load_hooks()  # 重新加载钩子
        return jsonify({
            'success': True,
            'message': '示例钩子已创建',
            'path': hook_path
        })
    except Exception as e:
        logger.error(f"创建示例钩子时出错: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hooks/run', methods=['POST'])
def run_hook():
    """运行特定钩子"""
    data = request.json
    hook_name = data.get('hook')
    commit_data = data.get('data', [])
    
    if not hook_name:
        return jsonify({'error': '钩子名称是必需的'}), 400
    
    if not commit_data:
        return jsonify({'error': '没有提供提交数据'}), 400
    
    success = hooks.run_specific_hook(hook_name, commit_data)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'钩子 {hook_name} 已成功运行'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'运行钩子 {hook_name} 失败'
        }), 500

@app.route('/api/hooks/reload', methods=['POST'])
def reload_hooks():
    """重新加载所有钩子"""
    try:
        hooks.load_hooks()
        return jsonify({
            'success': True,
            'message': '所有钩子已重新加载',
            'hooks': list(hooks.hooks.keys())
        })
    except Exception as e:
        logger.error(f"重新加载钩子时出错: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/stats', methods=['POST'])
def get_stats():
    """获取提交统计信息"""
    data = request.json
    results = data.get('results', [])
    
    if not results:
        return jsonify({'error': '没有数据可分析'}), 400
    
    # 计算统计信息
    total_commits = sum(day['count'] for day in results)
    avg_commits = total_commits / len(results) if results else 0
    
    # 找出提交最多的日期
    max_day = max(results, key=lambda x: x['count']) if results else None
    
    # 找出连续提交的最长天数
    current_streak = 0
    max_streak = 0
    
    for day in results:
        if day['count'] > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    # 按星期几分组
    weekday_stats = {i: 0 for i in range(7)}  # 0=周一, 6=周日
    
    for day in results:
        date_obj = datetime.datetime.strptime(day['date'], '%Y-%m-%d')
        weekday = date_obj.weekday()
        weekday_stats[weekday] += day['count']
    
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_data = [{'day': weekday_names[i], 'count': weekday_stats[i]} for i in range(7)]
    
    return jsonify({
        'total_commits': total_commits,
        'average_commits': round(avg_commits, 2),
        'max_day': max_day,
        'max_streak': max_streak,
        'weekday_stats': weekday_data
    })

@app.errorhandler(404)
def page_not_found(e):
    """处理404错误"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """处理500错误"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 确保导出目录存在
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # 创建示例钩子
    if not os.listdir(hooks.hooks_dir):
        hooks.create_example_hook()
        hooks.load_hooks()
    
    # 启动应用
    app.run(debug=True)