# 跨平台字体配置

程序需要三种字体来生成 PDF：

| 字体 | 注册名 | 用途 |
|------|--------|------|
| 黑体 | `SimHei` | 标题 |
| 宋体 | `SimSun` | 正文 |
| Times New Roman | `TimesNewRoman` | 英文字符 |

## 字体查找优先级

程序按以下顺序查找字体文件：

<div class="result" markdown>

1. **命令行参数** — `--font-simhei`、`--font-simsun`、`--font-times`
2. **环境变量** — `NEWSPAPER_FONT_SIMHEI`、`NEWSPAPER_FONT_SIMSUN`、`NEWSPAPER_FONT_TIMES`
3. **指定字体目录** — `--font-dir /path/to/fonts/`
4. **系统字体目录** — 自动搜索 Windows / Linux / macOS 标准字体路径
5. **开源 CJK 回退** — Noto CJK、文泉驿、思源黑体等

</div>

优先级高的找到后就不再往下查找。

## 手动指定字体

=== "命令行参数"

    ```bash
    python jfjb.py \
      --font-simhei /path/to/NotoSansCJK-Bold.otf \
      --font-simsun /path/to/NotoSerifCJK-Regular.otf \
      --font-times /path/to/times.ttf
    ```

=== "环境变量"

    ```bash
    export NEWSPAPER_FONT_SIMHEI=/path/to/simhei.ttf
    export NEWSPAPER_FONT_SIMSUN=/path/to/simsun.ttf
    export NEWSPAPER_FONT_TIMES=/path/to/times.ttf
    python jfjb.py
    ```

=== "字体目录"

    ```bash
    python jfjb.py --font-dir /path/to/my-fonts/
    ```

    程序会在该目录中递归搜索字体文件名。

## 各平台字体位置

程序自动搜索以下目录：

=== "Linux"

    - `/usr/share/fonts`
    - `/usr/local/share/fonts`
    - `~/.fonts`
    - `~/.local/share/fonts`

=== "macOS"

    - `/Library/Fonts`
    - `/System/Library/Fonts`
    - `~/Library/Fonts`

=== "Windows"

    - `%SystemRoot%\Fonts`（通常 `C:\Windows\Fonts`）
    - `%LOCALAPPDATA%\Microsoft\Windows\Fonts`

## 回退字体文件名

如果未手动指定，程序会搜索以下文件名（按优先级）：

**SimHei（黑体）**

`simhei.ttf` → `NotoSansCJKsc-Bold.otf` → `SourceHanSansSC-Bold.otf` → `WenQuanYiZenHei.ttf`

**SimSun（宋体）**

`simsun.ttc` → `NotoSerifCJKsc-Regular.otf` → `NotoSansCJKsc-Regular.otf` → `SourceHanSerifSC-Regular.otf`

**Times New Roman**

`times.ttf` → `LiberationSerif-Regular.ttf` → `DejaVuSerif.ttf` → `FreeSerif.ttf`

!!! note "Times New Roman 未找到"

    如果找不到 Times New Roman，英文字符会使用中文字体渲染，效果可能不够理想。建议安装 Liberation Serif 作为替代：

    ```bash
    # Ubuntu/Debian
    sudo apt install fonts-liberation
    ```
