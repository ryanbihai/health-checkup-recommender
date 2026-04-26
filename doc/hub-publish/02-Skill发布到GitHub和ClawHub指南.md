# Skill 发布到 GitHub 和 ClawHub 指南

> 本文档详细介绍如何将 Skill 同时发布到 GitHub 和 ClawHub 平台。

---

## 📋 前置准备

### 1. 工具准备

```bash
# 检查 Git
git --version

# 检查 clawhub CLI
clawhub --version

# 检查 npm（用于安装依赖）
npm --version
```

### 2. 环境要求

- GitHub 账户并创建了仓库
- ClawHub 账户
- `clawhub` CLI 已登录：`clawhub whoami`

### 3. ⚠️ 重要：确认 Skill Slug

**发布前必须确认要使用的 Slug**，避免创建重复的 Skill！

```bash
# 检查 Skill 是否已存在
clawhub inspect <slug>

# 列出你拥有的所有 Skill
clawhub search ""  # 或在网页上查看
```

**如果存在重复 Skill**，先删除旧版本：
```bash
# 删除重复的 Skill（软删除）
clawhub delete <重复的-slug>
```

---

## 🔄 发布流程总览

```
┌─────────────────────────────────────────────┐
│           发布流程                           │
├─────────────────────────────────────────────┤
│  1. 安全检查 → 2. 代码提交 → 3. GitHub Push  │
│           ↓                                  │
│  4. 版本更新 → 5. ClawHub Publish           │
└─────────────────────────────────────────────┘
```

---

## 第一步：本地安全检查

在发布前运行安全验证脚本：

```bash
cd health-checkup-recommender
node scripts/validate_skill.js
```

如果发现控制字符，清理后再继续：

```bash
node -e "const fs=require('fs');['SKILL.md','PROMPTS.md'].forEach(f=>{const c=fs.readFileSync(f,'utf8');fs.writeFileSync(f,c.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u200B-\u200D\uFEFF]/g,''));console.log('Cleaned:',f)})"
```

---

## 第二步：移除敏感文件

发布前必须删除不应公开的文件：

```bash
# 删除 DEBUG_MODE（测试环境标记）
rm -f DEBUG_MODE

# 或者在 .gitignore 中添加
echo "DEBUG_MODE" >> .gitignore
```

---

## 第三步：更新版本号

### ⚠️ 发布前必须检查现有版本

```bash
# 查看当前已发布的版本
clawhub inspect <slug>
```

**如果版本号冲突**（显示 "already exists"）：
- 使用更高的补丁版本号（如 1.4.1 → 1.4.2）
- 或使用 minor 版本号（如 1.4 → 1.5）

### 更新 `_meta.json`

```json
{
  "version": "4.1.0",
  "changelog": "本次更新的说明"
}
```

**同步更新 `SKILL.md` 的 YAML frontmatter**：

```yaml
---
name: your-skill-slug
version: 4.1.0  # ← 必须同步更新
description: ...
---
```

### 版本号规范（Semver）

| 版本格式 | 说明 |
|---------|------|
| `4.0.0` → `4.1.0` | 补丁版本（新功能兼容） |
| `4.0.0` → `5.0.0` | 主版本（破坏性变更） |
| `4.0.0` → `4.0.1` | 小补丁（Bug 修复） |

---

## 第四步：提交到 GitHub

### 4.1 初始化 Git（如果是新项目）

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
```

### 4.2 提交更改

```bash
git add SKILL.md PROMPTS.md _meta.json scripts/*.js
git commit -m "v4.1.0: 更新说明"
```

**⚠️ Git 未检测到文件变化？**

如果修改了文件但 `git status` 显示未更改，尝试以下方法：

```bash
# 方法1：强制刷新索引
git update-index --really-refresh <file>

# 方法2：直接强制添加
git add -f <file>

# 方法3：检查文件编码和行尾符
file <file>  # 检查是否有 BOM 或编码问题

# 方法4：完全重新暂存
git add -A
```

### 4.3 推送到 GitHub

```bash
git push origin main
```

---

## 第五步：发布到 ClawHub

### 5.1 登录验证

```bash
clawhub whoami
```

如果未登录，先登录：

```bash
clawhub login
```

### 5.2 发布命令

**⚠️ 必须使用 `--slug` 参数**：避免创建重复的 Skill！

```bash
clawhub publish "完整路径" --slug <你的-skill-slug> --version 4.1.0 --changelog "更新说明"
```

**示例**：

```bash
clawhub publish "c:/IT/00 工具和探索/clawhub/health-checkup-recommender" --slug health-checkup-recommender --version 4.1.0 --changelog "安全修复"
```

**⚠️ 版本号冲突处理**：

如果收到 "already exists" 错误：
```bash
# 使用更高的版本号重试
clawhub publish "path" --slug <slug> --version 4.1.1 --changelog "修复版本号冲突"
```

### 5.3 查看发布结果

```bash
clawhub inspect <slug>
```

**⚠️ 发布后版本未立即更新？**

这是正常现象！ClawHub 需要几秒到几分钟来索引新版本。等待 5-10 秒后再检查。

```bash
# 等待后重新检查
sleep 5 && clawhub inspect <slug>
```

---

## 第六步：验证发布

### 检查 ClawHub

```bash
clawhub search health-checkup-recommender
```

### 检查 GitHub

访问 `https://github.com/USERNAME/REPO`

---

## 📝 常用命令速查

| 操作 | 命令 |
|------|------|
| 登录 ClawHub | `clawhub login` |
| 查看登录状态 | `clawhub whoami` |
| 发布 Skill | `clawhub publish <path> --slug <slug> --version <ver>` |
| 检查 Skill | `clawhub inspect <slug>` |
| 删除 Skill | `clawhub delete <slug>` |
| 搜索 Skill | `clawhub search <query>` |
| 提交 Git | `git add . && git commit -m "msg"` |
| 推送 Git | `git push origin main` |

---

## ⚠️ 常见问题

### Q1: 版本号格式错误

```
Error: --version must be valid semver
```

**解决**：确保版本号符合 Semver 规范，如 `1.0.0`、`2.1.3`

### Q2: 路径错误

```
Error: Path must be a folder
```

**解决**：使用完整绝对路径，如 `"c:/path/to/skill"`

### Q3: 未登录

```
Error: Not authenticated
```

**解决**：运行 `clawhub login` 并在浏览器中完成授权

### Q4: Git 冲突

```
Error: failed to push some refs
```

**解决**：先 `git pull --rebase`，解决冲突后再 `git push`

### Q5: 版本号已存在

```
Error: version X.X.X already exists
```

**解决**：使用更高的版本号（如 1.4.1 → 1.4.2）重新发布

### Q6: Git 未检测到文件变化

修改了文件但 `git status` 显示未更改。

**解决**：
```bash
# 方法1：强制刷新索引
git update-index --really-refresh <file>

# 方法2：强制添加
git add -f <file>

# 方法3：完全重新暂存
git add -A
```

### Q7: 发布后版本未更新

`clawhub inspect` 仍显示旧版本号。

**原因**：ClawHub 索引有延迟（通常几秒到几分钟）

**解决**：等待 5-10 秒后重新检查

### Q8: 创建了重复的 Skill

同一套代码被发布了多次，产生多个 slug。

**原因**：发布时未指定 `--slug` 参数

**解决**：
```bash
# 1. 删除重复的 Skill
clawhub delete <重复的-slug>

# 2. 今后发布时务必使用 --slug
clawhub publish "path" --slug <正确的-slug> --version X.X.X
```

---

## 🔗 相关资源

- [ClawHub CLI 文档](https://clawhub.ai/docs/cli)
- [GitHub 官方文档](https://docs.github.com/)
- [Semver 版本规范](https://semver.org/lang/zh-CN/)

---

## 📂 示例：完整发布脚本

```bash
#!/bin/bash
# publish.sh - 一键发布脚本

VERSION="4.1.0"
SKILL_SLUG="health-checkup-recommender"
SKILL_PATH="health-checkup-recommender"
CHANGELOG="安全修复版本"

echo "🔍 检查当前版本..."
clawhub inspect ${SKILL_SLUG}

echo "🔍 运行安全检查..."
node scripts/validate_skill.js

echo "📦 提交到 Git..."
git add SKILL.md PROMPTS.md _meta.json scripts/*.js
git commit -m "v${VERSION}: ${CHANGELOG}"
git push origin main

echo "🚀 发布到 ClawHub..."
clawhub publish "${SKILL_PATH}" --slug "${SKILL_SLUG}" --version "${VERSION}" --changelog "${CHANGELOG}"

echo "⏳ 等待索引..."
sleep 5

echo "🔍 验证发布..."
clawhub inspect ${SKILL_SLUG}

echo "✅ 发布完成！"
```

---

*最后更新：2026-04-10*
