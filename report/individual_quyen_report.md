# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo tập trung vào phạm vi RAG và vector index được phân công cho thành viên. Các kết quả được đối chiếu với artifacts hiện có trong repository.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Minh Quyền             |
| MSSV               | 2A202602438                     |
| Khóa/Lớp         | K4-L3B              |
| Tên nhóm         | Nhóm Một     |
| Vai trò chính    | RAG & Vector Index |
| Repository         | K4-L3B-DAY10-NhomMot-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Embedding và vector index | `src/retrieval/embeddings.py`, `src/retrieval/index.py` | Clean DataFrame, `text_for_embedding` | ChromaDB collections và embedding manifests | Đã rà soát code và artifacts |
| RAG retrieval và answer flow | `src/retrieval/qa.py`, `src/retrieval/agent.py`, `src/retrieval/llm.py` | Câu hỏi, index, cấu hình LLM | Tài liệu truy xuất, context và câu trả lời | Đã rà soát code; ghi nhận mismatch cần xử lý |

Phạm vi này tách biệt với orchestration `core/` và `src/pipelines/` trong báo cáo cá nhân của trưởng nhóm. Cleaning/raw data do Nguyễn Nhật Thăng phụ trách; observability và evaluation do Vương Việt Hoàng phụ trách.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Đối chiếu contract giữa cleaned data, index và evaluation | Ingestion, evaluation | Xác nhận `paper_id` là document identity; cùng test set được dùng trong cả ba trạng thái |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Rà soát cách tạo embeddings và ChromaDB collections | `src/retrieval/embeddings.py`, `src/retrieval/index.py` | Ba collection baseline/corrupted/repaired; manifest embedding tương ứng | Code và `data/embeddings/papers_embeddings*.json` |
| Đối chiếu kết quả RAG trên cùng benchmark | `src/retrieval/qa.py`, `data/eval/test_set.json` | Hit Rate 100% → 60% → 100%; Token F1 0.5235 → 0.0963 → 0.5235 | `data/results/*_metrics.json` |

Output cụ thể đã đối chiếu là ba bộ metrics và các manifest cho collection `papers-baseline`, `papers-corrupted`, `papers-repaired`. Báo cáo này không thay đổi code, dữ liệu hay metrics nên kết quả hiện có được giữ nguyên.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần RAG/index chuyển dữ liệu đã chuẩn hóa thành embeddings có thể tìm kiếm, sau đó cung cấp context cho luồng hỏi đáp. Document identity và cách nạp index cần ổn định để kết quả baseline, corruption và repair có thể so sánh.

### Cách triển khai

`MiniLMEmbeddings` dùng `sentence-transformers/all-MiniLM-L6-v2` và chuẩn hóa vector. `LocalEmbeddingIndex.build` tạo ChromaDB collection với cosine distance, lưu nội dung `text_for_embedding` cùng metadata, và đặt ID theo dạng `paper_id::index`. Collection được chọn theo artifact đầu ra để tách baseline, corrupted và repaired. Khi truy vấn, `qa.py` tìm kiếm top-k và có thể ưu tiên exact title lookup trước khi trích câu trả lời từ metadata.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Clean DataFrame gồm `paper_id`, `title`, metadata và `text_for_embedding`; câu hỏi người dùng |
| Output                         | Embeddings, ChromaDB search results, retrieved contexts và câu trả lời |
| Module phụ thuộc             | `ingestion/cleaning.py`, `core/config.py`, Sentence Transformers, ChromaDB |
| Module sử dụng output        | `evaluation/metrics.py`, `retrieval/agent.py`, các pipeline |
| Điều kiện lỗi cần xử lý | Collection không tồn tại, index rỗng, metadata thiếu hoặc câu hỏi không khớp quy tắc answer extraction |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tạo baseline index và đánh giá lại cùng test set ở các trạng thái corrupted/repaired.
- **Kết quả trong artifacts hiện có:** Baseline Hit Rate 100%, corrupted 60%, repaired 100%; Token F1 lần lượt 0.5235, 0.0963 và 0.5235.
- **Artifact/log:** `data/embeddings/`, `data/results/*_metrics.json`, `data/eval/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Tách document identity khỏi nội dung để cập nhật index lặp lại mà không trộn các trạng thái thí nghiệm.
- **Các phương án đã cân nhắc:** Dùng DOI trực tiếp làm ID; dùng DOI kết hợp vị trí bản ghi.
- **Phương án đang dùng:** `paper_id::index` và các collection riêng cho baseline, corrupted, repaired.
- **Lý do:** Giữ ID ChromaDB duy nhất trong collection và cô lập dữ liệu giữa các lượt so sánh. `build` xóa collection cùng tên trước khi tạo lại, tránh giữ vector cũ.
- **Bằng chứng:** Các manifest trong `data/embeddings/` ghi collection/model; ba file metrics cho thấy repaired khớp baseline ở các chỉ số đã lưu.

## 6. Vấn đề phát hiện và hướng xử lý

- **Vấn đề:** Quy tắc nhận diện câu hỏi trong `src/retrieval/qa.py` chưa khớp một số prompt của test set. Code nhận diện `who authored`/`list the authors` và `what categories`, trong khi benchmark dùng “Who are the authors…” và “primary research field…”. Những câu này có thể rơi về nhánh trả summary thay vì authors/category.
- **Phạm vi ảnh hưởng:** Answer quality và các chỉ số judge/token F1; không làm thay đổi việc truy xuất document ID.
- **Trạng thái:** Đã xác định khi rà soát code; chưa sửa trong thay đổi tài liệu này. Không ghi nhận đây là lỗi đã được khắc phục.
- **Bước tiếp theo:** Đồng bộ phrase rules với `question_type`, thêm kiểm thử cho bốn loại câu hỏi, rồi chạy lại baseline/corruption/repaired và cập nhật metrics từ kết quả thực tế.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Raw Crossref records được cleaning thành DataFrame, gồm metadata và `text_for_embedding`; MiniLM mã hóa nội dung, rồi ChromaDB lưu vector, document ID và metadata để truy vấn.
2. Mỗi câu có `ground_truth` và `ground_truth_doc_ids`. Retrieval Hit Rate kiểm tra ID chuẩn có nằm trong kết quả top-k; Token F1 so độ trùng token giữa câu trả lời và ground truth.
3. GX kiểm tra cấu trúc/completeness/uniqueness/độ dài. Freshness SLA kiểm tra tỷ lệ `age_days > 180`, báo stale khi tỷ lệ vượt 25%.
4. Cố định test set giúp so sánh cùng câu hỏi và document IDs, giảm biến số ngoài chất lượng corpus.
5. Đối chiếu metrics repaired với baseline, GX/freshness report và số dòng clean sau khi dựng lại từ raw snapshot.

Lưu ý về luồng hiện tại: trong `run_phase1_pipeline`, index và evaluation chạy trước quality checks; quality result chưa được dùng để fail-closed/chặn index.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 100.00% | 60.00% | 100.00% | Corruption làm mất 4 tài liệu mới nhất; cả 4 đều có trong benchmark, nên hit rate giảm rõ rệt. |
| `mean_token_f1`      | 0.5235 | 0.0963 | 0.5235 | Câu trả lời suy giảm khi dữ liệu bị xóa/nhiễu; repaired trở lại giá trị baseline. |
| `judge_accuracy`     | 50.00% | 10.00% | 50.00% | Cùng xu hướng với chất lượng câu trả lời; evaluator có heuristic fallback khi LLM judge không khả dụng. |
| `mean_judge_score`   | 3.00 | 1.20 | 3.00 | Điểm trung bình phục hồi về baseline. |
| Quality checks       | Pass | Fail | Pass | Corrupted fail uniqueness và summary length; repaired pass. |
| Freshness status     | Fresh (4.17%) | Stale (50.00%) | Fresh (4.17%) | Corrupted artifact là 11/22 stale, vượt ngưỡng 25%. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Drop 4 records mới nhất, blank summary và duplicate rows → GX fail uniqueness/summary length; stale date làm 11/22 dòng quá hạn → Hit Rate/F1 giảm trên artifacts corrupted.
2. Rebuild clean data từ raw snapshot → GX pass, freshness trở về 1/24 stale → Hit Rate và Token F1 trong repaired metrics trở lại mức baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Drop latest records có tác động trực tiếp, dễ kiểm chứng nhất: 4 tài liệu bị bỏ đúng là document ID của bốn câu hỏi đầu trong test set. Hit Rate giảm 40 điểm phần trăm, tương ứng 4/10 câu không còn tài liệu ground truth trong index.

Kết quả nào khác với kỳ vọng ban đầu?

Freshness corrupted là 50%, không phải 36.36%. `corrupted_quality_report.json` ghi 11 stale rows trên 22; báo cáo nhóm đã được đồng bộ, còn báo cáo cá nhân có sẵn của một thành viên khác cần được chủ sở hữu đối chiếu lại.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Document identity, metadata và embedding text là contract quan trọng giữa cleaning và vector index.
2. Giữ riêng collection cho từng trạng thái giúp phép so sánh và repair dễ kiểm tra hơn.
3. Retrieval có thể vẫn chạy khi dữ liệu sai; cần kiểm tra answer extraction và quality signals chứ không chỉ dựa vào việc chương trình không crash.

### Nếu có thêm thời gian

Đồng bộ answer extraction với `question_type` thay vì dò một vài cụm từ tự do, thêm test cho summary/authors/date/categories, rồi tái sinh cả ba metrics. Theo dõi Hit Rate, Token F1 và judge metrics để bảo đảm không giảm so với baseline hiện tại.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Tôi đã rà soát và xác nhận nội dung, vai trò, MSSV trước khi nộp.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Các số liệu báo cáo được đối chiếu với artifacts hiện có.
- [x] Báo cáo phân biệt rõ vấn đề đã phát hiện với vấn đề đã khắc phục.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Nội dung tập trung vào RAG/vector index, không sao chép báo cáo cá nhân của trưởng nhóm.

**Họ và tên:** Nguyễn Minh Quyền

**Ngày xác nhận:** Chờ thành viên rà soát và xác nhận trước khi nộp.
