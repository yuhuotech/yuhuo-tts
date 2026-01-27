# TTS-Alignment-API 云端部署指南

## 云服务商选项

### 选项 1: 阿里云 (推荐)

#### 第1步: 准备云服务器

```bash
# 购买 GPU 实例（建议配置）
- GPU: NVIDIA T4 或 A10
- CPU: 8核+
- 内存: 32GB+
- 存储: 100GB+ (SSD)
- 带宽: 10Mbps+
- 系统: Ubuntu 20.04

# 获取公网 IP
export PUBLIC_IP=1.2.3.4  # 替换为你的公网IP
```

#### 第2步: 环境配置

```bash
# SSH 连接
ssh root@$PUBLIC_IP

# 更新系统
apt-get update && apt-get upgrade -y

# 安装依赖
apt-get install -y python3.10 pip curl wget git
apt-get install -y nvidia-cuda-toolkit

# 克隆项目
git clone <your-repo-url> /opt/tts-api
cd /opt/tts-api
```

#### 第3步: 安装和启动

```bash
conda create -n tts-api python=3.10 -y
conda activate tts-api

pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 下载模型
modelscope download --model FunAudioLLM/CosyVoice2-0.5B \
  --local_dir pretrained_models/CosyVoice2-0.5B

# 启动服务（使用 systemd）
sudo tee /etc/systemd/system/tts-api.service << 'SYSTEMD'
[Unit]
Description=TTS-Alignment-API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tts-api
Environment="PATH=/opt/conda/envs/tts-api/bin"
ExecStart=/opt/conda/envs/tts-api/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable tts-api
sudo systemctl start tts-api
```

## 配置域名和 HTTPS

### 第1步: 申请域名

从域名服务商购买域名（如阿里云域名）

### 第2步: 配置 DNS

```bash
# 将域名 A 记录指向公网 IP
tts-api.yourdomain.com  A  1.2.3.4
```

### 第3步: 配置 SSL 证书

```bash
# 使用 Let's Encrypt（免费）
apt-get install -y certbot python3-certbot-nginx

certbot certonly --standalone -d tts-api.yourdomain.com
```

### 第4步: 配置 Nginx

安装 Nginx：
```bash
apt-get install nginx -y
```

创建 Nginx 配置文件 `/etc/nginx/sites-available/tts-api`：

```nginx
upstream tts_api {
    server 127.0.0.1:8000;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name tts-api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name tts-api.yourdomain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/tts-api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tts-api.yourdomain.com/privkey.pem;

    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 性能配置
    client_max_body_size 100M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://tts_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /audio/ {
        alias /opt/tts-api/output_audio/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/tts-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 最终 API 访问

### 开发环境
- API: http://localhost:8000
- 文档: http://localhost:8000/docs

### 生产环境
- API: https://tts-api.yourdomain.com
- 文档: https://tts-api.yourdomain.com/docs

### 示例 API 调用（公网）

```bash
curl -X POST https://tts-api.yourdomain.com/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "model": "cosyvoice2",
    "output_format": "base64"
  }'
```

## 成本估算

| 项目 | 规格 | 月成本 |
|-----|------|--------|
| GPU 实例 | NVIDIA T4 | ¥500 |
| 存储 | 100GB SSD | ¥50 |
| 带宽 | 10Mbps | ¥100 |
| 域名 | .com | ¥8 |
| SSL 证书 | 免费 (Let's Encrypt) | ¥0 |
| **总计** | | **~¥650/月** |

---

**部署完成后，您将获得一个完整的公网可访问 URL。**
