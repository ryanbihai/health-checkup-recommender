# 🛡️ 安全审核与隐私说明 (Security Audit & Privacy)

本文档是为了回应静态安全扫描器对于第三方网络调用、依赖项、以及本地文件读取的关切而编写的正式声明。

---

## 1. 脚本行为矩阵（完整透明说明）

| 脚本 | 网络请求 | 本地文件读取 | 传输数据 | PII |
|------|---------|-------------|---------|-----|
| `verify_items.js` | ❌ 无 | ✅ `checkup_items.json`（只读） | 无 | ❌ 无 |
| `calculate_prices.js` | ❌ 无 | ✅ `checkup_items.json`（只读） | 无 | ❌ 无 |
| `check_conflicts.js` | ❌ 无 | ❌ 无 | 无 | ❌ 无 |
| `sync_items.js` | ✅ 有 | ❌ 无 | `{ itemIds: [...] }` | ❌ 无 |
| `generate_qr.js` | ❌ 无 | ✅ 写二维码图片 | 无 | ❌ 无 |

### 1.1 纯本地脚本（无网络）

**verify_items.js**
- 功能：验证体检项目 ID 有效性、检测冲突项
- 数据来源：仅读取 `reference/checkup_items.json`
- 输出：项目有效性结果和价格

**calculate_prices.js**
- 功能：计算套餐总价
- 数据来源：仅读取 `reference/checkup_items.json`
- 输出：价格明细和总价

**check_conflicts.js**
- 功能：检测同类父子项冲突（如肝功能11项 vs 肝功能15项）
- 数据来源：无外部依赖
- 输出：冲突检测结果

**generate_qr.js**
- 功能：生成本地二维码图片
- 数据来源：无
- 输出：PNG 图片文件到本地

### 1.2 网络脚本（sync_items.js）

**唯一会发起网络请求的脚本**

```
端点：https://pe.ihaola.com.cn/skill/api/recommend/addpack
方法：POST
Content-Type: application/json
```

**请求Payload（唯一传输内容）**：
```json
{
  "itemIds": ["item029", "item131", "item173"]
}
```

**保证**：
- ❌ 不传输姓名
- ❌ 不传输手机号
- ❌ 不传输身份证号
- ❌ 不传输任何可识别个人的信息
- ✅ 仅传输脱敏的体检项目 ID

**响应**：
```json
{
  "welfareid": "wxxxxx",
  "ruleid": "rxxxxx"
}
```

这两个 ID 用于生成二维码，扫码后用户在 ihaola 网站上自行填写个人信息。

---

## 2. 二维码内容说明

二维码仅包含以下参数：
```
https://www.ihaola.com.cn/launch/haola/pe?urlsrc=brief&welfareid=wxxxxx&ruleid=rxxxxx
```

**二维码中不包含**：
- 姓名 ❌
- 手机号 ❌
- 身份证号 ❌
- 年龄/性别 ❌
- 体检结果 ❌

用户在扫码后跳转 H5 页面，自行填写预约信息。

---

## 3. 用户同意强制机制

所有涉及用户数据的操作必须携带 `--consent=true` 参数：

```bash
# 同步项目（需要同意）
node scripts/sync_items.js --consent=true item029 item131

# 生成二维码（需要同意）
node scripts/generate_qr.js --consent=true output.png w123 r456
```

无此参数时脚本拒绝执行并报错。

---

## 4. 本地文件系统访问声明

- **已修复**：旧版本 `config/api.js` 检查 `.env` 文件已被移除
- **当前实现**：仅使用 `process.env.NODE_ENV` 判断环境，无任何本地文件读取
- **配置文件**：`reference/` 目录下的 JSON 文件是 Skill 数据包的一部分，非敏感配置

---

## 5. 第三方服务商隐私政策

- **服务商**：`ihaola.com.cn`（北京聚合科技有限公司）
- **数据处理**：用户在扫码后与 ihaola 平台直接交互，遵循其隐私政策
- **本 Skill**：仅生成预约链接，不存储、不处理任何个人数据

---

## 6. 依赖项与安装规范

| 依赖 | 用途 | 声明位置 |
|------|------|---------|
| `qrcode` (npm) | 生成二维码图片 | `package.json` + `_meta.json` |
| `qrcode` (pip) | Python 备用脚本 | `_meta.json` |

---

*最后更新：2026-04-07*