# Phase 1 Baseline Report

_Sinh lúc: 2026-09-26T05:41:19.244616+00:00_

## 1. Nguồn Dữ Liệu

- Source API: Crossref REST API
- Tổng số bản ghi thu thập: 24
- Số dòng sau khi làm sạch: 24

## 2. Baseline RAG Evaluation

| Metric | Giá trị |
| --- | --- |
| Samples | 10 |
| Retrieval Hit Rate | 100.00% |
| Mean Token F1 | 0.5235 |
| Judge Accuracy | 50.00% |
| Mean Judge Score | 3.00 / 5 |

Ragas: bỏ qua (đặt `RUN_RAGAS=1` để bật).

## 3. Data Quality Gate (Great Expectations 1.x)

- Trạng thái chốt kiểm soát: **PASS**
- GX Expectations Success: True
- Số dòng kiểm tra: 24

| Expectation | Success |
| --- | --- |
| `expect_table_row_count_to_be_between` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_values_to_be_unique` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_value_lengths_to_be_between` | PASS |

## 4. Freshness SLA

- Ngưỡng freshness: 180 ngày
- Bài báo quá hạn: 1/24 (4.2%)
- Kết quả Freshness (is_fresh): True
