const dropZone = document.getElementById('dropZone');
const csvFile = document.getElementById('csvFile');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFile = document.getElementById('clearFile');
const deviceModel = document.getElementById('deviceModel');
const generateBtn = document.getElementById('generateBtn');
const status = document.getElementById('status');
const resultCard = document.getElementById('resultCard');
const statGrid = document.getElementById('statGrid');
const viewReport = document.getElementById('viewReport');
const resetBtn = document.getElementById('resetBtn');

let selectedFile = null;

// Drag & Drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

csvFile.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showStatus('请选择 CSV 格式的文件', 'error');
        return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    hideStatus();
}

clearFile.addEventListener('click', () => {
    selectedFile = null;
    csvFile.value = '';
    fileInfo.style.display = 'none';
});

// Generate
generateBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        showStatus('请先选择 CSV 文件', 'error');
        return;
    }
    const model = deviceModel.value.trim();
    if (!model) {
        showStatus('请输入测试机型', 'error');
        return;
    }

    setLoading(true);
    hideStatus();
    resultCard.style.display = 'none';

    const formData = new FormData();
    formData.append('csv', selectedFile);
    formData.append('model', model);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success) {
            showStatus('报告生成成功', 'success');
            showResult(result);
            viewReport.href = '/reports/' + result.report;
        } else {
            showStatus(result.error || '生成失败', 'error');
        }
    } catch (err) {
        showStatus('网络错误：' + err.message, 'error');
    } finally {
        setLoading(false);
    }
});

function showResult(result) {
    const stats = result.stats;
    const items = [
        { label: '数据点', value: stats.data_points },
        { label: '平均电压', value: stats.avg_voltage },
        { label: '平均电流', value: stats.avg_current },
        { label: '平均功率', value: stats.avg_power },
        { label: '最大功率', value: stats.max_power },
        { label: '最大电压', value: stats.max_voltage },
        { label: '最大电流', value: stats.max_current },
    ];

    statGrid.innerHTML = items.map(item => `
        <div class="stat-item">
            <div class="stat-item-label">${item.label}</div>
            <div class="stat-item-value">${item.value}</div>
        </div>
    `).join('');

    resultCard.style.display = 'block';
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

resetBtn.addEventListener('click', () => {
    selectedFile = null;
    csvFile.value = '';
    fileInfo.style.display = 'none';
    deviceModel.value = '';
    resultCard.style.display = 'none';
    hideStatus();
});

function showStatus(message, type) {
    status.textContent = message;
    status.className = 'status ' + type;
    status.style.display = 'block';
}

function hideStatus() {
    status.style.display = 'none';
}

function setLoading(loading) {
    generateBtn.disabled = loading;
    generateBtn.querySelector('.btn-text').textContent = loading ? '生成中...' : '生成报告';
    generateBtn.querySelector('.spinner').style.display = loading ? 'inline-block' : 'none';
}
