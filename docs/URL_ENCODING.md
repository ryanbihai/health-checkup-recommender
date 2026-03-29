# 体检套餐URL编码规则
## Booking URL Encoding Specification v1.0

---

## 一、整体结构

```
https://www.ihaola.com.cn/partners/haola-2ca4db68-192a-f911-501a-f155af6f5772/pe/launching.html
?fromLaunch=1
&needUserInfo=1
&code=<BASE64URL_ENCODED_PAYLOAD>
&state=
```

> `code` 参数 = 套餐信息经 Base64URL 编码后的字符串

---

## 二、Payload 结构

```
[ver(2)][userType(1)][age(2)][gender(1)][risks(0-3)][n(1)][items(3n)]
```

| 字段 | 长度 | 类型 | 说明 |
|------|------|------|------|
| `ver` | 2 | 固定 | 版本号，当前为 `01` |
| `userType` | 1 | 固定 | `P`=本人 `F`=家人 `U`=未知 |
| `age` | 2 | 固定 | 十进制年龄，如 `50`、`65` |
| `gender` | 1 | 固定 | `M`=男 `F`=女 `U`=未知 |
| `risks` | 0~3 | 可变 | 风险标记拼接：`D`=高血糖 `H`=高血压 `C`=心脑家族 `T`=肿瘤家族 `S`=吸烟 |
| `n` | 1 | 固定 | 加项数量（十六进制，`1`-`F`） |
| `items` | 3n | 可变 | 每个加项3字符，紧凑拼接 |

**最小 Payload**：2 + 1 + 2 + 1 + 0 + 1 + 0 = **7字符**
**示例（0项加项）**：`01P50M0`（本人50岁男，无加项）

---

## 三、加项代码表

| 代码 | 检查项 | 对应编码 |
|------|--------|---------|
| G01 | 胃镜 | HLZXX0205 |
| G02 | 肠镜 | HLZXX0259 |
| G03 | 低剂量螺旋CT | HLZXX0162 |
| G04 | 前列腺特异抗原 | HLZXX0121~0123 |
| G05 | 心脏彩超 | HLZXX0092 |
| G06 | 同型半胱氨酸 | HLZXX0089 |
| G07 | 肝纤维化检测 | HLZXX0228 |
| G08 | 糖化血红蛋白 | HLZXX0025 |
| G09 | 颈动脉彩超 | HLZXX0082 |
| G10 | 冠状动脉钙化积分 | HLZXX0220 |
| G11 | 乳腺彩超+钼靶 | HLZXX0109~0110 |
| G12 | TCT+HPV | HLZXX0113~0116 |

---

## 四、基础套餐（固定包含，URL 中不携带）

- 血尿便常规、肝肾功能、血脂四项
- 心电图、颈动脉彩超、动脉硬化
- 腹部彩超、甲状腺彩超、甲功五项
- 肿瘤标志物、骨密度、肺功能、眼科全套

---

## 五、编码示例

### 示例1：50岁男，胃部不适，加项：胃镜 + 低剂量螺旋CT + 前列腺特异抗原

```
ver       = 01
userType  = P        （本人）
age       = 50
gender    = M        （男）
risks     =          （无风险）
n         = 3        （3个加项）
items     = G01G03G04

拼串：01P50M3G01G03G04
Base64URL：MDFQNTBNM0cwMUcwM0cwNA
```

### 示例2：50岁男，高血糖，加项：糖化血红蛋白 + 同型半胱氨酸 + 颈动脉彩超

```
ver       = 01
userType  = P
age       = 50
gender    = M
risks     = D        （高血糖/糖尿病）
n         = 3
items     = G08G06G09

拼串：01P50MD3G08G06G09
Base64URL：MDFQNTBNRDNHMDhHMDZHMDk
```

### 示例3：60岁男，高血压+心脑血管家族史，加项：心脏彩超 + 冠状动脉钙化积分

```
ver       = 01
userType  = F        （家人）
age       = 60
gender    = M
risks     = HC       （高血压+心脑家族史）
n         = 2
items     = G05G10

拼串：01F60MHC2G05G10
Base64URL：MDFGNjBNSEMyRzA1RzEw
```

---

## 六、解码算法

```javascript
function decodeBookingCode(code) {
  const payload = Buffer.from(code, 'base64url').toString('utf8');

  const ver = payload.slice(0, 2);
  const userType = payload[2];
  const age = payload.slice(3, 5);
  const gender = payload[5];

  // risks: 紧跟gender之后，仅收集D/H/C/T/S，遇到其他字符停止
  let risksEnd = 6;
  while (risksEnd < payload.length && 'DGHTCRSL'.includes(payload[risksEnd])) {
    risksEnd++;
  }
  const risks = payload.slice(6, risksEnd);

  const n = parseInt(payload[risksEnd], 16);
  const itemsRaw = payload.slice(risksEnd + 1);

  const REVERSE_MAP = {
    G01:'胃镜', G02:'肠镜', G03:'低剂量螺旋CT', G04:'前列腺特异抗原',
    G05:'心脏彩超', G06:'同型半胱氨酸', G07:'肝纤维化检测',
    G08:'糖化血红蛋白', G09:'颈动脉彩超', G10:'冠状动脉钙化积分',
    G11:'乳腺彩超+钼靶', G12:'TCT+HPV'
  };

  const items = [];
  for (let i = 0; i < n * 3 && i + 3 <= itemsRaw.length; i += 3) {
    const c = itemsRaw.slice(i, i + 3);
    items.push({ code: c, name: REVERSE_MAP[c] || c });
  }

  return { ver, userType, age, gender, risks, items };
}

// 示例
const decoded = decodeBookingCode('MDFQNTBNM0cwMUcwM0cwNA');
// {
//   ver: '01',
//   userType: 'P',
//   age: '50',
//   gender: 'M',
//   risks: '',
//   items: [
//     { code: 'G01', name: '胃镜' },
//     { code: 'G03', name: '低剂量螺旋CT' },
//     { code: 'G04', name: '前列腺特异抗原' }
//   ]
// }
```

---

## 七、风险标记说明

| 标记 | 含义 |
|------|------|
| D | 高血糖/糖尿病 |
| H | 高血压 |
| C | 心脑血管家族史 |
| T | 肿瘤家族史 |
| S | 吸烟/粉尘暴露 |

多个风险可拼接，如 `DH` = 高血糖+高血压。

---

## 八、更新日志

| 日期 | 版本 | 更新 |
|-----|------|------|
| 2026-03-29 | 1.0.0 | 初版发布 |
