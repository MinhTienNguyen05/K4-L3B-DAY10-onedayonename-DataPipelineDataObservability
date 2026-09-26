# 🔬 Báo Cáo Đối Chiếu 3 Trạng Thái: Baseline vs Corrupted vs Repaired

> **Chủ đề:** Đo lường suy giảm chất lượng dữ liệu (Data Corruption & Silent Failure) và Khả năng tự phục hồi (Idempotent Repair)  
> **Hệ thống:** Data Pipeline & Data Observability for RAG

---

## 1. 📊 Bảng Đối Chiếu Hiệu Năng 3 Trạng Thái (Comparative Benchmark Table)

| Tiêu chí / Chỉ số (Metric) | Baseline (Chuẩn) | Corrupted (Tiêm Lỗi) | Repaired (Phục Hồi) | Xu Hướng & Tác Động |
| :--- | :---: | :---: | :---: | :--- |
| **Retrieval Hit Rate** | **100.00%** | **60.00%** | **100.00%** | Giảm **+40.0%** khi lỗi, phục hồi **+40.0%** |
| **Mean Token F1** | **1.0000** | **0.8526** | **1.0000** | Giảm **+0.1474** khi lỗi, phục hồi **+0.1474** |
| **LLM Judge Accuracy** | **100.00%** | **90.00%** | **100.00%** | Chênh lệch rõ rệt về độ chính xác nội dung |
| **Mean Judge Score (1 - 5)** | **5.00** | **4.60** | **5.00** | Điểm số sụt giảm khi dính text rác / rỗng |
| **Data Quality Gate (GX 1.x)** | **✅ PASS** | **❌ FAIL** | **✅ PASS** | Chặn đứng dữ liệu lỗi trước khi index |
| **Freshness SLA (180 days)** | **✅ FRESH** | **⚠️ STALE** | **✅ FRESH** | Báo động khi tỷ lệ stale vượt quá 25% |

---

## 2. ⚠️ Phân Tích Hiện Tượng Silent Failure Trên Dữ Liệu Bẩn

Khi tiêm 6 kịch bản dữ liệu lỗi (`Drop latest`, `Blank summary`, `Inject noise`, `Truncate title`, `Stale date`, `Duplicate rows`):
- **Không xảy ra crash hệ thống (Silent Failure):** Mã nguồn RAG vẫn thực thi bình thường, không văng exception, nhưng câu trả lời của AI và kết quả truy hồi vector bị suy giảm nặng nề.
- **Suy giảm Retrieval Hit Rate:** Việc xóa rỗng tóm tắt hoặc chèn chuỗi ký tự rác làm vector embedding bị méo mó, dẫn đến các văn bản liên quan không còn xuất hiện trong Top-K kết quả.
- **Suy giảm chất lượng câu trả lời:** LLM bị mất ngữ cảnh chính xác, sinh ra câu trả lời mơ hồ hoặc sai lệch (hallucination).

---

## 3. 🛡️ Vai Trò Của Data Quality Gate (Great Expectations 1.x)

Hệ thống Data Observability đã hoạt động chính xác:
- **Phát hiện ngay lập tức:** Báo cáo `corrupted_quality_report.json` kích hoạt cờ `success=False` do vi phạm các Expectation:
  - `ExpectColumnValueLengthsToBeBetween`: Phát hiện `summary` bị cắt ngắn hoặc xóa rỗng.
  - `ExpectColumnValuesToBeUnique`: Phát hiện bản ghi bị nhân bản (duplicate `paper_id`).
  - `ExpectColumnValuesToNotBeNull`: Phát hiện thiếu trường thông tin bắt buộc.
- **Cảnh báo độ tươi mới (Freshness SLA):** Tỷ lệ bài báo cũ vượt ngưỡng 25% làm `is_fresh=False`, giúp phát hiện sự cố stale dữ liệu kịp thời.

---

## 4. 🔄 Cơ Chế Tự Phục Hồi (Idempotent Repair)

Nhờ áp dụng nguyên lý **Idempotent Data Pipeline** và lưu trữ dữ liệu thô ban đầu (`crossref_records.json`):
1. **Re-ingestion & Cleansing:** Tự động lấy lại dữ liệu từ nguồn snapshot tin cậy, thực thi lại toàn bộ quy trình tiền xử lý và tạo lại trường `text_for_embedding`.
2. **Re-indexing ChromaDB:** Tái lập vector store sạch, loại bỏ hoàn toàn các vector lỗi thời hoặc bị ô nhiễm.
3. **Kết quả phục hồi:** Toàn bộ các chỉ số `Retrieval Hit Rate`, `Token F1`, và `Judge Score` đã lấy lại mức hiệu năng tương đương/tiệm cận với trạng thái Baseline ban đầu.
4. **Data Quality Gate:** Great Expectations 1.x và Freshness SLA đều quay trở về trạng thái **PASSED**.

---

## 5. 🎯 Kết Luận

Thí nghiệm chứng minh tầm quan trọng sống còn của **Data Observability** trong các hệ thống RAG Agent. Việc kết hợp kiểm thử tự động dữ liệu (GX 1.x) cùng đường ống xử lý có khả năng tự phục hồi (Idempotent Pipeline) giúp bảo vệ hệ thống AI khỏi hiện tượng suy thoái ngầm trong môi trường production.
