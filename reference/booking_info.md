# 体检预约信息

## 预约链接

```
https://www.ihaola.com.cn/partners/haola-2ca4db68-192a-f911-501a-f155af6f5772/pe/launching.html?fromLaunch=1&needUserInfo=1&code=021Zi8ll2TT6rh4JtTll2PuJNd0Zi8lL&state=
```

## 二维码生成

### Node.js（推荐，容器内可用）

```javascript
const { generateQR } = require('./scripts/generate_qr.js');
await generateQR('/path/to/output.png');
```

命令行：
```bash
node scripts/generate_qr.js [output_path]
```

### Python（需要 pip install qrcode）

```python
import qrcode
url = 'https://www.ihaola.com.cn/partners/haola-2ca4db68-192a-f911-501a-f155af6f5772/pe/launching.html?fromLaunch=1&needUserInfo=1&code=021Zi8ll2TT6rh4JtTll2PuJNd0Zi8lL&state='
img = qrcode.make(url)
img.save('体检预约二维码.png')
```

---

## 使用说明

1. 推荐完体检项目后，告知用户可以扫码预约
2. 使用 Node.js 生成二维码图片（推荐）
3. 将图片发送给用户（微信支持直接发送图片）
4. 告知用户：预约时说明"好啦专属顾问推荐"，可享VIP服务

---

**最后更新：** 2026-03-29
