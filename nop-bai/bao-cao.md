# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Duy Phong |
| MSSV | 2A202602834 |
| Lớp / Khóa | K4 |
| Repo GitHub | https://github.com/DuyPhong123-ai/K4-L3-DAY21-NguyenDuyPhong-2A202602834-CI-CD-for-AI-Systems |
| Ngày nộp | Chưa nộp |

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---|---|---|---|---|
| 1 | 100 | 0.1 | 3 | 0.7109 | 0.8780 |
| 2 | 50 | 0.05 | 2 | 0.6051 | 0.8460 |
| 3 | 200 | 0.1 | 5 | 0.7149 | 0.8740 |

**Bộ siêu tham số đã chọn:** `n_estimators=200`, `learning_rate=0.1`, `max_depth=5`.

**Lý do:** Bộ thứ ba đạt F1 cao nhất, vượt ngưỡng 0.65 và tăng 0.0040 so với bộ thứ nhất. Bộ thứ nhất có accuracy cao nhất nhưng F1 thấp hơn, nên accuracy không quyết định lựa chọn. Bộ thứ hai dùng 50 cây, learning_rate 0.05 và độ sâu 2, đạt F1 0.6051 nên không đủ điều kiện triển khai. Khi giảm learning_rate, thường cần tăng số cây để bù mức đóng góp của từng cây. Các thí nghiệm thay đổi đồng thời số cây, learning_rate và độ sâu, nên chưa tách được ảnh hưởng từng tham số.

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Tập dữ liệu Adult có 24,8% mẫu thu nhập trên 50K và 75,2% mẫu thu nhập thấp, nên mô hình có thể thiên về lớp đa số. Nếu luôn dự đoán thu nhập thấp, mô hình vẫn đạt accuracy 75,2% nhưng bỏ sót toàn bộ người thu nhập cao. Accuracy do đó có thể gây hiểu nhầm về khả năng nhận diện nhóm này. F1 của lớp dương kết hợp precision và recall, đánh giá độ đúng khi dự đoán thu nhập cao và mức độ tìm đủ các trường hợp. Không dùng `average="weighted"` vì kết quả chịu ảnh hưởng từ lớp đa số. Không dùng `average="macro"` vì đó là trung bình F1 của hai lớp. Ngưỡng 0.65 áp dụng riêng cho F1 của lớp thu nhập cao.

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| MLflow không kết nối SQLite. | SQLAlchemy 2.1.3 không tương thích. | Ghim SQLAlchemy 2.0.30. |
| SSH từ máy cá nhân thất bại. | Quyền file key quá rộng và user chưa đúng. | Giới hạn quyền key, dùng `ec2-user`. |
| Release bị timeout tại SCP. | Cổng SSH chưa cho phép runner truy cập. | Cập nhật rule cổng 22, chạy lại Release. |

## 4. So Sánh Bước 2 và Bước 3

| Giai đoạn | f1_score | accuracy |
|---|---|---|
| [Bước 2](https://github.com/DuyPhong123-ai/K4-L3-DAY21-NguyenDuyPhong-2A202602834-CI-CD-for-AI-Systems/actions/runs/37654256393) (22.361 mẫu) | 0.7149 | 0.8740 |
| [Bước 3](https://github.com/DuyPhong123-ai/K4-L3-DAY21-NguyenDuyPhong-2A202602834-CI-CD-for-AI-Systems/actions/runs/37655708959) (44.722 mẫu) | 0.7354 | 0.8820 |

**Nhận xét:** Khi số mẫu train tăng từ 22.361 lên 44.722, F1 tăng 0.0205 và accuracy tăng 0.0080. Các chỉ số lấy từ artifact CI, với cùng bộ tham số và 500 mẫu holdout. Kết quả cải thiện ở lần thử này, không chứng minh thêm dữ liệu luôn làm F1 tăng.
