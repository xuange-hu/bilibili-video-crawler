# 📚 B站视频爬虫 - 详细使用指南

> 本指南将手把手教你如何使用这个爬虫程序

---

## 📋 目录
1. [环境准备](#环境准备)
2. [安装步骤](#安装步骤)
3. [基本使用](#基本使用)
4. [命令详解](#命令详解)
5. [实际案例](#实际案例)
6. [常见问题](#常见问题)

---

## 🔧 环境准备

### 系统要求
- **操作系统**: Windows、macOS 或 Linux
- **Python**: 3.8 或更高版本
- **磁盘空间**: 至少1GB（用于存储视频）
- **网络**: 稳定的互联网连接

### 检查 Python 版本

#### Windows 用户
```bash
python --version
```

#### macOS/Linux 用户
```bash
python3 --version
```

如果输出版本号 3.8+，说明已安装。如果版本低于3.8，请到 [python.org](https://www.python.org/downloads/) 下载更新。

---

## 📥 安装步骤

### 第1步：克隆项目

#### 方法一：使用 Git（推荐）
```bash
git clone https://github.com/xuange-hu/bilibili-video-crawler.git
cd bilibili-video-crawler
```

#### 方法二：下载 ZIP
1. 访问 https://github.com/xuange-hu/bilibili-video-crawler
2. 点击绿色 "Code" 按钮
3. 选择 "Download ZIP"
4. 解压到本地文件夹
5. 打开命令行，进入该文件夹

---

### 第2步：创建虚拟环境（可选但推荐）

**什么是虚拟环境？**
虚拟环境可以隔离项目依赖，避免与系统其他Python项目冲突。

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

激活成功后，命令行前面会出现 `(venv)` 标志。

---

### 第3步：安装依赖

```bash
pip install -r requirements.txt
```

等待安装完成（可能需要1-2分钟）。

**输出示例：**
```
Successfully installed requests-2.31.0 BeautifulSoup4-4.12.2 click-8.1.7 ...
```

---

## 💻 基本使用

### 查看帮助信息

```bash
python main.py --help
```

**输出：**
```
usage: main.py [-h] [--bvid BVID] [--batch BATCH] [--download] [-o OUTPUT] [--init-config]

B站视频爬虫 - 获取视频信息并下载到本地

optional arguments:
  -h, --help            show this help message and exit
  --bvid BVID           视频BV号（例如: BV1oN411N7Jt）
  --batch BATCH         包含BV号列表的文件路径（每行一个BV号）
  --download            是否下载视频文件
  -o OUTPUT, --output OUTPUT
                        视频下载目录（默认: ./videos）
  --init-config         生成默认配置文件
```

---

## 🎯 命令详解

### 命令 1️⃣：获取视频信息（不下载）

```bash
python main.py --bvid BV1oN411N7Jt
```

**功能：**
- ✅ 获取视频标题、UP主、播放量等信息
- ✅ 信息保存到数据库
- ❌ 不下载视频文件

**输出示例：**
```
============================================================
获取视频信息: BV1oN411N7Jt
============================================================

📺 视频信息:
  标题: 【2024 Python最新教程】零基础学Python
  UP主: 张三
  播放量: 125000
  点赞: 5200
  硬币: 3100
  收藏: 8900
  分享: 450
  时长: 1850秒
  简介: 本课程从零开始讲解Python...

✓ 视频信息已保存到数据库
```

---

### 命令 2️⃣：获取并下载视频

```bash
python main.py --bvid BV1oN411N7Jt --download
```

**功能：**
- ✅ 获取视频信息
- ✅ 下载视频文件到 `./videos` 目录
- ✅ 记录下载信息到数据库

**输出示例：**
```
============================================================
获取视频信息: BV1oN411N7Jt
============================================================

📺 视频信息:
  标题: 【2024 Python最新教程】零基础学Python
  UP主: 张三
  播放量: 125000
  ...

下载视频到: ./videos

下载进度: 10.5% (52428800/500000000 bytes)
下载进度: 25.3% (126540000/500000000 bytes)
下载进度: 50.0% (250000000/500000000 bytes)
下载进度: 75.8% (379000000/500000000 bytes)
下载进度: 100.0% (500000000/500000000 bytes)

✓ 视频下载成功!
```

---

### 命令 3️⃣：下载到指定目录

```bash
python main.py --bvid BV1oN411N7Jt --download --output D:\MyVideos
```

**功能：**
- 下载视频到自定义目录
- 可以指定绝对路径或相对路径

**例子：**
```bash
# 下载到当前目录下的 my_videos 文件夹
python main.py --bvid BV1oN411N7Jt --download --output ./my_videos

# Windows: 下载到 D 盘
python main.py --bvid BV1oN411N7Jt --download --output D:\Videos

# macOS/Linux: 下载到用户主目录
python main.py --bvid BV1oN411N7Jt --download --output ~/Videos
```

---

### 命令 4️⃣：批量下载多个视频

**第一步：创建 BV号列表文件**

新建一个文本文件 `my_videos.txt`，内容如下：
```
BV1oN411N7Jt
BV1jJ411x7Cq
BV1jx411x7Gh
BV1234567890a
```

**第二步：执行批量下载**

```bash
python main.py --batch my_videos.txt --download
```

**输出示例：**
```
============================================================
批量处理 4 个视频
============================================================

[正在处理] 1/4: BV1oN411N7Jt
  标题: Python教程第1集
  下载进度: 100.0%
  ✓ 成功

[正在处理] 2/4: BV1jJ411x7Cq
  标题: Python教程第2集
  下载进度: 100.0%
  ✓ 成功

[正在处理] 3/4: BV1jx411x7Gh
  标题: Python教程第3集
  ✗ 失败: 无法获取下载链接

[正在处理] 4/4: BV1234567890a
  标题: Python教程第4集
  下载进度: 100.0%
  ✓ 成功

============================================================
批量处理完成
  成功: 3
  失败: 1
============================================================
```

---

## 💡 实际案例

### 案例 1：下载一个UP主的单个视频

**步骤：**

1. 打开 B站，找到想要的视频
2. 从URL中复制BV号

```
https://www.bilibili.com/video/BV1oN411N7Jt/?share_source=copy_web&vd_source=abc123
                                    ^^^^^^^^^^^^^^
                                    这就是BV号
```

3. 运行命令：
```bash
python main.py --bvid BV1oN411N7Jt --download
```

4. 等待下载完成，视频会保存在 `./videos` 目录

---

### 案例 2：批量下载某个UP主的多个视频

**步骤：**

1. 找到该UP主的所有视频链接
2. 提取所有BV号，创建文件 `up_videos.txt`
3. 运行命令：

```bash
python main.py --batch up_videos.txt --download --output ./my_favorites
```

4. 所有视频会下载到 `./my_favorites` 目录

---

### 案例 3：查看已下载视频信息

下载后，视频信息保存在 `data.db` 数据库中。

**查看数据库内容：**

```bash
# 需要安装 sqlite3（通常已预装）
sqlite3 data.db "SELECT title, views, likes FROM videos LIMIT 5;"
```

**输出：**
```
【2024 Python最新教程】零基础学Python|125000|5200
Python高级技巧|89000|3500
Django框架完整教程|156000|6700
...
```

---

## ❓ 常见问题

### Q1：什么是 BV号？

**A：** BV号是B站每个视频的唯一标识符，格式为 `BV` + 10位字母数字。

**如何找到BV号？**
1. 打开视频页面
2. 查看URL，例如：`https://www.bilibili.com/video/BV1oN411N7Jt/`
3. BV号就是 `BV1oN411N7Jt`

---

### Q2：为什么下载速度很慢？

**A：** 可能原因：

1. **网络问题**
   - 检查网络连接
   - 换个WiFi或移动网络试试

2. **B站限速**
   - 这是正常的，B站会限制单个连接的速度
   - 可以修改 `config.json` 中的 `request_delay`

3. **时间**
   - 高峰期（晚上7-10点）会更慢
   - 建议在非高峰期下载

**修改配置加快速度：**

编辑 `config.json`：
```json
{
  "request_delay": 0.5,  // 改为 0.5 秒
  ...
}
```

---

### Q3：下载失败提示 "无法获取下载链接"？

**A：** 可能原因：

1. **BV号错误**
   - 检查BV号是否正确

2. **视频被删除**
   - 视频已被UP主删除

3. **地域限制**
   - 某些视频可能有地域限制，无法下载

4. **网络问题**
   - 重新尝试下载

---

### Q4：可以恢复已删除的视频吗？

**A：** 不能。爬虫只能下载当前可访问的视频。如果视频已被删除或设为私密，则无法下载。

---

### Q5：下载的视频存在哪里？

**A：** 默认存放在项目目录下的 `videos` 文件夹中。

**打开查看：**
- Windows: 双击 `videos` 文件夹
- macOS/Linux: 打开终端，输入 `open videos`

---

### Q6：怎样修改下载目录？

**方法 1：命令行指定**
```bash
python main.py --bvid BV1oN411N7Jt --download --output D:\MyVideos
```

**方法 2：修改配置文件**

编辑 `config.json`：
```json
{
  "download_dir": "D:\\MyVideos",  // Windows
  ...
}
```

或 macOS/Linux：
```json
{
  "download_dir": "/Users/username/Videos",
  ...
}
```

---

### Q7：如何生成默认配置文件？

**A：** 运行以下命令：

```bash
python main.py --init-config
```

会生成一个 `config.json` 文件，包含所有可配置项。

---

### Q8：程序如何处理重复下载？

**A：** 如果已下载过同一个视频：
- 视频文件会被覆盖
- 数据库会更新下载记录

如果想避免重复，建议：
1. 检查是否已下载
2. 使用不同的下载目录

---

### Q9：可以在后台运行吗？

**A：** 可以。

**Windows 后台运行：**
```bash
start python main.py --bvid BV1oN411N7Jt --download
```

**macOS/Linux 后台运行：**
```bash
nohup python main.py --bvid BV1oN411N7Jt --download &
```

---

### Q10：如何查看日志？

**A：** 日志文件保存在 `logs` 目录中。

**查看最新日志：**

```bash
# Windows
type logs\*.log

# macOS/Linux
tail -f logs/*.log
```

---

## 📊 数据库说明

爬虫会自动创建 `data.db` 文件，包含两个表：

### videos 表
| 字段 | 说明 | 例子 |
|------|------|------|
| bvid | 视频BV号 | BV1oN411N7Jt |
| title | 视频标题 | Python教程 |
| duration | 时长（秒） | 1850 |
| views | 播放量 | 125000 |
| likes | 点赞数 | 5200 |
| coins | 硬币数 | 3100 |
| up_name | UP主名称 | 张三 |

### downloads 表
| 字段 | 说明 | 例子 |
|------|------|------|
| bvid | 视频BV号 | BV1oN411N7Jt |
| file_path | 文件路径 | ./videos/Python教程.mp4 |
| file_size | 文件大小 | 500000000 |
| status | 下载状态 | success/failed |
| completed_at | 完成时间 | 2025-05-30 14:30:00 |

---

## 🎓 常用命令速查表

| 需求 | 命令 |
|------|------|
| 获取视频信息 | `python main.py --bvid BV1oN411N7Jt` |
| 下载单个视频 | `python main.py --bvid BV1oN411N7Jt --download` |
| 下载到指定目录 | `python main.py --bvid BV1oN411N7Jt --download --output ./my_videos` |
| 批量下载 | `python main.py --batch videos.txt --download` |
| 生成配置文件 | `python main.py --init-config` |
| 查看帮助 | `python main.py --help` |

---

## 🆘 获取帮助

遇到问题？

1. **查看日志文件** - `logs` 目录中有详细的错误信息
2. **检查BV号** - 确保BV号格式正确
3. **尝试重新下载** - 有时网络问题会自动重试
4. **查看 README.md** - 有更多技术细节

---

## ✅ 成功检查清单

使用前确认：

- [ ] Python 版本 3.8+
- [ ] 已安装依赖 `pip install -r requirements.txt`
- [ ] 有足够的磁盘空间
- [ ] 网络连接正常
- [ ] 获取了正确的BV号

---

**现在你已经掌握了所有使用方法，开始下载你喜欢的B站视频吧！** 🎉

