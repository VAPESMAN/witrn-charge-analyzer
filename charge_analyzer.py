import csv
import json
from datetime import datetime, timedelta
import os
import base64

def parse_time(time_str):
    # 新版格式: ="00:00:00.000" (HH:MM:SS.mmm)
    # 旧版格式: "00:00:00:000" (HH:MM:SS:mmm)
    time_str = time_str.lstrip('=').strip('"')
    if '.' in time_str:
        # 新版: HH:MM:SS.mmm
        parts = time_str.split(':')
        seconds_and_ms = parts[2].split('.')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(seconds_and_ms[0])
        milliseconds = int(seconds_and_ms[1]) if len(seconds_and_ms) > 1 else 0
    else:
        # 旧版: HH:MM:SS:mmm
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
    
    with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)

        METADATA_KEYS = {'SUM', 'TotalTime', 'SampTime(ms)', 'DateTime'}

        for row in reader:
            if len(row) < 2:
                continue

            key = row[0].strip()
            value = row[1].strip() if len(row) > 1 else ''

            if key in METADATA_KEYS:
                if key == 'SUM':
                    data['metadata']['sum'] = value
                elif key == 'TotalTime':
                    # 新版: ="01:13:35.300"，旧版: 0001:11:16
                    data['metadata']['total_time'] = value.lstrip('=').strip('"')
                elif key == 'SampTime(ms)':
                    data['metadata']['sample_time_ms'] = value
                elif key == 'DateTime':
                    data['metadata']['date_time'] = value
            elif key.startswith('Time'):
                # 新版: Time(D.hh:mm:ss.ms)，旧版: Time(hh:mm:ss:ms)
                continue
            else:
                # 数据行
                try:
                    time_str = key
                    voltage = float(value)
                    current = float(row[2].strip())
                    power = float(row[3].strip())
                    _temp = row[4].strip() if len(row) > 4 else ''
                    temp = _temp if _temp not in ('', '--') else ''

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

def compute_stats(data):
    """计算统计数据"""
    return {
        'max_voltage': max(data['voltage']),
        'max_current': max(data['current']),
        'max_power': max(data['power']),
        'avg_voltage': sum(data['voltage']) / len(data['voltage']),
        'avg_current': sum(data['current']) / len(data['current']),
        'avg_power': sum(data['power']) / len(data['power']),
    }

def generate_video_html(data, output_path, device_model, stats):
    """生成视频报告HTML - 苹果风16:9视频报告"""
    json_data = json.dumps(data, ensure_ascii=False, indent=2)

    # 读取静态资源并转为base64（生成自包含HTML，移动后资源不丢失）
    base_dir = os.path.dirname(os.path.abspath(__file__))

    def _file_to_base64(path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('ascii')

    chart_js_b64 = _file_to_base64(os.path.join(base_dir, 'static/js/chart.umd.js'))
    font_outfit_regular = _file_to_base64(os.path.join(base_dir, 'static/fonts/Outfit-Regular.ttf'))
    font_outfit_medium = _file_to_base64(os.path.join(base_dir, 'static/fonts/Outfit-Medium.ttf'))
    font_outfit_semibold = _file_to_base64(os.path.join(base_dir, 'static/fonts/Outfit-SemiBold.ttf'))
    font_outfit_bold = _file_to_base64(os.path.join(base_dir, 'static/fonts/Outfit-Bold.ttf'))
    font_jetbrains_regular = _file_to_base64(os.path.join(base_dir, 'static/fonts/JetBrainsMono-Regular.ttf'))
    font_jetbrains_medium = _file_to_base64(os.path.join(base_dir, 'static/fonts/JetBrainsMono-Medium.ttf'))
    font_jetbrains_bold = _file_to_base64(os.path.join(base_dir, 'static/fonts/JetBrainsMono-Bold.ttf'))
    logo_svg_b64 = _file_to_base64(os.path.join(base_dir, 'static/logo.svg'))

    # 苹果风16:9视频报告模板
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>充电测试报告 - DEVICE_TITLE</title>
    <script src="data:text/javascript;base64,CHART_JS_B64"></script>
    <style>
        @font-face {
            font-family: 'Outfit';
            font-style: normal;
            font-weight: 400;
            src: url('data:font/ttf;base64,FONT_OUTFIT_REGULAR') format('truetype');
        }
        @font-face {
            font-family: 'Outfit';
            font-style: normal;
            font-weight: 500;
            src: url('data:font/ttf;base64,FONT_OUTFIT_MEDIUM') format('truetype');
        }
        @font-face {
            font-family: 'Outfit';
            font-style: normal;
            font-weight: 600;
            src: url('data:font/ttf;base64,FONT_OUTFIT_SEMIBOLD') format('truetype');
        }
        @font-face {
            font-family: 'Outfit';
            font-style: normal;
            font-weight: 700;
            src: url('data:font/ttf;base64,FONT_OUTFIT_BOLD') format('truetype');
        }
        @font-face {
            font-family: 'JetBrains Mono';
            font-style: normal;
            font-weight: 400;
            src: url('data:font/ttf;base64,FONT_JETBRAINS_REGULAR') format('truetype');
        }
        @font-face {
            font-family: 'JetBrains Mono';
            font-style: normal;
            font-weight: 500;
            src: url('data:font/ttf;base64,FONT_JETBRAINS_MEDIUM') format('truetype');
        }
        @font-face {
            font-family: 'JetBrains Mono';
            font-style: normal;
            font-weight: 700;
            src: url('data:font/ttf;base64,FONT_JETBRAINS_BOLD') format('truetype');
        }

        :root {
            --bg-primary: #F2F2F5;
            --bg-surface: #FFFFFF;
            --bg-chart: #FFFFFF;
            --bg-stat: #FAFAFC;
            --text-primary: #1A1A1E;
            --text-secondary: #6E6E78;
            --text-tertiary: #9E9EA8;
            --accent-orange: #F5A623;
            --accent-blue: #2D8CF0;
            --accent-green: #34C759;
            --shadow-soft: 0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 12px rgba(0, 0, 0, 0.04);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        @keyframes revealUp {
            0% {
                opacity: 0;
                transform: translateY(60px);
                filter: blur(12px);
            }
            60% {
                opacity: 1;
                filter: blur(2px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
                filter: blur(0);
            }
        }

        body {
            font-family: 'Outfit', 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 40px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .page {
            width: 100%;
            max-width: 1600px;
            height: calc(100vh - 80px);
            background: var(--bg-surface);
            border-radius: 16px;
            box-shadow: var(--shadow-soft);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .header {
            height: 92px;
            flex-shrink: 0;
            padding: 0 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            animation: revealUp 1.8s cubic-bezier(0.22, 1, 0.36, 1) 1.5s forwards;
            opacity: 0;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-icon {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            flex-shrink: 0;
        }

        .brand-icon img {
            width: 44px;
            height: 44px;
            object-fit: contain;
        }

        .device-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-secondary);
            letter-spacing: -0.3px;
        }

        .report-type {
            font-size: 16px;
            font-weight: 500;
            color: var(--text-secondary);
            background: rgba(0, 0, 0, 0.04);
            padding: 10px 22px;
            border-radius: 100px;
            letter-spacing: -0.2px;
        }

        .chart-area {
            flex: 1;
            padding: 24px 32px 0;
            display: flex;
            flex-direction: column;
            animation: revealUp 2.0s cubic-bezier(0.22, 1, 0.36, 1) 1.8s forwards;
            opacity: 0;
            min-height: 0;
        }

        .chart-wrapper {
            flex: 1;
            position: relative;
            background: var(--bg-chart);
            border-radius: 12px;
            padding: 20px 28px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            min-height: 0;
        }

        .chart-wrapper canvas {
            width: 100% !important;
            height: 100% !important;
        }

        .stats-footer {
            flex-shrink: 0;
            padding: 20px 32px 28px;
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            animation: revealUp 1.6s cubic-bezier(0.22, 1, 0.36, 1) 2.1s forwards;
            opacity: 0;
        }

        .stat-card {
            background: var(--bg-stat);
            border-radius: 12px;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            position: relative;
            overflow: hidden;
            border-top: 4px solid transparent;
        }

        .stat-card:nth-child(1) { border-top-color: var(--accent-blue); }
        .stat-card:nth-child(2) { border-top-color: var(--accent-green); }
        .stat-card:nth-child(3) { border-top-color: var(--accent-orange); }
        .stat-card:nth-child(4) { border-top-color: #FF6B6B; }
        .stat-card:nth-child(5) { border-top-color: var(--text-secondary); }

        .stat-icon {
            width: 26px;
            height: 26px;
            margin-bottom: 8px;
            color: var(--text-tertiary);
        }

        .stat-label {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .stat-value {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
            line-height: 1.1;
            font-variant-numeric: tabular-nums;
        }

        .stat-unit {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-size: 16px;
            font-weight: 500;
            color: var(--text-tertiary);
            margin-left: 2px;
        }

        @media (max-width: 1200px) {
            body { padding: 24px; }
            .header { padding: 0 32px; height: 72px; }
            .chart-area { padding: 20px 32px 0; }
            .stats-footer { padding: 14px 32px 22px; height: 150px; gap: 12px; }
            .stat-value { font-size: 30px; }
        }

        @media (max-width: 768px) {
            body { padding: 16px; }
            .header { padding: 0 20px; height: 64px; }
            .chart-area { padding: 16px 20px 0; }
            .stats-footer {
                grid-template-columns: repeat(2, 1fr);
                padding: 12px 20px 20px;
                height: auto;
                gap: 12px;
            }
            .stat-value { font-size: 26px; }
            .report-type { display: none; }
        }
    </style>
</head>
<body>
    <div class="page">
        <header class="header">
            <div class="brand">
                <div class="brand-icon">
                    <img src="data:image/svg+xml;base64,LOGO_SVG_B64" alt="轻洞" />
                </div>
                <span class="device-title">DEVICE_TITLE</span>
            </div>
            <span class="report-type">充电测试报告</span>
        </header>

        <div class="chart-area">
            <div class="chart-wrapper">
                <canvas id="chart"></canvas>
            </div>
        </div>

        <div class="stats-footer">
            <div class="stat-card">
                <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                <div class="stat-label">峰值电压</div>
                <div class="stat-value">
                    <span id="maxVoltage">-</span><span class="stat-unit">V</span>
                </div>
            </div>
            <div class="stat-card">
                <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M2 12h20"/></svg>
                <div class="stat-label">峰值电流</div>
                <div class="stat-value">
                    <span id="maxCurrent">-</span><span class="stat-unit">A</span>
                </div>
            </div>
            <div class="stat-card">
                <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10"/></svg>
                <div class="stat-label">平均功率</div>
                <div class="stat-value">
                    <span id="avgPower">-</span><span class="stat-unit">W</span>
                </div>
            </div>
            <div class="stat-card">
                <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1 2-3 4-5.5 5.5C6.5 18 8.5 20 12 20s5.5-2 5.5-5.5c0-1.12-.5-2.5-2-4.5-1 2-2 3-3.5 4.5z"/></svg>
                <div class="stat-label">最大功率</div>
                <div class="stat-value">
                    <span id="maxPower">-</span><span class="stat-unit">W</span>
                </div>
            </div>
            <div class="stat-card">
                <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <div class="stat-label">总耗时</div>
                <div class="stat-value">
                    <span id="totalTime">-</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = DATA_JSON;
        const stats = STATS_JSON;

        document.getElementById('maxVoltage').textContent = stats.max_voltage ? stats.max_voltage.toFixed(2) : '-';
        document.getElementById('maxCurrent').textContent = stats.max_current ? stats.max_current.toFixed(2) : '-';
        document.getElementById('avgPower').textContent = stats.avg_power ? stats.avg_power.toFixed(2) : '-';
        document.getElementById('maxPower').textContent = stats.max_power ? stats.max_power.toFixed(2) : '-';
        document.getElementById('totalTime').textContent = data.metadata.total_time || '-';

        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.timestamps,
                datasets: [
                    {
                        label: '功率 (W)',
                        data: data.power,
                        borderColor: '#F5A623',
                        backgroundColor: 'rgba(245, 166, 35, 0.06)',
                        borderWidth: 5,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        fill: true,
                        tension: 0.3,
                        order: 1
                    },
                    {
                        label: '电压 (V)',
                        data: data.voltage,
                        borderColor: '#2D8CF0',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [8, 4],
                        pointRadius: 0,
                        tension: 0.3,
                        order: 2
                    },
                    {
                        label: '电流 (A)',
                        data: data.current,
                        borderColor: '#34C759',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        borderDash: [4, 4],
                        pointRadius: 0,
                        tension: 0.3,
                        order: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1600,
                    easing: 'easeOutQuart',
                    delay: 1800,
                    x: {
                        type: 'number',
                        easing: 'linear',
                        duration: 1600,
                        from: NaN,
                        delay(ctx) {
                            if (ctx.type !== 'data' || ctx.xStarted) {
                                return 0;
                            }
                            ctx.xStarted = true;
                            return ctx.index * (1600 / ctx.chart.data.labels.length);
                        }
                    },
                    y: {
                        type: 'number',
                        easing: 'linear',
                        duration: 1600,
                        from: (ctx) => ctx.index === 0 ? ctx.chart.scales.y.getPixelForValue(0) : undefined,
                        delay(ctx) {
                            if (ctx.type !== 'data' || ctx.yStarted) {
                                return 0;
                            }
                            ctx.yStarted = true;
                            return ctx.index * (1600 / ctx.chart.data.labels.length);
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'line',
                            pointStyleWidth: 28,
                            padding: 20,
                            font: {
                                size: 16,
                                family: "'Outfit', 'PingFang SC', sans-serif",
                                weight: 500
                            },
                            color: '#6E6E78'
                        }
                    },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间 (分钟)',
                            font: { size: 15, weight: 600, family: "'Outfit', 'PingFang SC', sans-serif" },
                            color: '#9E9EA8',
                            padding: { top: 12 }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.04)',
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 14, family: "'JetBrains Mono', monospace" },
                            color: '#9E9EA8',
                            maxTicksLimit: 12,
                            padding: 8
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.04)',
                            drawBorder: false
                        },
                        ticks: {
                            font: { size: 14, family: "'JetBrains Mono', monospace" },
                            color: '#9E9EA8'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>'''

    # 替换占位符
    stats_json = json.dumps(stats, ensure_ascii=False, indent=2)
    html_content = html_template.replace('DATA_JSON', json_data)
    html_content = html_content.replace('STATS_JSON', stats_json)
    html_content = html_content.replace('DEVICE_TITLE', device_model)
    html_content = html_content.replace('CHART_JS_B64', chart_js_b64)
    html_content = html_content.replace('FONT_OUTFIT_REGULAR', font_outfit_regular)
    html_content = html_content.replace('FONT_OUTFIT_MEDIUM', font_outfit_medium)
    html_content = html_content.replace('FONT_OUTFIT_SEMIBOLD', font_outfit_semibold)
    html_content = html_content.replace('FONT_OUTFIT_BOLD', font_outfit_bold)
    html_content = html_content.replace('FONT_JETBRAINS_REGULAR', font_jetbrains_regular)
    html_content = html_content.replace('FONT_JETBRAINS_MEDIUM', font_jetbrains_medium)
    html_content = html_content.replace('FONT_JETBRAINS_BOLD', font_jetbrains_bold)
    html_content = html_content.replace('LOGO_SVG_B64', logo_svg_b64)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

# [已弃用] 旧的 generate_html 和 generate_interactive_html 函数已删除
# 统一使用 generate_video_html 生成视频优化报告

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
    
    # 计算统计数据并生成视频报告HTML
    stats = compute_stats(data)
    generate_video_html(data, output_html, device_model, stats)
    
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
