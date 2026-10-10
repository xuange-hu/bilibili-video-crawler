# bilibili-video-crawler

[![CI](https://github.com/xuange-hu/bilibili-video-crawler/actions/workflows/ci.yml/badge.svg)](https://github.com/xuange-hu/bilibili-video-crawler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB)](https://www.python.org)
[![Security](https://img.shields.io/badge/security-policy-brightgreen)](SECURITY.md)

> **仅供学习与研究** 的 B 站视频下载器示例：理解 WBI 签名、现代反爬与 Python 工程化。
> 详见 [SECURITY.md](SECURITY.md) 与 [NOTICE.md](NOTICE.md) —— 仅用于你拥有合法访问权限的内容，请遵守平台协议与著作权。

**English**: A Python crawler for Bilibili videos with local download support.
It is a **learning-oriented** example for understanding Bilibili's WBI signing, modern anti-bot strategies, and Python project structure. See [SECURITY.md](SECURITY.md) / [NOTICE.md](NOTICE.md): use only for content you are legitimately entitled to access, and respect the platform ToS and copyright.

---

## ✨ 特性 / Features

- **WBI 签名**：`wbi_sign.py` 完整实现 mixin key 计算与参数签名（`w_rid` = SHA-256）。
- **现代反爬**：随机 User-Agent、请求延迟、退避重试、403/404/429 专项异常。
- **工程化**：配置管理（`config.py`）、下载记录（`database.py`）、分级日志（`logger.py`）、CI 测试门禁。
- **安全合规**：已移除 `verify=False`（启用证书校验）、Cookie 仅注入请求头且**不打印原文**、`config.json` 已排除出版本库。

## 🚀 快速开始 / Quick start

```bash
pip install -r requirements.txt
cp config.example.json config.json   # 填入你自己的登录态 Cookie（可选）
python main.py                       # 按提示输入 BV 号批量下载
```

## 📚 文档 / Docs

- [USAGE_GUIDE.md](USAGE_GUIDE.md) — 详细使用指南
- [SECURITY.md](SECURITY.md) — 安全与合规边界
- [NOTICE.md](NOTICE.md) — 免责声明

## ⚠️ 合规提醒 / Compliance

本项目**不提供**对付费、大会员专属或 DRM 保护内容的破解能力，也不鼓励此类用途。
使用即表示你已阅读并理解上述声明。下载内容的合法性与著作权风险由使用者自行承担。

## 🧪 测试 / Tests

```bash
pytest tests -q
```
