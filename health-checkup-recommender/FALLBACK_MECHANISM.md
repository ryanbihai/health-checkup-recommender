# 📱 二维码生成降级机制说明

> **版本**: v3.9.0
> **更新时间**: 2026-04-05

---

## 🎯 问题背景

在之前的版本中，二维码生成依赖 `sync_items.js` 接口来获取个性化的 `welfareid` 和 `ruleid`。当接口返回 404 错误时，整个流程会失败，导致无法生成二维码。

**问题场景**：
- 接口服务器维护/升级
- 网络连接不稳定
- 接口限流/熔断
- 服务暂时不可用

---

## 💡 解决方案

新增 **智能降级脚本** `generate_qr_with_fallback.js`，实现：

1. ✅ **优先尝试**：调用接口获取个性化参数
2. ✅ **自动降级**：接口失败时使用默认参数
3. ✅ **100% 可用**：无论接口状态如何，都能生成二维码
4. ✅ **透明提示**：清晰告知用户当前使用的参数来源

---

## 🔧 技术实现

### 核心逻辑

```javascript
async function smartGenerateQR(outputPath, itemIds) {
  // 1. 尝试调用接口
  const result = await trySyncItems(itemIds)

  // 2. 判断是否成功
  if (result && result.welfareid && result.ruleid) {
    // 3a. 成功：使用个性化参数
    return await generateQR(outputPath, result)
  } else {
    // 3b. 失败：自动降级为默认参数
    return await generateFallbackQR(outputPath, itemIds)
  }
}
```

### 支持的接口返回格式

```javascript
// 格式1：直接返回
{ welfareid: 'xxx', ruleid: 'yyy' }

// 格式2：包装在 data 字段中
{ code: 0, data: { welfareid: 'xxx', ruleid: 'yyy' } }

// 格式3：接口失败
{ code: 404, message: 'Not Found' }
// 或直接抛出异常
```

### 默认参数

```javascript
const DEFAULT_WELFARE_ID = 'default_welfare'
const DEFAULT_RULE_ID = 'default_rule'
```

---

## 📖 使用方法

### 推荐用法（智能降级）

```bash
node scripts/generate_qr_with_fallback.js <output_path> item029 item131 ...

# 示例
node scripts/generate_qr_with_fallback.js qr.png Item029 Item131 Item173 Item032
```

### 输出示例

**正常情况（接口成功）**：
```
📋 体检项目: Item029, Item131, Item173, Item032
📁 输出路径: C:\path\to\qr.png
🔄 尝试同步项目获取个性化参数...
✅ 项目同步成功: { code: 0, data: { welfareid: 'f6a3f9ef14', ruleid: 'e8c8941424' } }
✅ 接口返回个性化参数
   welfareid: f6a3f9ef14
   ruleid: e8c8941424
✅ 使用接口返回的个性化参数

✅ 二维码生成完成
📍 路径: C:\path\to\qr.png
🔗 内容: https://www.ihaola.com.cn/launch/haola/pe?urlsrc=brief&welfareid=f6a3f9ef14&ruleid=e8c8941424
📊 来源: 个性化接口 ✅
```

**降级情况（接口失败）**：
```
📋 体检项目: Item029, Item131, Item173
📁 输出路径: C:\path\to\qr.png
🔄 尝试同步项目获取个性化参数...
⚠️ 接口调用失败: HTTP error! status: 404
⚠️ 使用默认参数（降级模式）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  降级模式 - 使用默认预约二维码
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
说明：因接口暂时不可用，使用通用预约二维码
      用户可在预约页面手动选择体检项目
推荐项目仅供参考: Item029, Item131, Item173
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 二维码生成完成
📍 路径: C:\path\to\qr.png
🔗 内容: https://www.ihaola.com.cn/launch/haola/pe?urlsrc=brief&welfareid=default_welfare&ruleid=default_rule
📊 来源: 降级默认 ⚠️

💡 提示：接口暂不可用，已使用默认二维码
   用户可在预约页面手动选择体检项目
```

---

## 🎯 降级场景

| 场景 | 接口状态 | 生成结果 | 用户体验 |
|------|---------|---------|---------|
| 接口正常 | ✅ 200 OK | 个性化二维码 | 直接预约，体检项目已预填 |
| 接口404 | ❌ 404 | 默认二维码 | 扫码后手动选择项目 |
| 网络超时 | ❌ Timeout | 默认二维码 | 扫码后手动选择项目 |
| 服务器错误 | ❌ 500 | 默认二维码 | 扫码后手动选择项目 |
| 格式异常 | ⚠️ 200 但无数据 | 默认二维码 | 扫码后手动选择项目 |

---

## 🔍 技术细节

### 错误处理

```javascript
try {
  const response = await syncService.syncItems(itemIds)

  // 解析多种返回格式
  const welfareid = response?.data?.welfareid || response?.welfareid
  const ruleid = response?.data?.ruleid || response?.ruleid

  if (welfareid && ruleid) {
    return { welfareid, ruleid, source: 'api' }
  }

  // 格式异常
  console.log('⚠️ 接口返回格式异常')
  return null
} catch (error) {
  // 网络错误/超时/服务器错误
  console.log(`⚠️ 接口调用失败: ${error.message}`)
  return null
}
```

### 透明性设计

1. **详细日志**：每个步骤都有清晰的日志输出
2. **明确提示**：降级时显示醒目的提示信息
3. **参数对比**：输出时会显示使用的 welfareid 和 ruleid
4. **用户体验**：降级时提示用户需要手动选择项目

---

## 📦 新增文件

### `generate_qr_with_fallback.js`

**功能**：
- 智能判断接口状态
- 自动选择参数来源
- 统一生成二维码

**导出**：
```javascript
module.exports = {
  smartGenerateQR,      // 主函数
  generateFallbackQR,   // 降级生成
  trySyncItems,         // 尝试同步
  DEFAULT_WELFARE_ID,   // 默认welfareid
  DEFAULT_RULE_ID      // 默认ruleid
}
```

### `test_fallback.js`

**功能**：
- 演示降级机制
- 测试脚本正确性
- 展示输出格式

---

## 🚀 部署建议

### SKILL.md 更新

在 SKILL.md 中明确推荐使用智能降级脚本：

```markdown
### 预约码生成与发送流程（⚠️ 强烈推荐使用智能降级脚本）

> **⚠️ 推荐使用智能降级脚本**：当接口失败时自动降级为默认二维码，确保100%成功

```bash
# ✅ 推荐方式：自动降级
node scripts/generate_qr_with_fallback.js <output_path> item029 item131 ...
```
```

---

## ✅ 优势总结

| 优势 | 说明 |
|------|------|
| **高可用** | 接口失败也能生成二维码 |
| **透明性** | 清晰告知用户和开发者当前状态 |
| **容错性** | 自动处理各种错误场景 |
| **易用性** | 一行命令即可使用 |
| **兼容性** | 支持多种接口返回格式 |
| **可追溯** | 完整日志记录，便于排查 |

---

## 🧪 测试验证

### 正常运行测试

```bash
node scripts/generate_qr_with_fallback.js qr.png Item029 Item131 Item173
```

### 演示模式（无需参数）

```bash
node scripts/generate_qr_with_fallback.js
```

### 完整测试套件

```bash
node scripts/test_fallback.js
```

---

## 📝 注意事项

1. **默认参数预配置**：需要在 ihaola.com.cn 配置 `default_welfare` 和 `default_rule`
2. **日志监控**：建议监控降级频率，如果频繁降级需要检查接口健康状态
3. **用户体验**：降级时生成的二维码功能完整，用户可手动选择项目
4. **性能影响**：降级模式不影响二维码生成速度

---

## 🎉 总结

通过引入智能降级机制，我们成功解决了接口不可用时的二维码生成问题，实现了：

- ✅ **100% 可用性**：无论接口状态如何，都能生成二维码
- ✅ **优雅降级**：降级过程对用户透明
- ✅ **最小影响**：用户仍可完成预约，只是需要手动选择项目
- ✅ **易于排查**：完整的日志和提示信息

这个改进大大提高了系统的健壮性和用户体验！
