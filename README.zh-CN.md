# DFU 引导工具 V2（macOS｜Python CLI+GUI）

一个在 macOS 14/15 上可直接运行的 iPhone DFU 引导工具，支持 CLI 与 GUI。工具会自动轮询检测设备是否处于 DFU/恢复/正常 模式，并提供按机型族的逐秒操作指引与蜂鸣/可选语音提示。使用中文文档与一键安装脚本。

- 平台：macOS 14/15（Apple Silicon 优先，兼容 Intel）
- 技术：Python 3.11+；GUI 用 Tkinter；CLI 用 argparse；声音用 afplay/osascript
- 目录结构：
  - 源码：`dfu_guide/{main,cli,gui,detector,guide,audio,utils}.py`
  - 脚本：`scripts/setup_macos.sh`、`scripts/run_gui.sh`、`scripts/run_cli.sh`
  - 日志：`logs/dfu_YYYYMMDD_HHMMSS.log`

## 快速开始（推荐）

1) 安装 Xcode Command Line Tools（若未安装）：

```bash
xcode-select --install || true
```

2) 一键创建虚拟环境并启动：

- 启动 GUI：

```bash
bash scripts/run_gui.sh
```

- 启动 CLI（示例：Face ID 机型家族引导）：

```bash
bash scripts/run_cli.sh guide --family face
```

第一次运行会自动创建并启用 `.venv`，无需额外依赖。

如需手动创建 venv，可执行：

```bash
bash scripts/setup_macos.sh
```

## 功能说明

- 自动检测（非阻塞）：后台轮询 `system_profiler SPUSBDataType` 与 `ioreg -p IOUSB -l`，综合判定设备为：
  - DFU 模式
  - 恢复模式（Recovery / iBoot）
  - 正常模式（普通连接）
  - 未连接 / 未知

- 机型族选择（4 组）：
  1) 6s/Home（有 Home 键）
  2) 7（侧边键 + 音量下）
  3) 8/SE2/SE3（点击音量上→下，长按侧边键，随后与音量下配合）
  4) Face ID（X–15，同 8/SE2/SE3 节奏）

- 逐秒指引：
  - 按机型族执行 8s/5s/10s 节奏
  - GUI 大字倒计时；CLI 实时倒计时输出
  - 蜂鸣每秒提示，支持可选中文语音提示（需 macOS 上可调用 osascript/say/afplay）

- 成功/失败：
  - 检测到 DFU：显示“成功进入 DFU 模式”并三声蜂鸣
  - 若为恢复模式：提示“在松开电源键的瞬间重试（关键时机）”

- 日志：
  - `logs/dfu_YYYYMMDD_HHMMSS.log` 自动记录状态变化与指引事件

## CLI 用法

```bash
# 查看实时状态
bash scripts/run_cli.sh watch

# 按机型族开始引导
bash scripts/run_cli.sh guide --family face         # 取值：home/7/8/se2/se3/face
bash scripts/run_cli.sh guide --family home --voice # 开启语音提示
bash scripts/run_cli.sh guide --family 7 --no-beep  # 关闭蜂鸣
```

参数说明：
- `--family` 机型族，支持：`home`、`7`、`8`/`se2`/`se3`、`face`
- `--voice` 开启语音提示（调用 osascript 或 say）
- `--no-beep` 关闭蜂鸣（默认开启）
- `--interval` 轮询间隔（秒，默认 0.5）

## GUI 用法

- 启动：`bash scripts/run_gui.sh`
- 在窗口中选择机型族、勾选语音/蜂鸣选项，点击“开始引导”
- 状态栏会实时显示“当前状态：DFU/恢复模式/正常/未连接”
- 倒计时区显示大字秒数与步骤说明

## 权限与说明

- 本工具仅调用系统自带的命令：`system_profiler`、`ioreg`、`osascript`、`afplay`/`say`
- 不涉及刷机/固件下载与设备数据操作
- 仅在本地创建日志文件于 `logs/` 目录

## 常见问题（FAQ）

1) 语音/蜂鸣没有声音？
   - 请确认 `osascript`/`afplay`/`say` 是否可执行；系统音量是否开启
   - GUI 中勾选“语音提示/蜂鸣提示”，CLI 使用 `--voice` 或去掉 `--no-beep`

2) 一直识别为“未连接”？
   - 请确认数据线与接口正常；尝试更换端口/线材
   - 在正常模式下，`系统设置→隐私与安全→定位与隐私` 可能涉及“信任此电脑”的提示，请在手机上点“信任”

3) 进入了恢复模式而非 DFU？
   - 关键在于“松开电源键的瞬间”，请严格按倒计时操作，必要时多尝试几次

## 开发说明

- 代码风格：尽量保持简洁、可读、不阻塞 UI
- GUI 与 CLI 共享核心逻辑（检测与引导）
- 在非 macOS 环境下，检测结果会返回 `UNKNOWN`，用于兼容开发/CI

## 可选：PyInstaller 打包

如果需要，可在本机运行：

```bash
# 安装
pip install pyinstaller
# 打包 CLI 或 GUI
pyinstaller -F -n dfu-guide-cli dfu_guide/cli.py
pyinstaller -w -F -n dfu-guide-gui dfu_guide/gui.py
```

打包产物会在 `dist/` 目录。
