# Skill 安全优化指南

> 本文档总结了将 Skill 发布到 ClawHub 平台前应进行的安全检查、优化方法，以及在实战中积累的踩坑经验。通过将"检查方法"与"避坑教训"按风险类别整合，帮助你在每次发布前做到全面自检。

---

## 📌 简介

当一个 Skill 从本地脚本变成公共平台上的 AI Agent 运行时，它不再只是"能用"，还必须满足**安全**、**合规**、**可信赖**三个标准。ClawHub 的安全扫描器会检查以下几类风险：

| 风险类别 | 描述 | 关联章节 |
|---------|------|---------|
| Prompt 注入 | 隐藏的 Unicode 控制字符篡改 LLM 指令 | 第二章 |
| 隐私泄露 | 网络请求传输敏感数据 | 第三章 |
| 依赖风险 | 引入未知或危险的第三方包 | 第四章 |
| 同意绕过 | 未经用户确认即执行敏感操作 | 第五章 |
| 敏感词误报 | 文件名或文档内容触发静态扫描 | 第六章 |
| 伦理合规 | 强制性商业逻辑缺乏透明说明 | 第七章 |

---

## 第一类：Unicode 控制字符 / Prompt Injection 防御

### 1.1 风险说明

Unicode 控制字符（如零宽字符）是**不可见**的特殊字符。它们可能在以下场景被悄悄带入文件：

- 从网页或富文本编辑器复制内容时粘贴进来
- 从 Word / Google Docs 等编辑器导出 Markdown 时带入
- 从聊天记录中复制粘贴时附带

攻击者可以利用这些字符进行 **Prompt Injection**——在用户看不见的地方注入额外指令，篡改 AI 对原始 Prompt 的理解。例如在指令末尾插入零宽字符+恶意指令，AI 读取时会将其视为原始指令的一部分。

安全扫描器（如 ClawHub 集成的 VirusTotal 等引擎）会将"存在 Unicode 控制字符"本身标记为可疑，无论是否真的有恶意注入。

### 1.2 检查方法

使用以下正则表达式检测所有 Unicode 控制字符：

```bash
node -e "const fs=require('fs');const c=fs.readFileSync('SKILL.md','utf8');const m=c.match(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u200B-\u200D\uFEFF]/g);console.log('Found:',m?.length||0,'control chars');"
```

**需要检测的字符范围：**

| 范围 | 说明 |
|------|------|
| `\x00-\x08` | NUL 至 BS 控制字符 |
| `\x0B\x0C` | 垂直制表符、换页符 |
| `\x0E-\x1F` | 设备控制字符 |
| `\x7F` | DEL 字符 |
| `\u200B-\u200D` | 零宽字符（Zero-Width Joiner / Space / Non-Joiner） |
| `\uFEFF` | BOM 字节顺序标记 |

### 1.3 清理方法

```bash
node -e "const fs=require('fs');const c=fs.readFileSync('SKILL.md','utf8');fs.writeFileSync('SKILL.md',c.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u200B-\u200D\uFEFF]/g,''));"
```

> **注意**：手动正则替换容易破坏文件结构（如遗漏冒号、损坏链接）。如果文件已损坏，**不要依赖正则逐行修复，而是重写整个文件**，确保所有文件名、链接、格式完整正确。

### 1.4 经验教训

- **SKILL.md** 和 **PROMPTS.md** 是核心提示词文件，必须在每次发布前检测并清理
- 仅清理 `SKILL.md` 不够——ClawHub 扫描器会扫描仓库中所有 Markdown 文件
- 建议在本地开发流程中加入自动化检测环节（参见第八章）

---

## 第二类：网络请求安全审查

### 2.1 风险说明

涉及第三方网络调用的 Skill 容易被标记为"可疑行为"，尤其当请求体中可能包含个人信息时。

### 2.2 检查步骤

1. 查找所有网络调用脚本（`fetch`、`http`、`axios`、`node-fetch` 等）
2. 确认请求体中是否包含 PII（姓名、手机号、身份证、地址等）
3. 检查第三方域名是否可信
4. 确认请求仅传输业务所需的最少数据

**合格示例** — 仅传输必要的业务 ID，不含任何个人信息：

```javascript
await this.apiClient.post('/skill/api/recommend/addpack', { itemIds })
```

**不合格示例** — 请求体中包含姓名和手机号：

```javascript
await fetch('/api/book', {
  method: 'POST',
  body: JSON.stringify({ name: '张三', phone: '13812345678', itemIds })
})
```

---

## 第三类：依赖项安全审查

### 3.1 检查方法

```bash
# 查看 package.json
cat package.json

# 查看所有传递依赖（flattened list）
npm list
```

### 3.2 风险信号

- 未知或非必要的依赖包
- 包含 `eval`、`child_process`、`crypto` 等危险模块（除非是明确需要的业务功能）
- 过时的依赖版本存在已知 CVE 漏洞

### 3.3 经验教训

ClawHub 扫描器会分析 `package.json` 和 `package-lock.json`。尽量保持依赖最小化——只引入确实需要的包。业务逻辑尽量使用 Node.js 内置模块（如 `fs`、`path`、`crypto`），避免引入不熟悉的第三方包。

---

## 第四类：用户同意策略的硬执行

### 4.1 风险说明

在 `SKILL.md` 或 `PROMPTS.md` 中写"发送二维码前需获得用户同意"，这只是**文档层面的承诺**。安全扫描器不信任纯文本的流程约束——只要脚本存在第三方网络通信，就需要在代码层面有阻断机制。

### 4.2 文档层面：隐私声明（必须包含）

在 `_meta.json` 的 `privacy` 字段中明确声明：

```yaml
privacy:
  auto_send_qr: false      # 不自动发送
  consent_required: true    # 需要用户同意
  qr_contains_personal_data: false
```

### 4.3 代码层面：硬执行参数（必须实现）

在脚本的命令行入口处强制要求 `--consent=true` 参数。如果调用方没有传递此参数，脚本必须**拒绝执行**并输出错误信息。

```javascript
const consentIndex = args.findIndex(
  arg => arg === '--consent=true' || arg === '--consent'
)
const hasConsent = consentIndex !== -1

if (consentIndex !== -1) {
  args.splice(consentIndex, 1)
}

if (args.length === 0 || !hasConsent) {
  console.log('\n📌 用法:')
  console.log('  node generate_qr_with_fallback.js --consent=true [output_path] [item029] [item131] ...')
  console.log('\n⚠️ 安全限制:')
  console.log('  必须提供 --consent=true 参数，确认已获得用户明确同意生成二维码。')
  if (!hasConsent && args.length > 0) {
    console.error('\n❌ 拒绝执行: 未提供 --consent=true 参数。在生成预约二维码前，必须征得用户同意。')
    process.exit(1)
  }
  return
}
```

调用示例：

```bash
node generate_qr_with_fallback.js --consent=true ./output item029 item131
```

### 4.4 经验教训

- "需要用户同意"如果只写在文档里，扫描器认为这是**流程建议**，不是安全约束
- 代码层的 `--consent=true` 向安全审查机制证明了"同意"是**程序强制执行**的
- 即使只有一步网络调用（如只传商品 ID），也必须加此参数

---

## 第五类：敏感文件排除与误报规避

### 5.1 必须排除的文件

| 文件 | 说明 |
|------|------|
| `DEBUG_MODE` | 测试环境标记，不应发布 |
| `.env` | 环境变量文件，包含密钥 |
| `*.log` | 日志文件，可能包含敏感信息 |
| `node_modules/` | 依赖包，通过 npm install 安装 |
| `FALSE_POSITIVE_REPORT.md` | 解释误报原因的文档 |

### 5.2 经验教训：避免触发"敏感词"误报

**现象**：曾创建了一个 `FALSE_POSITIVE_REPORT.md` 文件，试图解释"为什么 `calls-wmi` 是误报"。但扫描器即使在 Markdown 纯文本中检测到 `calls-wmi` 字符串，依然会触发病毒告警。

**教训**：静态安全扫描器是**基于字符串特征匹配**的，不会理解上下文。即使是在解释"这不是病毒"的文件中提到敏感特征码，扫描器也会报警。

**对策**：
- 彻底删除触发误报的解释性文档，不要保留在仓库中
- 不要在文件名中包含敏感关键词（如 `wmi`, `trojan`, `virus` 等）
- 不要在文档中详细描述攻击技术的实现细节（即使是以"安全研究"的名义）

---

## 第六类：业务逻辑的伦理合规

### 6.1 风险说明

当 Skill 包含可能引发用户反感的强制性商业逻辑时（如最低消费、强制捆绑），扫描器会将其标记为"政策/伦理问题"。这是比技术风险更高层次的要求：**AI 代理不能暗中强制用户做他们不知情的事情**。

### 6.2 检查清单

在发布前，问自己以下问题：

- [ ] Skill 是否存在最低消费、强制凑单等"隐性门槛"？
- [ ] 是否存在默认勾选或强制推荐的额外项目？
- [ ] 如果存在以上规则，是否在 Prompt 中向用户说明了原因？

### 6.3 透明化原则

如果业务规则确实必要（如"体检机构不接受低于 600 元的订单"），必须将其**转变为透明建议**，而不是自动执行：

**不合格做法**（暗中自动加单）：

```
系统自动将总价补足至 600 元。
```

**合格做法**（透明告知 + 用户确认）：

```
身高体重血压（item029）是体检的重要基线指标，如果没有选择，我建议添加。
由于合作体检机构对低于 600 元的订单不接单，不足时请告知用户原因。
```

在 `PROMPTS.md` 和 `SKILL.md` 中都要包含业务规则说明，向 AI 代理明确：这些补充推荐是**有据可查的必要项**，并且代理必须先解释原因，再做推荐。

---

## 第七类：安全验证脚本

建议在每个 Skill 的 `scripts/` 目录中添加 `validate_skill.js`，在本地开发流程中自动化安全检查：

```javascript
#!/usr/bin/env node
const fs = require('fs')
const path = require('path')

const CONTROL_CHAR_PATTERN = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u200B-\u200D\uFEFF]/g
const DANGEROUS_PATTERNS = [
  /eval\s*\(/,
  /exec\s*\(/,
  /child_process/,
  /process\.env\.(?!NODE_ENV)/
]

const SKILL_ROOT = path.resolve(__dirname, '..')
const FILES_TO_CHECK = [
  'SKILL.md',
  'PROMPTS.md',
  '_meta.json'
]

function checkFile(filePath) {
  if (!fs.existsSync(filePath)) return { path: filePath, errors: [] }
  const content = fs.readFileSync(filePath, 'utf8')
  const errors = []

  const controlChars = content.match(CONTROL_CHAR_PATTERN)
  if (controlChars) {
    errors.push(`⚠️  发现 ${controlChars.length} 个 Unicode 控制字符`)
  }

  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(content)) {
      errors.push(`⚠️  发现可疑模式: ${pattern}`)
    }
  }

  return { path: filePath, errors }
}

function main() {
  console.log('🔍 Skill 安全检查...\n')
  let hasErrors = false

  for (const file of FILES_TO_CHECK) {
    const result = checkFile(path.join(SKILL_ROOT, file))
    if (result.errors.length > 0) {
      hasErrors = true
      console.log(`❌ ${result.path}`)
      result.errors.forEach(e => console.log(`   ${e}`))
    }
  }

  if (hasErrors) {
    console.log('\n❌ 检查未通过，请修复以上问题后再发布。')
    process.exit(1)
  } else {
    console.log('✅ 所有检查通过。')
  }
}

main()
```

在本地运行：

```bash
node scripts/validate_skill.js
```

---

## 第八类：发布流程与常见错误处理

### 8.1 标准发布流程

```bash
# 1. 本地安全检查
node scripts/validate_skill.js

# 2. 提交到 Git
git add .
git commit -m "vX.Y.Z: 更新说明"

# 3. 推送到 GitHub
git push origin main

# 4. 发布到 ClawHub
clawhub publish "绝对路径" --version X.Y.Z
```

### 8.2 常见错误与解决方案

#### 错误 1：`Error: Path must be a folder`

**原因**：`clawhub publish` 命令不能仅传入 slug 名称，需要指定包含 `_meta.json` 的目录路径。

**解决**：使用完整路径或相对路径：

```bash
# ❌ 错误
clawhub publish health-checkup-recommender --version 4.1.0

# ✅ 正确（绝对路径）
clawhub publish "c:/IT/00 工具和探索/clawhub/health-checkup-recommender" --version 4.1.0

# ✅ 正确（相对路径）
clawhub publish "./health-checkup-recommender" --version 4.1.0
```

#### 错误 2：`Error: --version must be valid semver`

**原因**：版本号格式不符合语义化版本规范（Semantic Versioning）。

**解决**：确保使用 `MAJOR.MINOR.PATCH` 格式：

```bash
# ❌ 错误
clawhub publish ... --version 4.0.0.1
clawhub publish ... --version 4.1

# ✅ 正确
clawhub publish ... --version 4.1.3
```

同时更新 `_meta.json` 中的 `version` 字段保持一致。

#### 错误 3：PowerShell 中 `&&` 不是有效语句分隔符

**原因**：Windows PowerShell 5.x 不支持 Bash 风格的 `&&` 多命令分隔符。

**解决**：使用分号 `;` 分隔，或逐条执行：

```powershell
# ❌ 错误（PowerShell 5.x 中报错）
git add . && git commit -m "update" && git push

# ✅ 正确（使用分号分隔）
git add . ; git commit -m "update" ; git push

# ✅ 也正确（逐条执行）
git add .
git commit -m "update"
git push
```

---

## ✅ 第九类：发布前最终检查清单

在点击"发布"前，逐项核对以下清单：

**安全检查**

- [ ] `SKILL.md` 和 `PROMPTS.md` 中不包含 Unicode 控制字符
- [ ] 所有网络请求脚本已审查，确认只传输最小必要数据
- [ ] `package.json` 中的依赖均为必要且可信的包
- [ ] 涉及网络通信的脚本已实现 `--consent=true` 硬执行
- [ ] 已删除 `DEBUG_MODE`、`.env`、日志文件、`FALSE_POSITIVE_REPORT.md` 等敏感文件
- [ ] 不存在触发误报的文件名或内容（如敏感关键词）
- [ ] 所有强制性业务逻辑已在 Prompt 中透明化说明

**版本管理**

- [ ] `_meta.json` 中的 `version` 字段已更新为正确格式（`X.Y.Z`）
- [ ] `changelog` 字段已补充本次更新的说明

**发布准备**

- [ ] 代码已提交并推送至 GitHub 远程仓库
- [ ] `clawhub publish` 命令使用正确的绝对路径
- [ ] 版本号与 Git tag（如果使用）保持一致

---

## 🔗 相关资源

- [ClawHub 平台](https://clawhub.ai)
- [Unicode 控制字符参考](https://unicode-table.com/)
- [npm 安全最佳实践](https://docs.npmjs.com/about-npm)
- [语义化版本规范 (SemVer)](https://semver.org/lang/zh-CN/)

---

*最后更新：2026-04-06*
