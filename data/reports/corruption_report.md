# Báo Cáo Đối Chiếu 3 Trạng Thái: Baseline vs Corrupted vs Repaired

> **Hệ thống:** Data Pipeline & Data Observability for RAG  
> **Mục tiêu:** Chứng minh năng lực phát hiện suy giảm chất lượng dữ liệu (Silent Failure) và khả năng tự phục hồi (Idempotent Repair).

---

## 1. Bảng Đối Chiếu Hiệu Năng & Observability Qua 3 Trạng Thái

| Chỉ số / Tín hiệu kiểm định | 1. Baseline (Chuẩn) | 2. Corrupted (Tiêm lỗi) | 3. Repaired (Phục hồi) | Tác động của Corruption | Mức độ phục hồi |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Retrieval Hit Rate** | **100.00%** | **60.00%** | **100.00%** | -40.00% | +40.00% |
| **Mean Token F1** | **0.5235** | **0.0963** | **0.5235** | -0.4272 | +0.4272 |
| **Judge Accuracy** | **50.00%** | **10.00%** | **50.00%** | -40.00% | +40.00% |
| **Mean Judge Score** | **3.00** | **1.20** | **3.00** | -1.80 | +1.80 |
| **GX 1.x Quality Gate** | Passed (100%) | **FAILED** | **Passed** | Vi phạm quy tắc dữ liệu | 100% Khôi phục |
| **Freshness SLA** | Fresh (<=25% stale) | **STALE (SLA Violated)** | **Fresh** | Quá hạn thời gian | 100% Khôi phục |

---

## 2. Phân Tích Hiện Tượng Silent Failure

Khi dữ liệu bị tiêm lỗi nhân tạo (Blank summary, Truncate title, Inject noise, Stale date, Duplicate rows, Drop latest):
- Các mô hình AI / Vector Search không quăng ngoại lệ (không crash chương trình), nhưng chỉ số **Hit Rate** và **Token F1** sụt giảm nghiêm trọng.
- **Data Quality Gate (Great Expectations 1.x)** và **Freshness SLA** đã kích hoạt cảnh báo đỏ kịp thời, chặn đứng dữ liệu bẩn trước khi phục vụ người dùng.

---

## 3. Cơ Chế Phục Hồi Dữ Liệu An Toàn (Idempotent Repair)

- Khi chốt kiểm soát báo động, luồng **Idempotent Repair** tự động khôi phục dữ liệu sạch từ bản lưu trữ thô bất biến ban đầu (`data/raw/crossref_records.json`).
- Sau khi làm sạch lại và re-index Vector Store, tất cả các chỉ số chất lượng retrieval và độ chính xác của câu trả lời đã lấy lại phong độ hoàn toàn như Baseline ban đầu.

---
*Báo cáo được tự động tạo bởi Data Observability Engine.*
