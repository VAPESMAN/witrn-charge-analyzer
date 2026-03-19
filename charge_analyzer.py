import csv
import json
from datetime import datetime, timedelta
import os

def parse_time(time_str):
    time_str = time_str.strip('"')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = int(parts[3])
    return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def process_csv(csv_file_path):
    data = {
        'metadata': {},
        'timestamps': [],
        'voltage': [],
        'current': [],
        'power': [],
        'temperature': []
    }
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if len(row) < 2:
                continue
                
            key = row[0].strip()
            value = row[1].strip()
            
            if key == 'SUM':
                data['metadata']['sum'] = value
            elif key == 'TotalTime':
                data['metadata']['total_time'] = value
            elif key == 'SampTime(ms)':
                data['metadata']['sample_time_ms'] = value
            elif key == 'DateTime':
                data['metadata']['date_time'] = value
            elif key == 'Time(hh:mm:ss:ms)':
                continue
            else:
                try:
                    time_str = key.strip('"')
                    voltage = float(value)
                    current = float(row[2].strip())
                    power = float(row[3].strip())
                    temp = row[4].strip()
                    
                    time_delta = parse_time(time_str)
                    total_seconds = time_delta.total_seconds()
                    total_minutes = int(total_seconds / 60)
                    
                    data['timestamps'].append(total_minutes)
                    data['voltage'].append(voltage)
                    data['current'].append(abs(current))
                    data['power'].append(abs(power))
                    data['temperature'].append(temp)
                except (ValueError, IndexError):
                    continue
    
    # 数据抽样优化性能
    if len(data['timestamps']) > 1000:
        sample_rate = max(1, len(data['timestamps']) // 1000)
        data['timestamps'] = data['timestamps'][::sample_rate]
        data['voltage'] = data['voltage'][::sample_rate]
        data['current'] = data['current'][::sample_rate]
        data['power'] = data['power'][::sample_rate]
        data['temperature'] = data['temperature'][::sample_rate]
    
    return data

def generate_html(data, output_path, device_model):
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 生成HTML模板
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>充电测试数据分析</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            padding: 30px;
        }
        h1 {
            text-align: center;
            color: white;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .metadata {
            background: rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        .metadata-item {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metadata-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .metadata-label {
            font-weight: bold;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .metadata-value {
            color: white;
            font-size: 1.1em;
            font-weight: 600;
        }
        .chart-container {
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        .chart-title {
            text-align: center;
            color: white;
            margin-bottom: 20px;
            font-size: 1.5em;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        .chart-controls {
            text-align: center;
            margin-bottom: 20px;
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        .chart-controls label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
            color: white;
            background: rgba(255, 255, 255, 0.25);
            padding: 8px 15px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .chart-controls label:hover {
            background: rgba(255, 255, 255, 0.35);
            transform: translateY(-2px);
        }
        .chart-controls input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.4);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        canvas {
            max-height: 400px;
            background: rgba(255, 255, 255, 0.85);
            border-radius: 10px;
            padding: 10px;
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 0.9em;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 20px;
            }
            h1 {
                font-size: 2em;
            }
            .chart-controls {
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
            .chart-controls label {
                width: 200px;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ 充电测试数据分析</h1>
        <p class="subtitle">MODEL_PLACEHOLDER - 测试结果</p>
        
        <div class="metadata">
            <div class="metadata-item">
                <div class="metadata-label">总采样数</div>
                <div class="metadata-value" id="sum">-</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">总测试时间</div>
                <div class="metadata-value" id="totalTime">-</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">采样间隔</div>
                <div class="metadata-value" id="sampTime">-</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">测试时间</div>
                <div class="metadata-value" id="dateTime">-</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">最大电压</div>
                <div class="stat-value" id="maxVoltage">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">最大电流</div>
                <div class="stat-value" id="maxCurrent">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">最大功率</div>
                <div class="stat-value" id="maxPower">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均功率</div>
                <div class="stat-value" id="avgPower">-</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📊 充电曲线分析</div>
            <div class="chart-controls">
                <label>
                    <input type="checkbox" id="toggleVoltage" checked> 电压 (V)
                </label>
                <label>
                    <input type="checkbox" id="toggleCurrent" checked> 电流 (A)
                </label>
                <label>
                    <input type="checkbox" id="togglePower" checked> 功率 (W)
                </label>
            </div>
            <canvas id="combinedChart"></canvas>
        </div>
        
        <div class="footer">
            <p>充电测试数据分析工具 | 生成时间: CURRENT_TIME_PLACEHOLDER</p>
        </div>
    </div>
    
    <script>
        const data = DATA_PLACEHOLDER;
        
        document.getElementById('sum').textContent = data.metadata.sum || '-';
        document.getElementById('totalTime').textContent = data.metadata.total_time || '-';
        document.getElementById('sampTime').textContent = data.metadata.sample_time_ms + ' ms' || '-';
        document.getElementById('dateTime').textContent = data.metadata.date_time || '-';
        
        const maxVoltage = Math.max(...data.voltage).toFixed(2);
        const maxCurrent = Math.max(...data.current).toFixed(2);
        const maxPower = Math.max(...data.power).toFixed(2);
        const avgPower = (data.power.reduce((a, b) => a + b, 0) / data.power.length).toFixed(2);
        
        document.getElementById('maxVoltage').textContent = maxVoltage + ' V';
        document.getElementById('maxCurrent').textContent = maxCurrent + ' A';
        document.getElementById('maxPower').textContent = maxPower + ' W';
        document.getElementById('avgPower').textContent = avgPower + ' W';
        
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 0
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#333',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#333',
                    bodyColor: '#666',
                    padding: 12,
                    displayColors: true,
                    enabled: true,
                    borderColor: '#ddd',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '时间 (分钟)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        color: '#333'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        stepSize: 5,
                        maxRotation: 0,
                        color: '#666'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    title: {
                        display: true,
                        text: '数值',
                        font: {
                            size: 14,
                            weight: 'bold'
                        },
                        color: '#333'
                    },
                    ticks: {
                        color: '#666'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            elements: {
                line: {
                    tension: 0.4
                },
                point: {
                    radius: 0,
                    hoverRadius: 4
                }
            }
        };
        
        const combinedChart = new Chart(document.getElementById('combinedChart'), {
            type: 'line',
            data: {
                labels: data.timestamps,
                datasets: [
                    {
                        label: '电压 (V)',
                        data: data.voltage,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        borderWidth: 2,
                        fill: true
                    },
                    {
                        label: '电流 (A)',
                        data: data.current,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        fill: true
                    },
                    {
                        label: '功率 (W)',
                        data: data.power,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }
                ]
            },
            options: chartOptions
        });
        
        document.getElementById('toggleVoltage').addEventListener('change', function() {
            combinedChart.data.datasets[0].hidden = !this.checked;
            combinedChart.update();
        });
        
        document.getElementById('toggleCurrent').addEventListener('change', function() {
            combinedChart.data.datasets[1].hidden = !this.checked;
            combinedChart.update();
        });
        
        document.getElementById('togglePower').addEventListener('change', function() {
            combinedChart.data.datasets[2].hidden = !this.checked;
            combinedChart.update();
        });
    </script>
</body>
</html>'''
    
    # 替换占位符
    html_content = html_template.replace('DATA_PLACEHOLDER', json_data)
    html_content = html_content.replace('MODEL_PLACEHOLDER', device_model)
    html_content = html_content.replace('CURRENT_TIME_PLACEHOLDER', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    import sys
    
    # 解析命令行参数
    csv_file = None
    device_model = None
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg.endswith('.csv') and csv_file is None:
            csv_file = arg
        elif device_model is None:
            device_model = arg
    
    if not csv_file:
        csv_file = input('请输入CSV文件路径（例如：d:\\\\ChargeTest\\\\12-100充电.csv）: ').strip()
    
    if not os.path.exists(csv_file):
        print(f'错误：文件 {csv_file} 不存在！')
        return
    
    print('正在处理CSV文件...')
    data = process_csv(csv_file)
    
    # 获取测试时间
    test_time = data['metadata'].get('date_time', '')
    if test_time:
        # 提取日期部分，格式：2026-03-10
        test_date = test_time.split(' ')[0]
    else:
        # 如果没有测试时间，使用当前日期
        test_date = datetime.now().strftime('%Y-%m-%d')
    
    # 询问测试机型（如果命令行没有提供）
    if not device_model:
        try:
            device_model = input('请输入测试机型（例如：小米14Ultra）: ').strip()
        except:
            device_model = 'Unknown'
    
    # 确保机型名称不为空
    if not device_model:
        device_model = 'Unknown'
    
    # 生成文件名（移除可能导致问题的字符）
    safe_model = ''.join(c for c in device_model if c.isalnum() or c in ' _-')
    output_html = f"{safe_model}_{test_date}.html"
    
    # 保存HTML到当前目录
    output_html = os.path.join(os.path.dirname(csv_file), output_html)
    
    # 生成HTML，传递机型信息
    generate_html(data, output_html, device_model)
    
    # 统一使用UTF-8编码输出
    import sys
    # 确保标准输出使用UTF-8编码
    if sys.stdout.encoding != 'utf-8':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    
    # 输出结果
    print('处理完成！')
    print('报告已生成：' + output_html)
    print('数据点数量：' + str(len(data["timestamps"])))
    print('最大功率：' + '{:.2f}'.format(max(data["power"])) + ' W')
    print('最大电压：' + '{:.2f}'.format(max(data["voltage"])) + ' V')
    print('最大电流：' + '{:.2f}'.format(max(data["current"])) + ' A')

if __name__ == '__main__':
    main()
