# WITRN 充电测试报告生成器

> [!TIP]
> 本仓库有两个版本，请根据需要选择：
> - **main 分支**（推荐）：Flask Web 版，支持 WITRN_PC_V1.0.4 生成视频报告 HTML
> - **[legacy 分支](https://github.com/VAPESMAN/witrn-charge-analyzer/tree/legacy)**：Electron 桌面应用版，支持旧版 V3.1 上位机

将 WITRN_PC_V1.0.4 新版上位机导出的 CSV 数据转换为**视频录制用 16:9 HTML 报告**，适用于短视频平台展示充电测试数据。

![Python](https://img.shields.io/badge/Python-3.6+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 分支说明

| 分支 | 技术栈 | 支持上位机 | 适用场景 |
|------|--------|-----------|----------|
| **main** | Flask + Chart.js | WITRN_PC_V1.0.4 | 短视频录制、分享报告 |
| **[legacy](https://github.com/VAPESMAN/witrn-charge-analyzer/tree/legacy)** | Electron + PyInstaller | V3.1 | 桌面应用、交互式图表 |

---

## 功能

- 解析 WITRN_PC_V1.0.4 上位机导出的 CSV 数据（电压、电流、功率、温度）
- 生成 16:9 横向视频报告 HTML，动画展示 Chart.js 曲线
- 自托管字体（Outfit + JetBrains Mono），无外部 CDN 依赖
- 报告完全自包含（base64 内嵌所有静态资源），可独立运行
- 可选 Flask Web 界面预览，或命令行直接转换

## 项目结构

```
├── charge_analyzer.py    # 核心脚本：CSV解析 → HTML报告生成
├── app.py                # Flask Web界面（可选）
├── templates/            # Flask模板
├── static/fonts/         # 自托管字体
├── reports/              # 生成的报告输出目录
├── requirements.txt      # Python依赖
└── README.md
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 命令行生成报告

```bash
python charge_analyzer.py
# 或指定CSV路径
python charge_analyzer.py path/to/your_data.csv
```

### Web界面预览

```bash
python app.py
# 访问 http://127.0.0.1:5000
```

报告文件会保存到 `reports/` 目录，文件名为 `{机型}_{日期}.html`。

## CSV 格式

本工具支持 WITRN_PC_V1.0.4 上位机导出的标准 CSV 格式：

```csv
SUM,42767
TotalTime,0001:11:16
SampTime(ms),100
DateTime, 2026-03-10 20:21:25
Time(hh:mm:ss:ms),Voltage(V),Current(A),Power(W),Temperature
"00:00:00:000", 0.000, 0.000, 0.000,--
"00:00:00:100", 15.19, -0.37, 5.652,--
...
```

## 示例报告

生成的 HTML 报告特点：

- **16:9 横向布局** — 适配视频录制比例
- **Chart.js 动态曲线** — 电压/电流/功率/温度四曲线
- **自启动画** — CSS revealUp 渐入效果
- **自包含资源** — 所有字体、图表均内嵌，无外部依赖

## 技术栈

- **数据处理**: Python
- **Web框架**: Flask
- **图表**: Chart.js
- **字体**: Outfit（正文）+ JetBrains Mono（数据）

## 相关链接

- [WITRN_PC_V1.0.4 上位机](https://www.witrn.com/) — 配套软件
- [WITRN K2](https://www.witrn.com/) — USB电流表硬件

## License

MIT

## 免责声明

本工具仅供学习和个人测试使用。使用本工具分析的数据仅供参考，不作为任何商业或专业用途的依据。本项目与 WITRN 无官方关联，为社区用户自发开发的第三方工具。
