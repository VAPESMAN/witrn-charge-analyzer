const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let lastCsvDir = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 700,
        height: 600,
        resizable: true,
        maximizable: true,
        title: '充电测试数据分析工具',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('electron-index.html');

    mainWindow.on('closed', function() {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

app.on('window-all-closed', function() {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function() {
    if (mainWindow === null) {
        createWindow();
    }
});

// 获取Python可执行文件路径
function getPythonExecutable() {
    if (app.isPackaged) {
        // 打包后：使用resources目录下的exe
        const exePath = path.join(process.resourcesPath, 'charge_analyzer.exe');
        return { command: exePath, useExe: true };
    } else {
        // 开发环境：使用python命令
        return { command: process.platform === 'win32' ? 'python' : 'python3', useExe: false };
    }
}

// 生成报告
ipcMain.on('generate-report', (event, data) => {
    const { csvFile, deviceModel } = data;
    lastCsvDir = path.dirname(csvFile);
    
    const env = Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' });
    const python = getPythonExecutable();
    const args = python.useExe ? [csvFile, deviceModel] : ['charge_analyzer.py', csvFile, deviceModel];
    const cwd = python.useExe ? path.dirname(csvFile) : __dirname;

    const pythonProcess = spawn(python.command, args, {
        cwd: cwd,
        stdio: 'pipe',
        env: env
    });

    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString('utf8');
    });

    pythonProcess.stderr.on('data', (data) => {
        error += data.toString('utf8');
    });
    
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            // 解析输出
            console.log('Python output:', output);
            const lines = output.split('\n');
            const result = {
                reportPath: '',
                dataPoints: '',
                maxPower: '',
                maxVoltage: '',
                maxCurrent: ''
            };
            
            lines.forEach(line => {
                console.log('Processing line:', line);
                if (line.includes('报告已生成：')) {
                    result.reportPath = line.split('报告已生成：')[1]?.trim() || '';
                } else if (line.includes('数据点数量：')) {
                    result.dataPoints = line.split('数据点数量：')[1]?.trim() || '';
                } else if (line.includes('最大功率：')) {
                    result.maxPower = line.split('最大功率：')[1]?.trim() || '';
                } else if (line.includes('最大电压：')) {
                    result.maxVoltage = line.split('最大电压：')[1]?.trim() || '';
                } else if (line.includes('最大电流：')) {
                    result.maxCurrent = line.split('最大电流：')[1]?.trim() || '';
                }
            });
            
            console.log('Parsed result:', result);
            event.reply('report-generated', result);
        } else {
            console.log('Python error:', error);
            event.reply('error', error || '处理失败');
        }
    });
});

// 打开输出文件夹
ipcMain.on('open-folder', () => {
    const folderPath = lastCsvDir || app.getPath('desktop');
    shell.openPath(folderPath);
});

// 打开报告
ipcMain.on('open-report', (event, reportPath) => {
    if (fs.existsSync(reportPath)) {
        shell.openPath(reportPath);
    }
});

// 显示帮助
ipcMain.on('show-help', () => {
    dialog.showMessageBox({
        type: 'info',
        title: '使用帮助',
        message: '使用说明',
        detail: `1. 选择CSV文件\n   点击"浏览"按钮选择要分析的CSV文件\n\n2. 输入测试机型\n   在"测试机型"输入框中输入设备名称\n   例如：小米14Ultra、iPhone 15 Pro等\n\n3. 生成报告\n   点击"生成分析报告"按钮开始处理\n\n4. 查看结果\n   处理完成后会自动询问是否打开报告\n\n提示：\n- 确保CSV文件格式正确\n- 机型名称将显示在报告标题中\n- 报告文件会自动保存到CSV文件所在目录`,
        buttons: ['确定']
    });
});