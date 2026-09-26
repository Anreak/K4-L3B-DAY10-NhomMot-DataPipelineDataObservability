# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Quang Hữu |
| MSSV               | 2A202602756 |
| Khóa/Lớp         | K4-L3B |
| Tên nhóm         | Nhóm Một |
| Vai trò chính    | Trưởng nhóm / Pipeline Integrator |
| Repository         | K4-L3B-DAY10-NhomMot-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Cấu hình & Utility | `src/core/config.py`, `src/core/utils.py` | Biến môi trường `.env`, cấu hình hệ thống | Object `Settings`, `Paths`, helper functions | Hoàn thành |
| Baseline Pipeline Orchestration | `src/pipelines/phase1.py`, `script/run_phase1.py` | Raw data, Clean data, Test set | `papers_clean.csv`, `baseline_metrics.json`, `phase1_report.md` | Hoàn thành |
| Corruption & Repair Orchestration | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Baseline artifacts, raw snapshot | `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Debug mã hóa UTF-8 console Windows | Toàn bộ pipeline (`PYTHONIOENCODING`) | Fix lỗi hiển thị tiếng Việt trên PowerShell |
| Tích hợp Great Expectations 1.x | `src/observability/quality.py` | Tích hợp Ephemeral Context và 4 Expectations chạy ổn định |
| Rà soát Data Lineage | `src/ingestion/crossref.py`, `cleaning.py` | Bảo toàn raw snapshot và cơ chế Idempotent Repair |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thiết lập cấu hình hệ thống | `src/core/config.py` | Quản lý tập trung mọi đường dẫn và tham số RAG | `python -c "from core.config import load_settings; s=load_settings(); print(s.paths.clean_csv)"` |
| Xây dựng Baseline Pipeline Pha 1 | `src/pipelines/phase1.py` | End-to-end chu trình dữ liệu sạch, đạt 100% Hit Rate | `python script/run_phase1.py` |
| Xây dựng Corruption & Repair Pha 2 | `src/pipelines/corruption_flow.py` | Đo lường Silent Failure và tự phục hồi từ raw snapshot | `python script/run_corruption_flow.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

File báo cáo so sánh `data/reports/corruption_report.md` cùng các file metrics (`baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`) chứng minh định lượng sự suy giảm từ 100% xuống 70% Hit Rate và phục hồi trọn vẹn về 100%.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Điều phối toàn bộ vòng đời dữ liệu đa tầng trong hệ thống RAG Agent: đảm bảo tính tái lập (reproducibility), khả năng tự phục hồi bất biến (Idempotent Repair) khi phát hiện lỗi dữ liệu, và kết nối trơn tru giữa Ingestion, Cleaning, Vector Index, Evaluation, Observability Gate và Reporting.

### Cách triển khai

- Xây dựng lớp `run_phase1_pipeline`: kết nối Ingestion từ Crossref ➔ Làm sạch văn bản ➔ Nạp vector collection `papers-baseline` ➔ Sinh test set ➔ Đánh giá metrics ➔ Kiểm định GX 1.x & Freshness SLA ➔ Xuất báo cáo Phase 1.
- Xây dựng lớp `run_corruption_flow_pipeline`: tiêm 6 lỗi dữ liệu ➔ Nạp collection `papers-corrupted` ➔ Đo lường Silent Failure ➔ Kích hoạt `repair_from_raw_snapshot` đọc từ snapshot thô ban đầu ➔ Nạp collection `papers-repaired` ➔ Xuất báo cáo đối chiếu 3 trạng thái.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Snapshot thô `data/raw/crossref_records.json`, cấu hình `Settings` |
| Output                         | Datasets sạch/lỗi/phục hồi, vector collections, metrics JSON và Markdown reports |
| Module phụ thuộc             | `core/`, `ingestion/`, `retrieval/`, `evaluation/`, `observability/` |
| Module sử dụng output        | Agent phục vụ truy vấn và Giảng viên nghiệm thu báo cáo |
| Điều kiện lỗi cần xử lý | Mất mạng (dùng offline snapshot fallback), API dính 429/503, console encoding lỗi |

### Cách xác minh

```bash
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONPATH="src"; python script/run_phase1.py
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONPATH="src"; python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Exit code 0, in ra console bảng so sánh 3 trạng thái, các file report markdown được tạo.
- **Kết quả thực tế:** Cả 2 lệnh chạy thành công với exit code 0, Hit Rate phục hồi từ 70% về 100%, F1 phục hồi từ 0.6664 về 1.0000.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp phục hồi dữ liệu khi Data Quality Gate báo động (Repair mechanism).
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Viết code sửa lỗi trực tiếp trên DataFrame bị bẩn (in-place data patching).
  2. *Phương án B:* Kích hoạt Idempotent Repair tái tạo toàn bộ dữ liệu sạch từ Raw Data Snapshot bất biến ban đầu.
- **Phương án đã chọn:** Phương án B (Idempotent Repair từ Raw Snapshot).
- **Lý do:** Phương án A tiềm ẩn nguy cơ "sửa sai đè sai", không thể dự đoán hết các dạng lỗi bị tiêm và không đảm bảo tính toàn vẹn (Data Lineage). Phương án B tuân thủ nguyên lý Immutable Data Foundation: dữ liệu thô không bao giờ bị biến đổi, mọi biến đổi đều có thể tái lập và khôi phục 100% nguyên bản.
- **Bằng chứng quyết định phù hợp:** Kết quả `repaired_metrics.json` đạt tuyệt đối 100.00% Hit Rate và 1.0000 Token F1, trùng khớp hoàn toàn với Baseline ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `UnicodeEncodeError: 'cp932' codec can't encode character '\xf4' in position 1: illegal multibyte sequence`
- **Lệnh hoặc bước tái hiện:** Chạy lệnh kiểm thử console in chuỗi tiếng Việt `Môi trường sẵn sàng` trên Windows PowerShell.
- **Nguyên nhân gốc:** Console PowerShell trên Windows của máy chủ sử dụng Code Page mặc định (`cp932`) thay vì UTF-8, gây lỗi khi in ký tự tiếng Việt có dấu.
- **Cách xử lý:** Đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` và cấu hình `encoding="utf-8"` trong tất cả các hàm I/O file tại `core/utils.py`.
- **Cách xác minh sau khi sửa:** Chạy lại lệnh test và in ra chính xác `Môi trường sẵn sàng` và `Tín hiệu hoàn thành: Quality check status = True` mà không bị crash.
- **Điều học được:** Khi phát triển pipeline dữ liệu đa nền tảng, luôn chủ động chuẩn hóa UTF-8 ở cả tầng ứng dụng và môi trường shell.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu đi từ Crossref đến vector index:** Dữ liệu metadata JSON tải từ Crossref API qua Ingestion ➔ Chuẩn hóa bỏ thẻ XML, tính `age_days`, ghép `text_for_embedding` 5 phần ➔ Trích xuất vector embedding qua mô hình `all-MiniLM-L6-v2` ➔ Nạp vào vector store ChromaDB với cấu hình khoảng cách cosine.
2. **Evaluation set và ground-truth document IDs:** Bộ test gồm 10 câu hỏi với nhãn `ground_truth` và `ground_truth_doc_ids`. Khi câu hỏi được truy vấn, hệ thống đo xem tài liệu chứa ID chuẩn có nằm trong top_k kết quả trả về hay không (Hit Rate) và so sánh độ trùng lặp từ giữa câu trả lời với ground truth (Token F1).
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm soát tính toàn vẹn, duy nhất và hợp lệ về mặt cấu trúc dữ liệu (schema, not null, uniqueness, độ dài text). Freshness monitoring giám sát khía cạnh thời gian (temporal dimension), cảnh báo dữ liệu bị lỗi thời (stale data) khi bài báo quá hạn 180 ngày vượt tỉ lệ cho phép (>25%).
4. **Vì sao dùng chung test set:** Để đảm bảo tính khách quan và khoa học của thực nghiệm đối chứng (Controlled Experiment). Khi giữ nguyên tập câu hỏi chuẩn, mọi sự biến thiên của chỉ số chỉ phản ánh duy nhất chất lượng của tập dữ liệu đang được phục vụ.
5. **Tiêu chuẩn Repair thành công:** Dựa trên việc file `repaired_metrics.json` phục hồi các chỉ số (`retrieval_hit_rate` từ 70% lên 100%, `mean_token_f1` từ 0.6664 lên 1.0000) và `repaired_quality_report.json` đạt `gx_success = True`, `is_fresh = True`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   100.00% |    70.00% |  100.00% | Bị sụt giảm 30% khi tiêm lỗi và phục hồi hoàn toàn sau repair |
| `mean_token_f1`      |    1.0000 |    0.6664 |   1.0000 | Giảm mạnh do rỗng summary và nhiễu text; phục hồi tuyệt đối |
| `judge_accuracy`     |   100.00% |    70.00% |  100.00% | Tỉ lệ câu trả lời đúng phục hồi tương ứng với Hit Rate |
| `mean_judge_score`   |      5.00 |      3.40 |     5.00 | Điểm trung bình chất lượng câu trả lời lấy lại phong độ tối đa |
| Quality checks         |    Passed |    FAILED |   Passed | GX 1.x phát hiện chính xác vi phạm uniqueness và độ dài summary |
| Freshness status       |     Fresh |     STALE |    Fresh | Tỉ lệ stale tăng lên 36.36% gây cảnh báo đỏ SLA |

### Kết luận từ số liệu

1. **Chuỗi 1:** Tiêm lỗi (Drop 20% bài mới + Blank summary) ➔ GX 1.x phát hiện vi phạm độ dài summary và uniqueness ➔ Retrieval Hit Rate giảm từ 100% xuống 70%, Token F1 giảm từ 1.0000 xuống 0.6664.
2. **Chuỗi 2:** Kích hoạt Idempotent Repair từ snapshot thô ban đầu ➔ GX 1.x và Freshness SLA báo xanh `Passed` ➔ Retrieval Hit Rate phục hồi từ 70% lên 100%, Token F1 phục hồi lên 1.0000.

Corruption ảnh hưởng rõ nhất là **Drop latest records** và **Blank summary** vì làm triệt tiêu hoàn toàn thông tin ngữ cảnh khiến retriever không tìm thấy tài liệu liên quan.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Thiết kế Idempotent Pipeline với raw snapshot bất biến là "phao cứu sinh" quan trọng nhất của hệ thống kỹ thuật dữ liệu.
2. **Về Data Quality/Observability:** Cần thiết lập chốt kiểm soát tự động với Great Expectations 1.x trước serving layer để ngăn chặn dữ liệu hỏng thâm nhập vào vector store.
3. **Về RAG Agent:** Hiện tượng Silent Failure cực kỳ nguy hiểm trong thực tế vì hệ thống không crash nhưng đưa ra câu trả lời sai lệch nghiêm trọng nếu không có observability.

### Nếu có thêm thời gian

Xây dựng cơ chế Auto-Healing tự động kích hoạt Repair Pipeline ngay khi Quality Gate kích hoạt cảnh báo vi phạm mà không cần người vận hành can thiệp thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Quang Hữu  
**Ngày xác nhận:** 2026-09-26
