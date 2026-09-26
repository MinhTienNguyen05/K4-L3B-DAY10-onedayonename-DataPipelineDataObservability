# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Mạnh Hùng             |
| MSSV               | 2A202602708                |
| Khóa/Lớp         | K4 — L3B                   |
| Tên nhóm         | onedayonename              |
| Vai trò chính    | Data Observability — Quality Gate & Freshness Monitoring |
| Repository         | https://github.com/MinhTienNguyen05/K4-L3B-DAY10-onedayonename-DataPipelineDataObservability |
| Branch             | `hung_obser`               |
| Commit chính      | `94fb267` — `feat(task2): observability` |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Data Quality Gate | `src/observability/quality.py`: `run_data_quality_checks` | `pd.DataFrame` đã cleaned, `Settings`, `report_name` | `data/quality/baseline_quality_report.json`, `data/quality/corrupted_quality_report.json`, `data/quality/repaired_quality_report.json` | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py`: `build_freshness_report` | `pd.DataFrame` có cột `age_days` và `published`, `Settings`, `report_path` | `data/quality/freshness_report.json` | Hoàn thành |
| Phase 1 Markdown Report | `src/observability/reporting.py`: `generate_phase1_report` | `source_summary`, `metrics`, `quality`, `freshness` dicts | `data/reports/phase1_report.md` | Hoàn thành |
| Corruption Comparison Report | `src/observability/reporting.py`: `generate_corruption_report` | Metrics, quality, freshness dicts của 3 trạng thái | `data/reports/corruption_report.md` | Hoàn thành |


### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Cung cấp interface `run_data_quality_checks` và `build_freshness_report` | Pipeline orchestration (Minh Tiến) | Hai hàm được gọi trực tiếp trong `phase1.py` bước 8 và `corruption_flow.py` bước 5 & 7 |
| Thiết kế định dạng report markdown | Toàn bộ nhóm khi review kết quả | `phase1_report.md` và `corruption_report.md` cung cấp bảng đối chiếu 3 trạng thái có metric số liệu rõ ràng |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thiết kế và implement 6 Expectations với GX 1.x Ephemeral Context | `quality.py`: `run_data_quality_checks` | `baseline_quality_report.json`: `success=true`, 6/6 PASS, 24 records | Mở file `data/quality/baseline_quality_report.json` |
| Tính stale ratio và đánh giá SLA freshness 180 ngày / 25% | `quality.py`: `build_freshness_report` | `freshness_report.json`: 1 stale/24 rows, ratio 0.0417, `is_fresh=true` | Mở file `data/quality/freshness_report.json` |
| Phát hiện corruption qua quality gate | `quality.py`: `run_data_quality_checks` | `corrupted_quality_report.json`: `success=false`, 4/6 PASS, 2 expectations fail | Mở file `data/quality/corrupted_quality_report.json` |
| Sinh markdown report Pha 1 | `reporting.py`: `generate_phase1_report` | `data/reports/phase1_report.md` với bảng metrics, GX status, freshness | Mở file `data/reports/phase1_report.md` |

Output cụ thể của phần việc là `data/quality/corrupted_quality_report.json`: file này xác nhận `success=false` khi 2 trong 6 expectations thất bại — `ExpectColumnValuesToBeUnique` phát hiện 8/24 record duplicate (33.33%) và `ExpectColumnValueLengthsToBeBetween` phát hiện 9/24 summary bị rỗng (37.5%). Đây là tín hiệu kích hoạt cảnh báo silent failure trong pipeline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Module observability cần cung cấp hai tầng giám sát độc lập cho dữ liệu trước khi đưa vào ChromaDB index: (1) **quality gate** kiểm tra tính hợp lệ cấu trúc và nội dung của DataFrame và (2) **freshness monitoring** theo dõi tuổi dữ liệu so với SLA. Nếu chỉ kiểm tra exit code của pipeline thì không phát hiện được silent failure khi RAG vẫn chạy nhưng dữ liệu đã bị corrupted hoặc quá cũ.

### Cách triển khai

**`run_data_quality_checks` — Great Expectations 1.x Ephemeral Context:**

Tôi sử dụng Ephemeral Context (không cần file system) để tránh phụ thuộc vào cấu hình persistent. Với mỗi lần gọi, hàm khởi tạo một context mới, đăng ký Pandas data source, tạo `DataFrameAsset` và `BatchDefinition`, rồi chạy `batch.validate(suite)` với 6 expectations:

1. `ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)` — row count hợp lệ.
2. `ExpectColumnValuesToNotBeNull(column="paper_id")` — không có paper_id null.
3. `ExpectColumnValuesToNotBeNull(column="title")` — không có title null.
4. `ExpectColumnValuesToNotBeNull(column="text_for_embedding")` — không có field embedding null.
5. `ExpectColumnValuesToBeUnique(column="paper_id")` — không trùng DOI.
6. `ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30)` — summary đủ nội dung.

Kết quả được trích xuất thành dict tường minh với `success`, `kwargs`, `result` cho từng expectation và lưu vào JSON artifact theo đường dẫn từ `Settings`.

**`build_freshness_report` — SLA-based Freshness:**

Hàm tính `stale_ratio = stale_rows / total_rows` với ngưỡng `age_days > freshness_threshold_days` (180 ngày). `is_fresh = stale_ratio <= 0.25`. Payload bao gồm đầy đủ: `latest_published`, `oldest_published`, `total_rows`, `stale_rows`, `stale_ratio`, `max_age_days`, `mean_age_days`.

**`generate_phase1_report` và `generate_corruption_report`:**

Hai hàm nhận các dict kết quả từ evaluation, quality và freshness, sau đó dùng f-string template để render markdown có bảng metric, trạng thái GX, freshness SLA và phân tích xu hướng. `generate_corruption_report` tính thêm `hit_drop`, `hit_recovery`, `f1_drop`, `f1_recovery` để hiển thị biên độ suy giảm và phục hồi.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| Input (quality) | `pd.DataFrame` cleaned 16 cột; `Settings` (chứa `freshness_threshold_days`, `paths`); `report_name: str` ("baseline", "corrupted", hoặc tên khác) |
| Input (freshness) | `pd.DataFrame` có cột `age_days: int` và `published: datetime`; `Settings`; `report_path: Path` |
| Output (quality) | JSON dict + file tại `data/quality/{report_name}_quality_report.json` |
| Output (freshness) | JSON dict + file tại path được truyền vào |
| Output (reporting) | Markdown files tại `data/reports/phase1_report.md`, `data/reports/corruption_report.md` |
| Module phụ thuộc | `core.config.Settings`, `core.utils.write_json`, `core.utils.write_text`, `great_expectations`, `pandas` |
| Module sử dụng output | `src/pipelines/phase1.py` (bước 8), `src/pipelines/corruption_flow.py` (bước 5 và 7) |
| Điều kiện lỗi cần xử lý | DataFrame rỗng; thiếu cột `age_days`/`published`; GX context đã tồn tại suite trùng tên (xử lý bằng try/except get); report_name không phải "baseline"/"corrupted" thì dùng quality_dir dynamic |

### Cách xác minh

```bash
# Kích hoạt venv và chạy pipeline
.venv\Scripts\Activate.ps1
uv sync

# Chạy baseline pipeline đầy đủ
uv run python script/run_phase1.py

# Chạy corruption flow
uv run python script/run_corruption_flow.py

# Xem artifact quality
Get-Content data/quality/baseline_quality_report.json
Get-Content data/quality/corrupted_quality_report.json
Get-Content data/quality/freshness_report.json
```

- **Kết quả mong đợi (baseline quality):** `"success": true`, `"successful_expectations": 6`, `"total_records": 24`.
- **Kết quả mong đợi (corrupted quality):** `"success": false`, `"successful_expectations": 4`, `"unsuccessful_expectations": 2`.
- **Kết quả thực tế:** Khớp hoàn toàn — đọc trực tiếp từ artifact đã commit.
- **Artifact/log:** `data/quality/baseline_quality_report.json`, `data/quality/corrupted_quality_report.json`, `data/quality/repaired_quality_report.json`, `data/quality/freshness_report.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Great Expectations 1.x thay đổi API so với phiên bản cũ, không dùng `DataContext` filesystem-based mặc định. Cần chọn cách khởi tạo context phù hợp với môi trường CI/lab.
- **Các phương án đã cân nhắc:**
  - (1) Dùng `gx.get_context()` với FileSystem DataContext — yêu cầu thư mục `great_expectations/` được cấu hình sẵn, dễ conflict khi nhiều test chạy cùng lúc.
  - (2) Dùng `gx.get_context(mode="ephemeral")` — in-memory, không ghi disk, mỗi lần gọi là một context sạch.
- **Phương án đã chọn:** Phương án (2) — Ephemeral Context.
- **Lý do:** Ephemeral Context không phụ thuộc cấu trúc thư mục GX, không sinh file `.yml` thừa, không có side effect giữa các lần chạy baseline/corrupted/repaired. Trade-off là không lưu được kết quả validate history trong GX store, nhưng với bài lab này, artifact JSON đã là đủ để đối chiếu.
- **Bằng chứng quyết định phù hợp:** Cả ba lần gọi `run_data_quality_checks("baseline")`, `run_data_quality_checks("corrupted")`, `run_data_quality_checks("repaired")` đều sinh artifact JSON đúng schema, pipeline không conflict và chạy thành công trong cùng một session.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `Exception: Data Source 'papers_source_baseline' already exists in this Data Context.` khi hàm `run_data_quality_checks` được gọi nhiều lần trong cùng một context.
- **Lệnh hoặc bước tái hiện:** Gọi `run_data_quality_checks(df, settings, "baseline")` hai lần liên tiếp trong cùng Python process hoặc unit test.
- **Nguyên nhân gốc:** GX 1.x lưu data source, asset và batch definition trong context theo tên. Nếu context object được tái sử dụng, lần gọi thứ hai cố `add_pandas(name=source_name)` với tên đã tồn tại sẽ raise exception.
- **Cách xử lý:** Bọc toàn bộ các lệnh `add_*` trong `try/except`, nếu exception thì gọi `get()` tương ứng để lấy object đã tồn tại. Pattern try-add/except-get áp dụng nhất quán cho `data_source`, `data_asset` và `batch_definition`.
- **Cách xác minh sau khi sửa:** Chạy pipeline đầy đủ bao gồm corruption flow (gọi `run_data_quality_checks` với "baseline", "corrupted" và "repaired" theo thứ tự) — không có exception, ba artifact JSON được tạo đúng.
- **Điều học được:** Với GX 1.x Ephemeral Context, object name là unique key trong context; pattern try-add/except-get là workaround chính thống hơn là reset context mỗi lần, vì reset có thể làm mất suite đã đăng ký.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref `/works` API trả về raw JSON payload. `fetch_source_records` (Gia Huy) lưu response thô vào `data/raw/crossref_response.json` và parse thành `list[PaperRecord]` lưu tại `data/raw/crossref_records.json`. `build_clean_dataframe` (Gia Huy) chuẩn hóa 16 cột và tạo cột `text_for_embedding` theo cấu trúc "Title: … Authors: … Published: … Categories: … Summary: …". `LocalEmbeddingIndex.build()` (Minh Tiến) encode cột đó bằng `sentence-transformers/all-MiniLM-L6-v2` và upsert vector cùng `paper_id` và metadata vào ChromaDB collection.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   `test_set.json` gồm 10 câu hỏi, mỗi câu có `ground_truth_doc_ids` là danh sách `paper_id` kỳ vọng và `ground_truth_answer` là câu trả lời tham chiếu. Retrieval hit được tính là `True` khi ít nhất một ID trong top-k kết quả ChromaDB khớp với `ground_truth_doc_ids`. `mean_token_f1` đo độ trùng token giữa câu trả lời LLM sinh ra và ground truth answer. LLM judge so sánh cả hai và cho điểm 1–5.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks (`run_data_quality_checks`) kiểm tra tính hợp lệ cấu trúc tại thời điểm chạy: số row trong khoảng hợp lệ, các field bắt buộc không null, `paper_id` unique và summary đủ dài. Freshness monitoring (`build_freshness_report`) tập trung vào chiều thời gian: `age_days` vượt 180 ngày thì tính là stale; nếu stale ratio > 25% thì SLA FAIL. Một dataset có thể PASS toàn bộ quality checks nhưng vẫn STALE (dữ liệu đúng schema nhưng toàn bài báo từ năm ngoái).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để giữ biến kiểm soát: cùng câu hỏi, cùng ground truth, cùng top-k. Nếu thay test set giữa các trạng thái thì không thể quy chênh lệch metric cho corruption/repair — sự thay đổi có thể đến từ câu hỏi dễ/khó hơn hoặc ground truth khác. Cùng `test_set.json` đảm bảo delta metric phản ánh đúng tác động của dữ liệu.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi: (a) `repaired_quality_report.json` có `success=true` và `successful_expectations=6/6`; (b) freshness report (repaired) có `is_fresh=true`; (c) `repaired_metrics.json` cho `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`, `judge_accuracy=1.0`, `mean_judge_score=5.0` — bằng với baseline. Trong kết quả hiện tại, cả bốn điều kiện đều thỏa mãn.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate`   | 1.0000   | 0.6000    | 1.0000   | Mất 40% hit rate; quality gate phát hiện đúng nguyên nhân (9 summary rỗng + 8 duplicate) |
| `mean_token_f1`        | 1.0000   | 0.8526    | 1.0000   | Context thiếu chính xác làm token overlap giảm dù pipeline không crash |
| `judge_accuracy`       | 1.0000   | 0.9000    | 1.0000   | LLM judge vẫn đúng 9/10 vì một số câu không phụ thuộc summary |
| `mean_judge_score`     | 5.0000   | 4.6000    | 5.0000   | Điểm giảm nhẹ hơn hit rate; những câu còn lấy được context đúng vẫn đạt 5 |
| Quality checks (GX)    | PASS 6/6 | FAIL 4/6  | PASS 6/6 | Module của tôi phát hiện đúng 2 violations: uniqueness và summary length |
| Freshness status       | FRESH    | STALE     | FRESH    | Stale date corruption đẩy ratio vượt 25% SLA; repair từ raw snapshot khôi phục |

### Kết luận từ số liệu

1. **Corruption → Observability signal → Agent metric:** Tiêm `blank_summary` (7 records) + `inject_noise` + `duplicate_rows` (4 records) + `stale_date` → Quality gate phát hiện `ExpectColumnValueLengthsToBeBetween` fail (9/24 summary rỗng, 37.5%) và `ExpectColumnValuesToBeUnique` fail (8/24 duplicate, 33.33%) → RAG mất ngữ cảnh embedding → retrieval hit rate giảm từ 1.0 xuống 0.6; freshness chuyển STALE.

2. **Repair → Observability signal → Agent metric:** Load lại `crossref_records.json` raw, chạy `build_clean_dataframe` sạch, re-index ChromaDB → quality gate về PASS 6/6, freshness về FRESH → toàn bộ bốn agent metric phục hồi về baseline (1.0 / 1.0 / 1.0 / 5.0).

Corruption ảnh hưởng rõ nhất là `blank_summary` và `duplicate_rows` — hai scenario này kích hoạt trực tiếp hai trong sáu expectations của quality gate, đồng thời làm hỏng vector embedding (summary rỗng làm mất nội dung ngữ nghĩa; duplicate paper_id gây nhiễu top-k). `stale_date` không ảnh hưởng embedding nhưng làm stale ratio nhảy vượt SLA, tín hiệu riêng biệt của freshness monitoring.

Điểm khác kỳ vọng: `judge_accuracy` chỉ giảm từ 1.0 xuống 0.9 trong khi `retrieval_hit_rate` giảm xuống 0.6. Giả thuyết là các câu hỏi nhóm `authors`, `date`, `categories` ít phụ thuộc vào summary — context trả về vẫn đủ để LLM judge đánh giá đúng, dù embedding đã bị nhiễu.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Silent failure là trạng thái nguy hiểm nhất — RAG vẫn chạy với exit code 0, LLM vẫn sinh ra câu trả lời, nhưng quality đã suy giảm âm thầm. Quality gate bắt buộc phải chạy trước bước index, không phải sau.
2. **Về data quality/observability:** Quality checks và freshness monitoring bổ sung cho nhau chứ không thay thế được nhau. Quality checks đo structural correctness tại thời điểm chạy; freshness đo temporal relevance theo thời gian. Một dataset cần pass cả hai để an toàn đưa vào production RAG.
3. **Về ảnh hưởng của data đến RAG agent:** Vector embedding phản ánh trực tiếp chất lượng text. Blank summary hay noise text làm semantic vector lệch khỏi ý nghĩa gốc — retrieval không tìm được document đúng dù model embedding không thay đổi. Data quality là bottleneck đầu tiên của toàn bộ hệ thống RAG.

### Nếu có thêm thời gian

Tôi sẽ bổ sung **alerting tự động** khi quality gate fail: khi `run_data_quality_checks` trả về `success=False`, pipeline nên emit cảnh báo rõ ràng với danh sách expectation fail và số record vi phạm, và tùy chọn gửi notification (webhook/Slack). Cải thiện đo được bằng cách kiểm tra pipeline có dừng sớm và emit alert khi corrupted data đi vào — thay vì chỉ ghi vào file mà cần đọc thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Mạnh Hùng
**Ngày xác nhận:** 2026-09-26
