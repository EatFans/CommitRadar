document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    const commitForm = document.getElementById('commitForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    
    // 添加表单提交事件监听器
    if (commitForm) {
        commitForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 获取输入值
            const username = document.getElementById('username').value.trim();
            const date = document.getElementById('date').value;
            
            // 验证输入
            if (!username || !date) {
                showError('请填写所有必填字段');
                return;
            }
            
            // 显示加载状态
            loading.classList.remove('d-none');
            results.classList.add('d-none');
            error.classList.add('d-none');
            
            console.log('正在发送请求...');
            console.log('用户名:', username);
            console.log('日期:', date);
            
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
                console.log('收到响应:', response.status);
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || '请求失败');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('解析数据:', data);
                // 隐藏加载状态
                loading.classList.add('d-none');
                
                // 显示结果
                results.classList.remove('d-none');
                
                // 更新结果摘要
                const resultSummary = document.getElementById('resultSummary');
                resultSummary.textContent = `用户 ${data.username} 在 ${data.date} 的提交次数: ${data.count}`;
                
                // 清空并更新提交列表
                const commitList = document.getElementById('commitList');
                commitList.innerHTML = '';
                
                if (data.count > 0 && data.commits && data.commits.length > 0) {
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
                
                // 保存数据用于导出
                window.commitData = data;
                
                // 显示导出按钮（如果存在）
                const exportContainer = document.getElementById('exportContainer');
                if (exportContainer) {
                    exportContainer.classList.remove('d-none');
                }
            })
            .catch(err => {
                console.error('错误:', err);
                // 隐藏加载状态
                loading.classList.add('d-none');
                
                // 显示错误信息
                showError(err.message || '获取数据时发生错误');
            });
        });
    } else {
        console.error('找不到提交表单元素');
    }
    
    // 添加导出JSON功能
    const exportJsonBtn = document.getElementById('exportJson');
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', function() {
            if (!window.commitData) {
                showError('没有可导出的数据，请先查询提交记录');
                return;
            }
            
            // 获取用户指定的导出路径
            const customPath = document.getElementById('exportPath')?.value.trim();
            
            // 发送导出请求
            fetch('/api/export-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data: window.commitData,
                    path: customPath
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || '导出失败');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 创建下载链接
                    const link = document.createElement('a');
                    link.href = data.download_url;
                    link.download = data.filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // 显示成功消息
                    const successAlert = document.createElement('div');
                    successAlert.className = 'alert alert-success mt-2';
                    successAlert.textContent = `成功导出到 ${data.filepath}`;
                    document.getElementById('exportContainer').appendChild(successAlert);
                    
                    // 3秒后移除成功消息
                    setTimeout(() => {
                        successAlert.remove();
                    }, 3000);
                } else {
                    throw new Error(data.error || '导出失败');
                }
            })
            .catch(err => {
                showError(err.message || '导出数据时发生错误');
            });
        });
    }
    
    // 显示错误信息的函数
    function showError(message) {
        const error = document.getElementById('error');
        if (error) {
            error.textContent = message;
            error.classList.remove('d-none');
        } else {
            console.error('错误:', message);
            alert('错误: ' + message);
        }
    }
    
    // 初始化日期选择器为今天
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;
    }
    
    // 添加导出按钮容器（如果不存在）
    if (!document.getElementById('exportContainer')) {
        const exportContainer = document.createElement('div');
        exportContainer.className = 'mt-3 mb-3 d-none';
        exportContainer.id = 'exportContainer';
        
        // 添加标题
        const exportTitle = document.createElement('h5');
        exportTitle.textContent = '导出数据：';
        exportContainer.appendChild(exportTitle);
        
        // 添加输入组
        const inputGroup = document.createElement('div');
        inputGroup.className = 'input-group mb-3';
        
        // 添加路径输入框
        const pathInput = document.createElement('input');
        pathInput.type = 'text';
        pathInput.className = 'form-control';
        pathInput.id = 'exportPath';
        pathInput.placeholder = '自定义导出路径（可选）';
        inputGroup.appendChild(pathInput);
        
        // 添加导出按钮
        const exportBtn = document.createElement('button');
        exportBtn.className = 'btn btn-success';
        exportBtn.type = 'button';
        exportBtn.id = 'exportJson';
        exportBtn.textContent = '导出为JSON';
        inputGroup.appendChild(exportBtn);
        
        exportContainer.appendChild(inputGroup);
        
        // 将导出容器添加到结果区域后面
        const results = document.getElementById('results');
        if (results) {
            results.appendChild(exportContainer);
        } else {
            document.querySelector('.card-body').appendChild(exportContainer);
        }
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