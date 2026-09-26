# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4-L3B |
| Tên nhóm         | Nhóm Một |
| Repository         | K4-L3B-DAY10-NhomMot-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Quang Hữu | 2A202602756 | Trưởng nhóm / Pipeline Integrator | `core/`, `phase1.py`, `corruption_flow.py` |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành xuất sắc toàn bộ 6 checkpoint trọng tâm của bài thực chiến Data Pipeline & Data Observability. Trong giai đoạn Baseline, hệ thống đã thu thập 24 công trình nghiên cứu từ Crossref API, chuẩn hóa và trích xuất ngữ cảnh 5 phần, nạp vector embedding `all-MiniLM-L6-v2` vào ChromaDB (`papers-baseline`), vượt qua chốt kiểm định Great Expectations 1.x và Freshness SLA với chỉ số: Retrieval Hit Rate 100.00% và Token F1 0.5235. 

Trong giai đoạn kiểm thử độ bền (Phase 2), bộ công cụ Synthetic Corruption Suite đã tiêm 6 kịch bản lỗi thực tế (bỏ rơi 20% bài mới, làm rỗng tóm tắt, chèn ký tự rác, cắt ngắn tiêu đề, lùi ngày xuất bản và nhân đôi bản ghi). Thí nghiệm đã làm phát lộ hiện tượng **Silent Failure**: chương trình không crash nhưng Hit Rate sụt giảm còn 60.00% và Token F1 giảm còn 0.0963. Ngay lập tức, Data Quality Gate (GX 1.x) và Freshness SLA đã kích hoạt báo động vi phạm chất lượng dữ liệu. Nhóm đã kích hoạt thành công cơ chế **Idempotent Repair** từ nguồn lưu trữ thô ban đầu, khôi phục toàn vẹn dữ liệu và đưa các chỉ số RAG trở lại mức ban đầu (Hit Rate 100.00%, F1 0.5235).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API / Snapshot | Fetch API, retry backoff, parse payload | `data/raw/crossref_records.json` | Nguyễn Quang Hữu |
| Cleaning          | Raw records | Bỏ thẻ XML, tính `age_days`, tạo `text_for_embedding` | `data/clean/papers_clean.csv` | Nguyễn Quang Hữu |
| Embedding/index   | Clean DataFrame | Sinh vector `all-MiniLM-L6-v2`, nạp ChromaDB | `data/chroma/`, `papers_embeddings.json` | Nguyễn Quang Hữu |
| Evaluation        | Clean/Corrupted/Repaired Index | Đánh giá Hit Rate, Token F1, LLM Judge | `data/results/*_metrics.json` | Nguyễn Quang Hữu |
| Observability     | Clean/Corrupted DataFrame | GX 1.x Ephemeral Context, Freshness SLA | `data/quality/*_quality_report.json` | Nguyễn Quang Hữu |
| Corruption/repair | Clean DataFrame & Raw Snapshot | Tiêm 6 dạng lỗi; Idempotent Repair từ snapshot | `corruption_log.json`, `*_repaired.*` | Nguyễn Quang Hữu |
| Orchestration     | Toàn bộ modules | Kết nối điều phối end-to-end Phase 1 & 2 | `phase1_report.md`, `corruption_report.md` | Nguyễn Quang Hữu |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini` (hỗ trợ fallback mock/heuristic khi không có API key) |
| `LLM_MODEL`                | `gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 bản ghi |
| Retrieval `top_k`           | 4 |
| Freshness threshold          | 180 ngày (tối đa 25% bài báo cũ) |
| Random seed, nếu có        | Mặc định định danh không đổi |

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-09-26 12:35:00 | `data/reports/phase1_report.md` (Hit Rate: 100.00%, F1: 0.5235) |
| Corruption flow   | Thành công | 2026-09-26 12:38:25 | `data/reports/corruption_report.md` (3 trạng thái) |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter                | `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:...,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-09-26 |
| Số record nhận được    | 24 bản ghi |
| Cơ chế retry/backoff      | 3 lần thử lại với exponential backoff khi gặp mã lỗi 429/500/502/503/504; tự động fallback đọc snapshot mẫu khi mất mạng |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | Định danh bài báo (DOI) | Bỏ qua record nếu thiếu DOI |
| `title` | `str` | Có | Tiêu đề bài báo | Bỏ qua record nếu thiếu tiêu đề; chuẩn hóa whitespace |
| `summary` | `str` | Có | Tóm tắt bài báo | Loại bỏ thẻ `<jats:p>`, chuẩn hóa khoảng trắng thừa |
| `authors` | `list[str]` | Có | Danh sách tác giả | Gộp `given` + `family`, chuẩn hóa thành chuỗi tên |
| `published` | `str` | Có | Ngày xuất bản chuẩn `YYYY-MM-DD` | Parse date-parts; gán `2026-01-01` nếu thiếu |
| `age_days` | `int` | Có | Số ngày tuổi tính từ ngày chạy | Tính `(run_date - published).days` |
| `text_for_embedding` | `str` | Có | Khối văn bản nạp vào mô hình embedding | Ghép nối cấu trúc 5 phần chuẩn hóa |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Khử thẻ JATS XML (`<jats:p>...</jats:p>`) | Validity / Consistency | 24 | Regex làm sạch trong `crossref.py` |
| Chuẩn hóa khoảng trắng (`\s+`) | Conformance | 24 | Hàm `normalize_whitespace` |
| Khử trùng lặp theo `paper_id` | Uniqueness | 0 ở baseline, 2 ở corruption | `drop_duplicates(subset=['paper_id'])` |
| Tính toán `age_days` | Timeliness / Freshness | 24 | Cột `age_days` trong DataFrame |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding` được cấu trúc thành 5 khối rõ ràng phân tách bởi dấu xuống dòng:
  ```text
  Title: <Tiêu đề>
  Authors: <Tác giả>
  Published: <Ngày xuất bản>
  Categories: <Chuyên ngành>
  Summary: <Tóm tắt>
  ```
- `record_id` trong Vector Store: Ghép nối giữa mã `paper_id` và số thứ tự bản ghi (`f"{paper_id}::{index}"`).
- `age_days`: Trừ ngày thực thi pipeline (`run_date.date()`) cho ngày xuất bản của bài báo (`pub_date`).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 câu hỏi |
| Các `question_type`                    | `summary` (3), `authors` (3), `date` (2), `categories` (2) |
| Ground-truth document ID                 | Khóa `paper_id` tương ứng với bài báo sinh câu hỏi |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | `gemini` / `gemini-2.5-flash` (kèm heuristic fallback evaluator) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Việc cố định tập kiểm thử (Controlled Evaluation Benchmark) là nguyên tắc cốt lõi trong đo lường hệ thống dữ liệu. Bằng cách giữ nguyên các câu hỏi kiểm thử, mọi sự thay đổi trong các chỉ số đo lường (Hit Rate, Token F1, Judge Accuracy) được đảm bảo phản ánh chính xác 100% tác động của sự thay đổi chất lượng dữ liệu nền tảng, loại bỏ hoàn toàn nhiễu từ phía câu hỏi đánh giá.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Đầy đủ `crossref_response.json` & `crossref_records.json` |
| Cleaned dataset          | `data/clean/`                        | Có | Đầy đủ `papers_clean.csv` & `papers_clean.json` (24 dòng) |
| Embedding manifest/index | `data/embeddings/`                   | Có | Đầy đủ `papers_embeddings.json` |
| Evaluation set           | `data/eval/`                         | Có | Đầy đủ `test_set.json` (10 câu hỏi) |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Hit Rate: 100.00%, F1: 0.5235 |
| Quality/freshness        | `data/quality/`                      | Có | Đầy đủ GX report và `freshness_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Báo cáo Markdown chi tiết Pha 1 |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |        100.00% | 10/10 câu hỏi truy xuất chính xác tài liệu chứa ground truth trong Top-4 |
| `mean_token_f1`      |         0.5235 | Trích xuất câu trả lời chuẩn xác theo ground truth |
| `judge_accuracy`     |         50.00% | Tỉ lệ câu trả lời khớp chính xác tiêu chí nghiệp vụ |
| `mean_judge_score`   |         3.00 / 5 | Điểm trung bình chất lượng câu trả lời đạt mức 3.00/5 |
| Ragas, nếu có        |            N/A | Tùy chọn tăng cường (mặc định tắt để tối ưu thời gian thực thi) |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `ExpectTableRowCountToBeBetween` | Completeness | Từ 5 đến 5000 dòng | Pass (24 dòng) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`paper_id`) | Completeness | 0 giá trị null | Pass (0 null) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`title`) | Completeness | 0 giá trị null | Pass (0 null) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`text_for_embedding`) | Completeness | 0 giá trị null | Pass (0 null) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` (`paper_id`) | Uniqueness | Không có trùng lặp | Pass (24 unique) | `data/quality/baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` (`summary`) | Validity | Tối thiểu 30 ký tự | Pass (độ dài >= 30) | `data/quality/baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cột `age_days` trong `data/clean/papers_clean.csv` |
| Timestamp mới nhất       | `2026-07-22` (age = 66 ngày) |
| Ngưỡng freshness         | Không quá 25% số bài báo có `age_days > 180` ngày |
| Trạng thái baseline      | Fresh (Hợp lệ) |
| Lý do                     | Chỉ có 1/24 bài báo (4.17%) có `age_days > 180`, thấp hơn nhiều so với ngưỡng cảnh báo 25% |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest records | Bỏ rơi 20% bài báo mới nhất theo ngày xuất bản | 4 | Row count giảm | Hit Rate sụt giảm 40% | Nạp lại đầy đủ từ raw snapshot |
| Blank summary | Xóa rỗng trường tóm tắt (`summary = ""`) | 2 | Vi phạm độ dài summary < 30 | Token F1 sụt giảm nghiêm trọng | Khôi phục lại abstract sạch từ raw |
| Inject noise | Chèn chuỗi ký tự rác vào tóm tắt | 2 | Nhiễu loạn ngữ nghĩa | Token F1 giảm | Khôi phục lại text gốc |
| Truncate title | Cắt ngắn tiêu đề xuống còn 5 ký tự | 2 | Khó tra cứu theo title | Giảm khả năng exact lookup | Tái tạo lại tiêu đề đầy đủ |
| Stale date | Lùi ngày xuất bản về 365 ngày trước | 8 | Tỉ lệ bài báo cũ vượt ngưỡng SLA | `is_fresh = False` (36.36% stale) | Cập nhật lại ngày xuất bản gốc |
| Duplicate rows | Nhân bản 2 dòng dữ liệu vào DataFrame | 2 | Vi phạm khóa chính duy nhất | GX 1.x Uniqueness báo lỗi đỏ | Khử trùng lặp theo `paper_id` |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ thời gian tiêm lỗi, số dòng ban đầu (24), số dòng sau biến đổi (22), các mã DOI bị ảnh hưởng chi tiết của từng kịch bản.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Hàm `repair_from_raw_snapshot` kích hoạt nguyên lý Idempotent Pipeline: thay vì vá lỗi thủ công trên DataFrame đã bị bẩn, quy trình đọc trực tiếp bản ghi từ raw data snapshot bất biến (`data/raw/crossref_records.json`). Dữ liệu thô sau đó được đưa qua toàn bộ quy tắc làm sạch chuẩn hóa ban đầu, xây dựng lại DataFrame sạch từ đầu và re-index toàn bộ ChromaDB, đảm bảo 100% tính nguyên vẹn của dữ liệu và khả năng truy vết nguồn gốc (Data Lineage).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |  100.00% |    60.00% |  100.00% |                  -40.00% |         +40.00% | Bị sụt giảm mạnh khi drop tài liệu và phục hồi hoàn toàn |
| `mean_token_f1`        |   0.5235 |    0.0963 |   0.5235 |                  -0.4272 |         +0.4272 | Do blank summary và noise; phục hồi trọn vẹn |
| `judge_accuracy`       |   50.00% |    10.00% |   50.00% |                  -40.00% |         +40.00% | Phục hồi hoàn hảo sau khi re-index dữ liệu sạch |
| `mean_judge_score`     |     3.00 |      1.20 |     3.00 |                    -1.80 |           +1.80 | Điểm số trung bình quay lại mức ban đầu 3.00/5 |
| Quality checks pass/fail |   Passed |    FAILED |   Passed | Vi phạm tính duy nhất & độ dài | 100% Khôi phục | GX 1.x báo động chính xác |
| Freshness status         |    Fresh |     STALE |    Fresh | Tăng tỉ lệ quá hạn lên 36.36% | 100% Khôi phục | SLA chuyển về mức an toàn (4.17%) |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **Nhân quả 1 (Corruption ➔ Observability ➔ RAG Degradation):** Khi tiêm lỗi làm rỗng summary và bỏ rơi 20% bài báo mới nhất, GX 1.x phát hiện vi phạm độ dài (`expect_column_value_lengths_to_be_between` thất bại) và Freshness SLA kích hoạt cảnh báo STALE (36.36% > 25%). Đồng thời, Retrieval Hit Rate sụt giảm từ 100.00% xuống 60.00% và Token F1 giảm từ 0.5235 xuống 0.0963.
2. **Nhân quả 2 (Idempotent Repair ➔ Observability Recovery ➔ RAG Restoration):** Khi kích hoạt quy trình phục hồi từ snapshot thô, tất cả 6 Expectations của GX 1.x đạt trạng thái `Passed`, Freshness SLA trở về mức `Fresh` (4.17% quá hạn), kéo theo sự phục hồi hoàn toàn của Retrieval Hit Rate lên 100.00% và Token F1 lên 0.5235.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Khi chạy các lệnh kiểm thử trên Windows PowerShell, console bị văng lỗi `UnicodeEncodeError: 'cp932' codec can't encode character '\xf4'`.
- **Nguyên nhân:** Windows PowerShell mặc định sử dụng Code Page 932 của hệ thống, không hỗ trợ hiển thị các ký tự tiếng Việt có dấu trong thông báo console và log.
- **Cách xử lý:** Đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi script và bổ sung tham số `encoding="utf-8"` trong tất cả các thao tác đọc/ghi file tại `src/core/utils.py`.
- **Cách xác minh:** Chạy `python script/run_phase1.py` và `python script/run_corruption_flow.py`, toàn bộ output tiếng Việt hiển thị chính xác và chương trình chạy exit code 0.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Quy mô dữ liệu hiện tại dừng ở 24 bài báo | Chưa mô phỏng hết độ trễ khi scale lên hàng triệu vector | Mở rộng tải pagination từ Crossref API với batch size 1000 records |
| Kích hoạt Repair vẫn cần gọi lệnh script | Cần có sự can thiệp của kỹ sư khi Quality Gate báo động | Xây dựng Auto-Healing webhook tự động trigger repair khi GX validation thất bại |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
