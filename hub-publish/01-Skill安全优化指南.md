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
- 仅清理 `SKILL.md` 不够——ClawHub 扫描器会扫描仓库中**所有 Markdown 文件**（包括 `README.md`、`CHANGELOG.md` 等），并在报告中统一归类为"SKILL.md 发现风险"。**实际操作中，在 `README.md` 中发现了一个 `\u200D`（零宽连字符），也会导致 `SKILL.md` 被标记**
- 建议在本地开发流程中加入自动化检测环节（参见第七章）

---

## 第二类：网络请求安全审查

### 2.1 风险说明

涉及第三方网络调用的 Skill 容易被标记为"可疑行为"，尤其当请求体中可能包含个人信息时。

### 2.2 检查步骤

1. 查找所有网络调用脚本（`fetch`、`http`、`axios`、`node-fetch` 等）
2. 确认请求体中是否包含 PII（姓名、手机号、身份证、地址等）
3. 检查第三方域名是否可信
4. 确认请求仅传输业务所需的最少数据

**代码层面：必须在 fetch 调用处写入隐私声明注释**

扫描器会分析脚本源码。如果脚本中有网络调用，仅有文档层面的隐私声明是不够的——在 `fetch` 的上方应补充明确的隐私说明注释，让静态分析工具能识别到"设计意图"：

```javascript
// 安全与隐私声明：
// 本请求仅传输脱敏的项目ID（如 ['item029', 'item131']），不包含任何个人身份信息（PII）。
// 数据仅用于在服务器暂存体检项目，生成脱敏的福利ID（welfareid/ruleid）。
// 用户的真实个人信息将在扫码后由用户自行在第三方平台授权提供。
const response = await fetch(url, { method: 'POST', body: JSON.stringify(data) })
```

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

### 2.3 脚本行为矩阵（透明化声明）

扫描器无法完全解析所有脚本代码时，会对"未完全可见"的代码产生疑虑。建议在 `SECURITY_AUDIT.md` 中提供每个脚本的行为矩阵，明确说明：

| 脚本 | 网络请求 | 本地文件读取 | 传输数据 | PII |
|------|---------|-------------|---------|-----|
| `verify_items.js` | ❌ 无 | ✅ 只读 JSON | 无 | ❌ 无 |
| `calculate_prices.js` | ❌ 无 | ✅ 只读 JSON | 无 | ❌ 无 |
| `sync_items.js` | ✅ 有 | ❌ 无 | `{ itemIds: [...] }` | ❌ 无 |
| `generate_qr.js` | ❌ 无 | ✅ 写图片 | 无 | ❌ 无 |

**矩阵说明示例**：
```markdown
### sync_items.js（唯一网络脚本）
- 端点：`https://pe.ihaola.com.cn/skill/api/recommend/addpack`
- 方法：POST
- 请求体：`{ "itemIds": ["item029", "item131"] }`
- 不传输：姓名、手机号、身份证号
- 响应：`{ "welfareid": "wxxxxx", "ruleid": "rxxxxx" }`
```

### 2.4 经验教训

- **元数据权限声明**：在 `_meta.json` 中必须显式声明所需的网络权限，例如：
  ```json
  "permissions": {
    "network": ["https://*.ihaola.com.cn", "http://*.ihaola.com.cn"]
  }
  ```
- **编写安全审计文档**：如果扫描器认为关键代码路径（如 `sync_items.js`）缺乏透明度，建议在仓库中补充 `SECURITY_AUDIT.md`。在该文档中详细说明每个代码路径（成功/回退/错误）中传输的具体字段，并解释第三方服务商的隐私政策，能有效提升人工或自动化审查的通过率。
- **多语言脚本检查**：不仅检查 JavaScript/TypeScript，也要检查 Python、Shell 等脚本中的文件读取行为（如 `os.path.exists()`、`test -f` 等）

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

- ClawHub 扫描器会分析 `package.json` 和 `package-lock.json`。尽量保持依赖最小化——只引入确实需要的包。业务逻辑尽量使用 Node.js 内置模块（如 `fs`、`path`、`crypto`），避免引入不熟悉的第三方包。
- **显式声明依赖和安装规范**：注册表元数据（`_meta.json`）与代码库应该保持一致。如果代码中用到了第三方包（如 `qrcode`），必须在 `_meta.json` 中显式声明 `dependencies` 和 `install`，否则会被标记为"未列出运行时依赖项"。
  ```json
  "dependencies": {
    "npm": ["qrcode"]
  },
  "install": "npm install"
  ```

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
- **所有涉及网络调用的脚本**都需要加 `--consent=true`，不仅仅是二维码生成脚本。实际操作中，`sync_items.js`（项目同步接口）也需要同样的硬阻断机制
- 在发起网络请求的代码处，应补充明确的隐私声明注释，让扫描器能看到"设计意图"：
  ```javascript
  // 安全与隐私声明：
  // 本请求仅传输脱敏的项目ID（如 ['item029', 'item131']），不包含任何个人身份信息（PII）。
  // 数据仅用于在服务器暂存体检项目，生成脱敏的福利ID（welfareid/ruleid）。
  // 用户的真实个人信息将在扫码后由用户自行在第三方平台授权提供。
  ```

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
| `*.png` / `*.jpg` | 测试生成的图片文件 |

### 5.2 创建 .gitignore

```gitignore
# Test/demo output files
*.png
*.jpg
*.jpeg
*.gif

# Environment files
.env
.env.*
!.env.example

# Logs
*.log
logs/

# Node
node_modules/

# OS
.DS_Store
Thumbs.db
```

### 5.3 文件读取一致性检查

**常见问题**：SKILL.md 声明"不读取本地敏感文件"，但代码中使用了文件检查：

```javascript
// ❌ 错误：会触发"声明与实现不一致"告警
const envFilePath = path.join(__dirname, '..', '.env')
if (fs.existsSync(envFilePath)) {
  return 'dev'
}
```

**正确做法**：使用标准环境变量

```javascript
// ✅ 正确：仅使用 NODE_ENV，无任何文件读取
if (process.env.NODE_ENV === 'development') {
  return 'dev'
}
```

**Python 脚本同样适用**：

```python
# ❌ 错误
if os.path.exists('DEBUG_MODE'):
    return 'https://t.ihaola.com.cn'

# ✅ 正确
import os
if os.environ.get('NODE_ENV') == 'development':
    return 'https://t.ihaola.com.cn'
```

### 5.4 经验教训：避免触发"敏感词"误报

**现象**：曾创建了一个 `FALSE_POSITIVE_REPORT.md` 文件，试图解释"为什么 `calls-wmi` 是误报"。但扫描器即使在 Markdown 纯文本中检测到 `calls-wmi` 字符串，依然会触发病毒告警。

**教训**：静态安全扫描器是**基于字符串特征匹配**的，不会理解上下文。即使是在解释"这不是病毒"的文件中提到敏感特征码，扫描器也会报警。

**对策**：
- 彻底删除触发误报的解释性文档，不要保留在仓库中
- 不要在文件名中包含敏感关键词（如 `wmi`, `trojan`, `virus` 等）
- 不要在文档中详细描述攻击技术的实现细节（即使是以"安全研究"的名义）

### 5.5 经验教训：文件系统读取权限

**现象**：如果在 `SKILL.md` 中声明了"不读取本地敏感文件"，但代码中却使用了 `fs.existsSync('DEBUG_MODE')` 来判断环境，扫描器会将其标记为"与声明相矛盾的文件系统读取"。

**对策**：
- **移除所有非必要的 `fs` 读取**：尤其是针对配置或环境变量的判断。
- **使用标准环境变量**：将 `fs.existsSync('DEBUG_MODE')` 替换为 `process.env.NODE_ENV === 'development'`。这样可以实现 100% 纯净运行，无需读取任何本地文件即可区分环境。
- **谨慎声明**：不要在 `SKILL.md` 中做过于绝对的承诺（如"不读取任何文件"），改为说明"仅在必要时读取自身配置文件"，以防被挑刺。
- **多语言一致**：Python、Shell 等脚本中同样要避免文件检查，使用 `os.environ.get()` 或 `test -z "$NODE_ENV"`

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
  { pattern: /eval\s*\(/, message: '发现动态代码执行' },
  { pattern: /exec\s*\(/, message: '发现命令执行' },
  { pattern: /child_process/, message: '发现子进程模块引用' },
  { pattern: /process\.env\.(?!NODE_ENV)/, message: '发现敏感环境变量访问' },
]

const SKILL_ROOT = path.resolve(__dirname, '..')
const FILES_TO_CHECK = [
  'SKILL.md',
  'PROMPTS.md',
  'README.md',
  '_meta.json',
  'SECURITY_AUDIT.md',
  'config/api.js',
  'scripts/sync_items.js',
  'scripts/generate_qr.js',
  'scripts/verify_items.js',
  'scripts/calculate_prices.js'
]

function checkFile(filePath) {
  if (!fs.existsSync(filePath)) return { path: filePath, errors: [] }
  const content = fs.readFileSync(filePath, 'utf8')
  const errors = []

  const controlChars = content.match(CONTROL_CHAR_PATTERN)
  if (controlChars && controlChars.length > 0) {
    errors.push(`⚠️  发现 ${controlChars.length} 个隐藏的 Unicode 控制字符`)
  }

  for (const { pattern, message } of DANGEROUS_PATTERNS) {
    if (pattern.test(content)) {
      errors.push(`❌ ${message}`)
    }
  }

  return { path: filePath, errors }
}

function main() {
  console.log('🔍 技能安全验证\n')
  console.log('='.repeat(50))

  let hasIssues = false

  for (const file of FILES_TO_CHECK) {
    const filePath = path.join(SKILL_ROOT, file)
    if (!fs.existsSync(filePath)) continue

    console.log(`\n📄 检查: ${file}`)
    const issues = checkFile(filePath)

    if (issues.length === 0) {
      console.log('   ✅ 无问题')
    } else {
      hasIssues = true
      for (const issue of issues) {
        console.log(`   ${issue}`)
      }
    }
  }

  console.log('\n' + '='.repeat(50))

  if (hasIssues) {
    console.log('\n❌ 验证失败：发现安全问题')
    process.exit(1)
  } else {
    console.log('\n✅ 验证通过：所有文件安全')
    process.exit(0)
  }
}

if (require.main === module) {
  main()
}

module.exports = { checkFile, CONTROL_CHAR_PATTERN }
```

**关键改进**：
1. **不检查自身**：`FILES_TO_CHECK` 不包含 `validate_skill.js`，避免自检误报
2. **消息更友好**：使用描述性消息而非直接显示正则
3. **覆盖关键脚本**：检查所有涉及网络或配置的脚本

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
- [ ] 所有 Markdown 文件（包括 README.md、SECURITY_AUDIT.md）无 Unicode 控制字符
- [ ] **代码声明一致性**：SKILL.md 中的隐私声明与代码实现一致
- [ ] **无本地文件读取**：所有脚本（JS/Python/Shell）使用 `NODE_ENV` 环境变量，无 `fs.existsSync()`、`os.path.exists()` 等文件检查
- [ ] 所有网络请求脚本已审查，确认只传输最小必要数据
- [ ] `package.json` 中的依赖均为必要且可信的包
- [ ] 涉及网络通信的脚本已实现 `--consent=true` 硬执行
- [ ] 已删除 `DEBUG_MODE`、`.env`、日志文件、`FALSE_POSITIVE_REPORT.md` 等敏感文件
- [ ] 不存在触发误报的文件名或内容（如敏感关键词）
- [ ] 所有强制性业务逻辑已在 Prompt 中透明化说明

**文档完整性**

- [ ] `SECURITY_AUDIT.md` 包含脚本行为矩阵（每个脚本的网络请求、本地文件读取、PII 传输情况）
- [ ] `SKILL.md` 安全声明中明确说明"仅 X 脚本发起网络请求"
- [ ] `validate_skill.js` 不检查自身，避免自检误报

**版本管理**

- [ ] `_meta.json` 中的 `version` 字段已更新为正确格式（`X.Y.Z`）
- [ ] `changelog` 字段已补充本次更新的说明

**发布准备**

- [ ] 已创建 `.gitignore` 排除测试文件、日志、node_modules
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

*最后更新：2026-04-07*

---

## 📝 实战案例：从"可疑"到"通过" (2026-04-07)

### 遇到的问题

健康体检推荐 Skill 发布后收到 OpenClaw "可疑"告警：

1. **声明与实现不一致**：SKILL.md 声称"不读取本地敏感文件"，但 `config/api.js` 检查 `.env` 文件
2. **Python 脚本遗漏**：`generate_qr.py` 中同样检查 `DEBUG_MODE` 文件
3. **脚本行为不透明**：扫描器无法确认脚本是否会发送 PII
4. **validate_skill.js 自检误报**：自带的危险模式检测被静态扫描器标记

### 修复措施

| 问题 | 修复 |
|------|------|
| `config/api.js` 检查 `.env` | 移除 `fs.existsSync`，改用 `process.env.NODE_ENV` |
| `generate_qr.py` 检查 `DEBUG_MODE` | 移除 `os.path.exists`，改用 `os.environ.get('NODE_ENV')` |
| 脚本行为不透明 | 新增 `SECURITY_AUDIT.md` 脚本行为矩阵 |
| SKILL.md 声明模糊 | 明确说明"仅 sync_items.js 发起网络请求" |
| 测试文件暴露 | 创建 `.gitignore` 排除 `*.png`、日志等 |

### 版本迭代

```
v4.2.1: 移除 .env 检查，统一 NODE_ENV
v4.2.2: 新增脚本行为矩阵、.gitignore
v4.2.3: 修复 generate_qr.py 的 DEBUG_MODE 检查
```

### 关键教训

1. **多语言一致性**：检查 JavaScript 时别忘了 Python、Shell 脚本
2. **文档即代码**：SECURITY_AUDIT.md 是给扫描器看的"第二层代码"
3. **环境判断只用环境变量**：`NODE_ENV` 是唯一正确的环境判断方式
4. **测试文件不进仓库**：`.gitignore` 是安全的基本保障
