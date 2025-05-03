document.addEventListener('DOMContentLoaded', function() {
    // 初始化年份选择器
    initYearSelect();
    
    // 设置默认日期
    const today = new Date();
    document.getElementById('start-date').value = formatDate(new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)); // 一周前
    document.getElementById('end-date').value = formatDate(today);
    document.getElementById('week-date').value = formatDate(today);
    
    // 设置默认月份和年份
    document.getElementById('month').value = today.getMonth() + 1;
    document.getElementById('month-year').value = today.getFullYear();
    
    // 绑定模式切换事件
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    modeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateModeDisplay(this.value);
        });
    });
    
    // 绑定搜索按钮点击事件
    document.getElementById('search-btn').addEventListener('click', searchBatchCommits);
    
    // 绑定导出按钮事件
    document.getElementById('export-excel').addEventListener('click', () => exportData('excel'));
    document.getElementById('export-csv').addEventListener('click', () => exportData('csv'));
    document.getElementById('export-json').addEventListener('click', () => exportData('json'));
});

// 初始化年份选择器
function initYearSelect() {
    const yearSelect = document.getElementById('month-year');
    const currentYear = new Date().getFullYear();
    
    // 添加从当前年份往前10年的选项
    for (let year = currentYear; year >= currentYear - 10; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
}

// 更新模式显示
function updateModeDisplay(mode) {
    const rangeMode = document.getElementById('range-mode');
    const weekMode = document.getElementById('week-mode');
    const monthMode = document.getElementById('month-mode');
    
    rangeMode.style.display = 'none';
    weekMode.style.display = 'none';
    monthMode.style.display = 'none';
    
    switch (mode) {
        case 'range':
            rangeMode.style.display = 'block';
            break;
        case 'week':
            weekMode.style.display = 'block';
            break;
        case 'month':
            monthMode.style.display = 'block';
            break;
    }
}

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 搜索批量提交记录
function searchBatchCommits() {
    const username = document.getElementById('username').value.trim();
    
    if (!username) {
        showError('请输入GitHub用户名');
        return;
    }
    
    // 获取当前选择的模式
    const mode = document.querySelector('input[name="mode"]:checked').value;
    
    // 准备请求数据
    const requestData = {
        username: username,
        mode: mode
    };
    
    // 根据不同模式添加参数
    switch (mode) {
        case 'range':
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            if (!startDate || !endDate) {
                showError('请选择开始和结束日期');
                return;
            }
            
            requestData.startDate = startDate;
            requestData.endDate = endDate;
            break;
            
        case 'week':
            const weekDate = document.getElementById('week-date').value;
            
            if (!weekDate) {
                showError('请选择日期');
                return;
            }
            
            requestData.date = weekDate;
            break;
            
        case 'month':
            const year = document.getElementById('month-year').value;
            const month = document.getElementById('month').value;
            
            requestData.year = year;
            requestData.month = month;
            break;
    }
    
    // 显示加载状态
    showLoading();
    
    // 发送API请求
    fetch('/api/batch-commits', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        displayResults(data);
        // 启用导出按钮
        enableExportButtons();
        // 保存结果数据用于导出
        window.commitData = data.results;
    })
    .catch(error => {
        hideLoading();
        showError('获取数据失败: ' + error.message);
    });
}

// 显示结果
function displayResults(data) {
    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const resultsBody = document.getElementById('results-body');
    const summaryContainer = document.getElementById('summary-container');
    
    // 清空现有结果
    resultsBody.innerHTML = '';
    summaryContainer.innerHTML = '';
    
    // 显示结果容器
    resultsContainer.style.display = 'block';
    
    // 添加汇总信息
    summaryContainer.innerHTML = `
        <h3>汇总信息</h3>
        <p>用户: <strong>${data.username}</strong></p>
        <p>总提交次数: <strong>${data.total_commits}</strong></p>
        <p>查询模式: <strong>${getModeText(data.mode)}</strong></p>
    `;
    
    // 添加表格行
    data.results.forEach(day => {
        const row = document.createElement('tr');
        
        // 日期单元格
        const dateCell = document.createElement('td');
        dateCell.textContent = day.date;
        row.appendChild(dateCell);
        
        // 提交次数单元格
        const countCell = document.createElement('td');
        countCell.textContent = day.count;
        // 根据提交次数设置不同的背景色
        if (day.count > 0) {
            const intensity = Math.min(day.count / 10, 1); // 最多10次提交为最深色
            const green = Math.floor(200 - intensity * 150);
            countCell.style.backgroundColor = `rgb(0, ${green}, 0)`;
            countCell.style.color = day.count > 5 ? 'white' : 'black';
        }
        row.appendChild(countCell);
        
        // 详情按钮单元格
        const detailsCell = document.createElement('td');
        if (day.count > 0 && day.commits && day.commits.length > 0) {
            const detailsBtn = document.createElement('button');
            detailsBtn.textContent = '查看详情';
            detailsBtn.className = 'btn btn-sm btn-info';
            detailsBtn.addEventListener('click', () => showCommitDetails(day));
            detailsCell.appendChild(detailsBtn);
        } else {
            detailsCell.textContent = '无提交';
        }
        row.appendChild(detailsCell);
        
        resultsBody.appendChild(row);
    });
    
    // 创建图表
    createCommitChart(data.results);
}

// 获取模式文本
function getModeText(mode) {
    switch (mode) {
        case 'range': return '日期范围';
        case 'week': return '一周';
        case 'month': return '月份';
        default: return mode;
    }
}

// 显示提交详情
function showCommitDetails(day) {
    const modal = document.getElementById('commit-details-modal');
    const modalTitle = document.getElementById('commit-details-title');
    const modalBody = document.getElementById('commit-details-body');
    
    // 设置标题
    modalTitle.textContent = `${day.date} 的提交详情 (${day.count} 次)`;
    
    // 清空并填充内容
    modalBody.innerHTML = '';
    
    if (day.commits && day.commits.length > 0) {
        const list = document.createElement('ul');
        list.className = 'list-group';
        
        day.commits.forEach(commit => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            
            const repoName = document.createElement('div');
            repoName.className = 'font-weight-bold';
            repoName.textContent = commit.repo;
            
            const commitTitle = document.createElement('div');
            commitTitle.textContent = commit.title;
            
            const commitTime = document.createElement('small');
            commitTime.className = 'text-muted';
            commitTime.textContent = commit.time;
            
            const commitLink = document.createElement('a');
            commitLink.href = commit.url;
            commitLink.target = '_blank';
            commitLink.className = 'btn btn-sm btn-outline-primary float-right';
            commitLink.textContent = '查看提交';
            
            item.appendChild(repoName);
            item.appendChild(commitTitle);
            item.appendChild(commitTime);
            item.appendChild(commitLink);
            
            list.appendChild(item);
        });
        
        modalBody.appendChild(list);
    } else {
        modalBody.innerHTML = '<p class="text-center">没有详细信息可用</p>';
    }
    
    // 显示模态框
    $(modal).modal('show');
}

// 创建提交图表
function createCommitChart(results) {
    const ctx = document.getElementById('commit-chart').getContext('2d');
    
    // 准备数据
    const dates = results.map(day => day.date);
    const counts = results.map(day => day.count);
    
    // 如果已有图表，销毁它
    if (window.commitChart) {
        window.commitChart.destroy();
    }
    
    // 创建新图表
    window.commitChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: '提交次数',
                data: counts,
                backgroundColor: counts.map(count => {
                    const intensity = Math.min(count / 10, 1);
                    return `rgba(0, ${Math.floor(200 - intensity * 150)}, 0, 0.7)`;
                }),
                borderColor: 'rgba(0, 100, 0, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// 导出数据
function exportData(format) {
    if (!window.commitData || window.commitData.length === 0) {
        showError('没有数据可导出');
        return;
    }
    
    // 显示加载状态
    showLoading();
    
    fetch('/api/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            results: window.commitData,
            format: format
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('导出失败');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        if (data.success && data.download_url) {
            // 创建下载链接并点击
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            showError(data.error || '导出失败');
        }
    })
    .catch(error => {
        hideLoading();
        showError('导出失败: ' + error.message);
    });
}

// 启用导出按钮
function enableExportButtons() {
    document.getElementById('export-excel').disabled = false;
    document.getElementById('export-csv').disabled = false;
    document.getElementById('export-json').disabled = false;
}

// 显示错误信息
function showError(message) {
    const alertBox = document.getElementById('alert-box');
    alertBox.textContent = message;
    alertBox.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        alertBox.style.display = 'none';
    }, 3000);
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading-spinner').style.display = 'block';
}

// 隐藏加载状态
function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
}