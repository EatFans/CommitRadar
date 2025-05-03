import requests
import datetime
import argparse
from typing import Dict, Any, Optional


class GitHubCommitRadar:
    """GitHub 提交扫描器，用于获取特定用户在特定日期的提交次数"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 GitHub 提交扫描器
        
        Args:
            token: GitHub 个人访问令牌（可选，但推荐使用以避免 API 速率限制）
        """
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def get_commits_count(self, username: str, date: datetime.date) -> int:
        """
        获取特定用户在特定日期的提交次数
        
        Args:
            username: GitHub 用户名
            date: 要查询的日期
            
        Returns:
            该日期的提交次数
        """
        # 格式化日期为 YYYY-MM-DD 格式
        date_str = date.strftime("%Y-%m-%d")
        
        # 构建查询参数
        # 查询格式: author:username committer-date:YYYY-MM-DD
        query = f"author:{username} committer-date:{date_str}"
        
        # 发送请求
        response = self._search_commits(query)
        
        # 返回提交次数
        return response.get("total_count", 0)
    
    def _search_commits(self, query: str) -> Dict[str, Any]:
        """
        使用 GitHub Search API 搜索提交
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            API 响应的 JSON 数据
        """
        url = f"{self.BASE_URL}/search/commits"
        params = {"q": query}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"错误: {response.status_code}")
            print(response.json())
            return {"total_count": 0}
        
        return response.json()


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="获取 GitHub 用户在特定日期的提交次数")
    parser.add_argument("username", help="GitHub 用户名")
    parser.add_argument("--date", help="要查询的日期 (YYYY-MM-DD 格式，默认为今天)", default=None)
    parser.add_argument("--token", help="GitHub 个人访问令牌", default=None)
    
    args = parser.parse_args()
    
    # 解析日期
    if args.date:
        try:
            date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("错误: 日期格式无效，请使用 YYYY-MM-DD 格式")
            return
    else:
        date = datetime.date.today()
    
    # 创建扫描器实例
    radar = GitHubCommitRadar(token=args.token)
    
    # 获取提交次数
    count = radar.get_commits_count(args.username, date)
    
    # 输出结果
    print(f"用户 {args.username} 在 {date} 的提交次数: {count}")


if __name__ == "__main__":
    main()