# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/) 约定，版本号参考 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-10-15

### Quality
- 新增静态类型门禁：`mypy.ini` + CI `typecheck` 作业（增量式接入，覆盖
  config / logger / database / wbi_sign，随 crawler.py 拆分推进再扩大）。
- `config.py`、`logger.py`、`database.py`、`wbi_sign.py` 补全类型注解。
- 修复 `wbi_sign.fetch_keys` 中 list/str 变量复用导致的类型冲突（改用独立匹配变量）。

### Fixed
- **配置文件损坏不再崩溃**：非法 JSON、或顶层不是 JSON 对象时回退默认配置
  （此前 `self.config.get` 会因非 dict 而崩溃）。
- **Logger 健壮性**：`log_dir` 缺失时回退 `./logs`（此前 `os.makedirs(None)` 崩溃）；
  `log_level` 非法回退 INFO；日志目录不可写时退化为仅控制台输出而不抛异常。

### Tests
- 新增 `tests/test_config_robustness.py`（10 例），测试总数 30 → 40。

## [0.2.0] - 2026-10-11

### Security
- 移除 `verify=False` 的 TLS 校验绕过，强制服务端证书校验。
- 新增 `SECURITY.md` 安全披露政策与 `NOTICE.md` 合规/版权声明。

### Quality
- 将裸 `except:` 收紧为具体异常类型，异常细节降级为调试日志。
- 新增网络层集成测试（`tests/test_network.py`，mock `requests.Session`）：
  覆盖 403 / 404 / 429 / API 限流(-412) / Cookie 过期(-401) / 非 JSON 响应 / 超时 / 断连等分支。
- CI 加入 `pytest` 冒烟 + 网络测试。

### Docs
- `README.md` 改写为中英双语，明确"仅供学习研究"的使用边界与法律责任。

## [0.1.0] - 早期版本
- 基础 B 站视频爬取能力：WBI 签名、配置加载、SQLite 记录、本地下载。
