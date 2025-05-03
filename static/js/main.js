document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期为今天
    const today = new Date();
    const dateInput = document.getElementById('date');
    dateInput.value = formatDate(today);
    
    // 绑定搜索按钮点击事件
    const searchBtn = document.getElementById('search-btn');
    searchBtn.addEventListener('click', searchCommits);
    
    // 绑定回车键搜索
    document.getElementById('username').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCommits();
        }
    });
    
    document.getElementById('date').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCommits();
        }
    });
});

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 搜索提交记录
function searchCommits() {
    const username = document.getElementById('username').value.trim();
    const date = document.getElementById('date').value;
    
    // 验证输入
    if (!username) {
        showError('请输入GitHub用户名');
        return;
    }
    
    if (!date) {
        showError('请选择日期');
        return;
    }
    
    // 显示加载状态
    showLoading();
    
    // 发送API请求
    fetch('/api/commits', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            date: date
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || '请求失败');
            });
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        displayResults(data);
    })
    .catch(error => {
        hideLoading();
        showError(error.message);
    });
}

// 显示结果
function displayResults(data) {
    // 更新结果区域
    document.getElementById('result-username').textContent = data.username;
    document.getElementById('result-date').textContent = data.date;
    document.getElementById('commit-count').textContent = data.count;
    
    // 清空并填充提交详情
    const commitsContainer = document.getElementById('commits-container');
    commitsContainer.innerHTML = '';
    
    if (data.commits && data.commits.length > 0) {
        data.commits.forEach(commit => {
            const commitItem = document.createElement('div');
            commitItem.className = 'commit-item';
            
            const title = document.createElement('h4');
            title.textContent = commit.title;
            
            const repo = document.createElement('p');
            repo.textContent = `仓库: ${commit.repo}`;
            
            const meta = document.createElement('div');
            meta.className = 'commit-meta';
            
            const time = document.createElement('span');
            time.textContent = `提交时间: ${commit.time}`;
            
            const link = document.createElement('a');
            link.href = commit.url;
            link.textContent = '查看详情';
            link.target = '_blank';
            
            meta.appendChild(time);
            meta.appendChild(link);
            
            commitItem.appendChild(title);
            commitItem.appendChild(repo);
            commitItem.appendChild(meta);
            
            commitsContainer.appendChild(commitItem);
        });
    } else {
        const noCommits = document.createElement('p');
        noCommits.textContent = '该日期没有提交记录';
        commitsContainer.appendChild(noCommits);
    }
    
    // 显示结果区域
    document.getElementById('results-container').style.display = 'block';
    document.getElementById('error-container').style.display = 'none';
}

// 显示错误信息
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('loading').style.display = 'none';
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('error-container').style.display = 'none';
}

// 隐藏加载状态
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}