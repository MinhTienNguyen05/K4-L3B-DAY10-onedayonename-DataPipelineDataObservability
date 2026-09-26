# 📊 Báo Cáo Pha 1: Baseline Pipeline & Data Observability

> **Hệ thống:** Data Pipeline & Observability for RAG Agent  
> **Trạng thái:** Hoàn thành Pha 1 (Baseline Verification)

---

## 1. 📥 Tổng Quan Nguồn Dữ Liệu (Source Summary)

- **Nguồn dữ liệu:** Crossref REST API
- **Tổng số bản ghi thu thập:** 24 bài báo khoa học
- **Trạng thái lưu trữ:** Đầy đủ `crossref_response.json` và `crossref_records.json` (Bảo toàn Data Lineage).
- **Bộ dữ liệu sau làm sạch (Cleaned):** Đã khử trùng lặp, chuẩn hóa cấu trúc 5 phần cho embedding (`text_for_embedding`).

---

## 2. 🛡️ Data Observability & Quality Gate (Great Expectations 1.x)

- **Trạng thái Quality Gate:** **✅ PASSED**
- **Số Expectations đánh giá:** 6
- **Số Expectations đạt chuẩn:** 6 / 6

### Chi tiết kiểm thử chất lượng:

| Expectation | Trạng thái | Tham số kiểm tra |
| :--- | :---: | :--- |
| `expect_table_row_count_to_be_between` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `min_value=5`, `max_value=5000` |
| `expect_column_values_to_not_be_null` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `column=paper_id` |
| `expect_column_values_to_be_unique` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `column=paper_id` |
| `expect_column_values_to_not_be_null` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `column=title` |
| `expect_column_values_to_not_be_null` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `column=text_for_embedding` |
| `expect_column_value_lengths_to_be_between` | ✅ PASS | `batch_id=papers_source_baseline-papers_asset_baseline`, `column=summary`, `min_value=30` |

---

## 3. ⏱️ Data Freshness SLA

- **Đánh giá SLA Freshness:** **✅ FRESH**
- **Ngưỡng độ tươi mới (SLA Threshold):** 180 ngày
- **Số bài báo quá hạn (Stale records):** 1 / 24
- **Tỷ lệ quá hạn:** 4.2% (Quy định SLA: tối đa 25%)
- **Thời gian xuất bản gần nhất:** `2026-07-22`
- **Thời gian xuất bản cũ nhất:** `2026-03-28`

---

## 4. 📈 Chỉ Số Đánh Giá Baseline RAG (Retrieval & Generation Benchmarks)

Đánh giá được thực hiện trên bộ Benchmark Test Set gồm **10** câu hỏi thuộc 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`).

| Chỉ số đánh giá (Metric) | Kết quả Baseline | Mục tiêu đề ra | Đánh giá |
| :--- | :---: | :---: | :--- |
| **Retrieval Hit Rate** | **100.00%** | $\ge 70\%$ | Đạt chuẩn |
| **Mean Token F1** | **1.0000** | $\ge 0.50$ | Tốt |
| **LLM Judge Accuracy** | **100.00%** | $\ge 70\%$ | Đạt chuẩn |
| **Mean Judge Score (1 - 5)** | **5.00 / 5.0** | $\ge 3.5$ | Xuất sắc |

---

## 5. 🎯 Kết Luận & Kế Hoạch Tiếp Theo

1. Pipeline sạch đã được xác thực an toàn qua Great Expectations 1.x và Freshness SLA.
2. Vector Index ChromaDB sẵn sàng với embedding `all-MiniLM-L6-v2`.
3. Sẵn sàng bước vào **Pha 2: Tiêm lỗi tổng hợp (Synthetic Data Corruption)** để kiểm chứng năng lực cảnh báo của Data Quality Gate và đo lường sự suy giảm chất lượng AI.
