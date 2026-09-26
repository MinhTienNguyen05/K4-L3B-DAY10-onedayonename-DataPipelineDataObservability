# Báo Cáo Cá Nhân — Nguyễn Thị Minh Tiến

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|-----------|----------|
| Họ và tên | Nguyễn Thị Minh Tiến |
| MSSV | 2A202602997 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | onedayonename |
| Vai trò chính | Pipeline Orchestration & Integration |
| Branch | `minhtien-pipeline` |
| Ngày hoàn thành | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|-------------------|---------------------|----------------|-----------------|------------|
| Baseline Pipeline | `src/pipelines/phase1.py` | raw records, settings | baseline metrics, reports | ✅ Hoàn thành |
| Corruption Flow | `src/pipelines/corruption_flow.py` | baseline metrics, clean df | comparison report, repaired metrics | ✅ Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|------------|------------------------------|---------|
| Review & fix bugs | Team (Anh Minh) | Hỗ trợ review code, test E2E |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|------------------------|--------------------------|-------------------|---------------|
| Viết phase1 pipeline | `src/pipelines/phase1.py` | Baseline pipeline E2E | `python script/run_phase1.py` |
| Viết corruption flow | `src/pipelines/corruption_flow.py` | Corruption→Repaired flow | `python script/run_corruption_flow.py` |
| Merge vào main | `minhtien-pipeline` → `main` | Code tích hợp | `git log` |
| Hoàn thiện TEAM.md | `docs/TEAM.md` | Tài liệu nhóm hoàn chỉnh | Review file |

### Output cụ thể

- **Baseline pipeline**: Hoàn thành luồng end-to-end từ raw records → clean data → ChromaDB index → evaluation → quality checks → reports
- **Corruption flow**: Mô phỏng corruption → phát hiện qua quality gate → repair từ raw records → so sánh 3 trạng thái
- **Artifacts**: `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần xây dựng 2 pipeline orchestration để kết nối tất cả module đã hoàn thành thành một hệ thống hoàn chỉnh:
1. **phase1.py**: Tự động hóa toàn bộ quy trình baseline từ fetch → clean → index → evaluate → report
2. **corruption_flow.py**: Mô phỏng lỗi → đánh giá → phục hồi → so sánh

### Cách triển khai

**phase1.py (9 bước):**
1. Load settings từ `core/config.py`
2. Load hoặc fetch raw records từ Crossref API
3. Clean data bằng `build_clean_dataframe()`
4. Save clean CSV/JSON vào `data/clean/`
5. Build ChromaDB index bằng `LocalEmbeddingIndex.build()`
6. Generate hoặc load evaluation test set
7. Evaluate bằng `evaluate_pipeline()` với Hit Rate, Token F1, Judge Score
8. Run quality checks (Great Expectations 1.x) và freshness report
9. Generate markdown report

**corruption_flow.py (8 bước):**
1. Load baseline metrics và clean dataframe
2. Corrupt data bằng `corrupt_clean_dataframe()` với 6 scenarios
3. Save corrupted artifacts
4. Build corrupted index và evaluate
5. Run quality checks trên corrupted data (phải FAILED)
6. Repair bằng cách load raw records và clean lại
7. Evaluate repaired data
8. Generate comparison report

### Input, output và contract

| Thành phần | Mô tả |
|------------|-------|
| Input | Settings, raw records từ `data/raw/`, clean df từ `data/clean/` |
| Output | Metrics JSON, answers JSON, markdown reports |
| Module phụ thuộc | `ingestion/`, `observability/`, `evaluation/`, `retrieval/` |
| Module sử dụng output | Team sử dụng để verify và present |
| Điều kiện lỗi cần xử lý | API timeout (có fallback), missing files (có error message) |

### Cách xác minh

```bash
# Test phase1
source .venv/bin/activate
python script/run_phase1.py

# Kết quả mong đợi:
# - Hit Rate: 100%
# - Quality Gate: PASSED
# - Freshness: FRESH
# - Exit code: 0

# Test corruption flow
python script/run_corruption_flow.py

# Kết quả mong đợi:
# - Corrupted Quality Gate: FAILED
# - Repaired Quality Gate: PASSED
# - Hit Rate recovered: 100%
# - Exit code: 0
```

**Kết quả thực tế:** Khớp với kết quả mong đợi

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Design pattern cho pipeline orchestration - nên dùng sequential steps hay DAG-based?
- **Các phương án đã cân nhắc:** 
  1. Sequential function calls (đơn giản, dễ debug)
  2. DAG-based với dependency resolution (phức tạp, linh hoạt)
- **Phương án đã chọn:** Sequential function calls với clear step numbering
- **Lý do:** Vì các module đã có input/output contracts rõ ràng qua `core/config.py`, sequential approach đủ để đảm bảo reproducibility mà không cần thêm complexity. Code dễ đọc, debug và explain cho team.
- **Bằng chứng quyết định phù hợp:** Cả 2 pipeline chạy thành công với exit code 0, metrics đúng như kỳ vọng.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'datasets'` khi import
- **Lệnh hoặc bước tái hiện:** `python -c "from pipelines.phase1 import main"`
- **Nguyên nhân gốc:** Chưa activate virtual environment `.venv`
- **Cách xử lý:** Sử dụng `source .venv/bin/activate` trước khi chạy Python scripts
- **Cách xác minh sau khi sửa:** Pipeline chạy thành công với đầy đủ output
- **Điều học được:** Luôn kiểm tra environment setup trước khi debug code

---

## 7. Hiểu biết về luồng end-to-end

### Câu trả lời:

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref API → raw JSON → `parse_crossref_payload()` → list[PaperRecord] → `build_clean_dataframe()` → pd.DataFrame → `LocalEmbeddingIndex.build()` → ChromaDB collection với embeddings

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Test set chứa câu hỏi + ground truth answer + document IDs. Retrieval hit = document được retrieve có trong ground truth. Judge LLM so sánh predicted answer với ground truth để đánh giá quality.

3. **Quality checks khác freshness monitoring ở điểm nào?**
   Quality checks (Great Expectations) = structural integrity (null, uniqueness, length). Freshness = temporal relevance (age_days > threshold). Cả 2 đều là observability signals nhưng đo lường khác nhau.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo so sánh công bằng - cùng câu hỏi, cùng ground truth. Nếu test set khác nhau, metrics không thể so sánh trực tiếp.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repaired metrics phải ≈ baseline metrics (hit rate phục hồi về 100%, quality gate quay lại PASSED, freshness quay lại FRESH). Corruption log xác nhận corruption đã xảy ra đúng scenarios.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|--------------|--------:|----------:|--------:|----------|
| `retrieval_hit_rate` | 100% | 60% | 100% | Corruption giảm hit rate 40%, repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.8526 | 1.0000 | Token overlap giảm khi bị corrupt, phục hồi 100% |
| `judge_accuracy` | 100% | 90% | 100% | LLM judge vẫn đánh giá được dù quality giảm |
| `mean_judge_score` | 5.00 | 4.60 | 5.00 | Score giảm nhẹ khi corrupted, phục hồi hoàn toàn |
| Quality checks | PASSED | **FAILED** | PASSED | GX phát hiện ngay data corruption |
| Freshness status | FRESH | STALE | FRESH | Stale ratio tăng đột ngột khi corrupt |

### Kết luận từ số liệu

**Chuỗi 1 (Corruption):**
Data corruption (blank summary, inject noise, truncate title, duplicate rows) → Quality Gate FAILED (phát hiện 2/6 expectations failed) + Freshness STALE → Retrieval hit rate giảm 40% (vector embedding bị méo mó bởi noise text) → Judge score giảm

**Chuỗi 2 (Repair):**
Repair từ raw records → Clean lại bằng `build_clean_dataframe()` → Quality Gate quay lại PASSED → Freshness FRESH → Hit rate phục hồi 100% → Judge score phục hồi 5.00

**Corruption nào ảnh hưởng rõ nhất:** 
`inject_noise` (chèn "!!!CORRUPTED NOISE RAG FAILURE!!!") ảnh hưởng nhiều nhất vì nó làm vector embedding bị nhiễu nặng, khiến semantic search không tìm được document đúng.

**Kết quả khác kỳ vọng:** Không có. Tất cả metrics đều khớp với kỳ vọng - corruption flow hoạt động đúng như thiết kế.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Idempotent Pipeline Design**: Việc lưu trữ raw data snapshot cho phép repair hoàn toàn. Không có raw data → không thể phục hồi sau corruption. Data lineage quan trọng hơn code.

2. **Data Quality Gate là Early Warning System**: Great Expectations phát hiện corruption TRƯỚC KHI ảnh hưởng đến downstream metrics. Đây là shift từ reactive sang proactive monitoring.

3. **Silent Failure là nguy hiểm nhất**: Pipeline vẫn chạy thành công với exit code 0 khi data bị corrupt, nhưng results sai. Cần quality gates, không chỉ exit codes.

### Nếu có thêm thời gian

Triển khai automated alerting khi quality checks fail - gửi notification qua email/Slack thay vì chỉ ghi log. Điều này đảm bảo team biết ngay khi data corruption xảy ra, không phải đợi manual review.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thị Minh Tiến
**Ngày xác nhận:** 2026-09-26
