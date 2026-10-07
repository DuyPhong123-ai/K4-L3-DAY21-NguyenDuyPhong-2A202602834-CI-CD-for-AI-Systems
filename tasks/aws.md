# Bước 2 trên AWS

Mã dùng S3 cho DVC và model, EC2 cho FastAPI. MLflow cục bộ giữ nguyên.

## 1. Máy cá nhân: S3 và DVC

Trong PowerShell đã kích hoạt `.venv311`:

```powershell
python -m pip install -r requirements.txt
aws sts get-caller-identity
$env:AWS_DEFAULT_REGION = "us-east-1"
$bucket = "TEN_BUCKET_CUA_BAN"
```

Thay region bằng region của bucket. Chọn bucket riêng cho lab, giữ Block Public Access bật. Bucket và EC2 cùng region để tránh phí truyền dữ liệu liên vùng. S3 tính phí lưu trữ và request; EC2, EBS và IP công khai có thể phát sinh phí. Xem [giá S3](https://aws.amazon.com/s3/pricing/) và [giá EC2](https://aws.amazon.com/ec2/pricing/).

Nếu chưa có bucket, tạo qua AWS Console. Sau đó:

```powershell
python -m dvc init
python -m dvc remote add -d labstore "s3://$bucket/dvc"
python -m dvc add data/train_batch1.csv data/holdout.csv data/train_batch2.csv
python -m dvc push
python -m pytest tests/ -v
```

DVC đọc credentials từ AWS CLI hoặc biến môi trường AWS. Không lưu access key vào `.dvc/config`. Khi đã có `.dvc`, không chạy lại `dvc init`.

## 2. GitHub Actions

Trong Settings → Secrets and variables → Actions, tạo các secrets:

| Secret | Giá trị |
|---|---|
| AWS_ACCESS_KEY_ID | Access key ID của danh tính CI. |
| AWS_SECRET_ACCESS_KEY | Secret access key tương ứng. |
| AWS_SESSION_TOKEN | Chỉ cần nếu dùng credentials tạm thời. |
| ARTIFACT_BUCKET | Tên bucket, không có `s3://`. |
| SERVER_HOST | IP công khai của EC2. |
| SERVER_USER | User SSH, ví dụ `ubuntu` trên Ubuntu. |
| SERVER_SSH_KEY | Private key được EC2 cho phép đăng nhập. |

Tạo repository variable `AWS_REGION` bằng region đã chọn. Workflow mặc định dùng `us-east-1` nếu chưa đặt.

Chỉ dán credentials vào GitHub Secrets. Danh tính CI cần đọc/ghi object dưới `dvc/` và `artifacts/`, cùng quyền liệt kê bucket trên các prefix này. Dùng danh tính dành cho lab với quyền giới hạn theo bucket; không dùng access key của tài khoản admin. Credentials tạm thời hết hạn cần được cập nhật trước lần chạy tiếp theo. Có thể chuyển sang GitHub OIDC sau khi cấu hình IAM role tương ứng.

## 3. EC2: chuẩn bị API

Dùng Ubuntu, gắn instance profile có quyền `s3:GetObject` cho `artifacts/current/model.joblib` trong bucket lab. Boto3 tự lấy credentials từ instance role; không cần chép access key lên EC2. Bật IMDSv2 và mã hóa EBS khi tạo máy.

Trên EC2, đặt `requirements-serving.txt` ở thư mục home rồi chạy:

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv ~/income-venv
~/income-venv/bin/python -m pip install -r ~/requirements-serving.txt
mkdir -p ~/src ~/models
```

Tạo `/etc/systemd/system/income-api.service`, thay `ubuntu`, `TEN_BUCKET` và `REGION` theo tài nguyên thật:

```ini
[Unit]
Description=Income API
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment=ARTIFACT_BUCKET=TEN_BUCKET
Environment=AWS_DEFAULT_REGION=REGION
ExecStart=/home/ubuntu/income-venv/bin/python /home/ubuntu/src/serve.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Chạy `sudo systemctl daemon-reload` và `sudo systemctl enable income-api`. User triển khai cần được phép chạy `sudo -n systemctl restart income-api`. Workflow chép `serve.py` vào `~/src/`, upload model đã đạt F1 >= 0.65, rồi restart service. Không khởi động service trước khi có model trên S3.

Security group cần cho phép kết nối SSH của runner và cổng 8080 từ nơi gọi API. Kiểm tra log bằng `journalctl -u income-api`; có thể bật CloudTrail S3 data events và CloudWatch metrics để theo dõi truy cập, lưu ý chi phí.

## 4. Kiểm tra sau triển khai

```powershell
$vmAddress = "IP_EC2"
Invoke-RestMethod "http://${vmAddress}:8080/healthz"
$payload = @{features = @(28, 2, 14, 2, 11, 0, 1, 0, 0, 45)} | ConvertTo-Json
Invoke-RestMethod "http://${vmAddress}:8080/score" -Method Post -ContentType "application/json" -Body $payload
```

Commit code và các file `.dvc`, rồi `dvc push` trước `git push`. Chỉ thực hiện Bước 3 sau khi đủ bốn jobs của Bước 2 thành công.
