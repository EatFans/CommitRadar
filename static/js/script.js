document.addEventListener('DOMContentLoaded', function() {
    // 设置日期输入框默认值为今天
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    document.getElementById('date').value = `${year}-${month}-${day}`;
    
    // 表单提交处理
    const commitForm = document.getElementById('commitForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const resultSummary = document.getElementById('resultSummary');
    const commitList = document.getElementById('commitList');
    
    commitForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const date = document.getElementById('date').value;
        
        if (!username || !date) {
            showError('请填写所有必填字段');
            return;
        }
        
        // 显示加载状态
        loading.classList.remove('d-none');
        results.classList.add('d-none');
        error.classList.add('d-none');
        
        // 发送 API 请求
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
            // 隐藏加载状态
            loading.classList.add('d-none');
            
            // 显示结果
            results.classList.remove('d-none');
            
            // 更新结果摘要
            resultSummary.textContent = `用户 ${data.username} 在 ${data.date} 的提交次数: ${data.count}`;
            
            // 清空并更新提交列表
            commitList.innerHTML = '';
            
            if (data.count > 0 && data.commits.length > 0) {
                data.commits.forEach(commit => {
                    const item = document.createElement('a');
                    item.href = commit.url;
                    item.target = '_blank';
                    item.className = 'list-group-item list-group-item-action commit-item';
                    
                    item.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1 commit-repo">${commit.repo}</h5>
                            <small class="commit-time">${commit.time}</small>
                        </div>
                        <p class="mb-1 commit-title">${commit.title}</p>
                    `;
                    
                    commitList.appendChild(item);
                });
            } else if (data.count > 0) {
                commitList.innerHTML = '<div class="alert alert-warning">找到了提交记录，但无法获取详细信息</div>';
            } else {
                commitList.innerHTML = '<div class="alert alert-warning">该日期没有提交记录</div>';
            }
        })
        .catch(err => {
            // 隐藏加载状态
            loading.classList.add('d-none');
            
            // 显示错误信息
            showError(err.message || '获取数据时发生错误');
        });
    });
    
    function showError(message) {
        error.textContent = message;
        error.classList.remove('d-none');
    }
});

// 添加到现有的script.js文件末尾

// 添加调试模式切换
const debugModeCheckbox = document.getElementById('debugMode');
const htmlInputContainer = document.getElementById('htmlInputContainer');

if (debugModeCheckbox && htmlInputContainer) {
    debugModeCheckbox.addEventListener('change', function() {
        if (this.checked) {
            htmlInputContainer.classList.remove('d-none');
        } else {
            htmlInputContainer.classList.add('d-none');
        }
    });
    
    // 添加HTML解析测试功能
    const testHtmlForm = document.getElementById('testHtmlForm');
    if (testHtmlForm) {
        testHtmlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const htmlContent = document.getElementById('htmlContent').value;
            const testDate = document.getElementById('testDate').value;
            
            if (!htmlContent || !testDate) {
                showError('请填写HTML内容和日期');
                return;
            }
            
            // 显示加载状态
            loading.classList.remove('d-none');
            results.classList.add('d-none');
            error.classList.add('d-none');
            
            // 发送API请求
            fetch('/api/test-parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    html: htmlContent,
                    date: testDate
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
                // 隐藏加载状态
                loading.classList.add('d-none');
                
                // 显示结果
                results.classList.remove('d-none');
                
                // 更新结果摘要
                resultSummary.textContent = `在 ${data.date} 的提交次数: ${data.count}`;
                
                // 清空提交列表
                commitList.innerHTML = '<div class="alert alert-info">这是HTML解析测试结果，不包含提交详情</div>';
            })
            .catch(err => {
                // 隐藏加载状态
                loading.classList.add('d-none');
                
                // 显示错误信息
                showError(err.message || '解析HTML时发生错误');
            });
        });
    }
}