# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Vũ Gia Huy |
| MSSV | 02705 |
| Khóa/Lớp | K4 — L3B |
| Tên nhóm | onedayonename |
| Vai trò chính | Data Foundation — Crossref ingestion và data cleaning |
| Repository | https://github.com/MinhTienNguyen05/K4-L3B-DAY10-onedayonename-DataPipelineDataObservability |
| Branch | `giahuy-ingestion` |
| Commit chính | `0c22d60` — `feat: implement Crossref ingestion and data cleaning` |
| Ngày hoàn thành báo cáo | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Crossref ingestion | `src/ingestion/crossref.py`: `PaperRecord`, `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref `/works` payload hoặc snapshot JSON cục bộ | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Cleaning và data modeling | `src/ingestion/cleaning.py`: `build_clean_dataframe` | Danh sách `PaperRecord` và thời điểm chạy | `data/clean/papers_clean.json`, `data/clean/papers_clean.csv` | Hoàn thành |

Các output sạch là contract đầu vào cho embedding/index, evaluation, observability và hai pipeline orchestration. Tôi chỉ nhận ownership đối với hai module ingestion nêu trên; các module retrieval, observability, evaluation và pipeline do thành viên khác phụ trách.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Bàn giao schema và clean artifacts | Embedding, observability, evaluation và orchestration | Cung cấp 24 record sạch với 16 cột, có `paper_id`, `age_days`, `summary_chars` và `text_for_embedding` để các bước sau dùng thống nhất |
| Bảo đảm khả năng chạy khi Crossref không khả dụng | Pipeline orchestration | Có cơ chế retry HTTP và fallback sang `crossref_response.json`, giúp giữ data lineage và khả năng tái lập |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Parse payload Crossref thành schema nội bộ | `parse_crossref_payload`, `PaperRecord` | Chuẩn hóa DOI, title, abstract, authors, subject, ngày và URL; bỏ record không hợp lệ/trùng DOI | Đối chiếu `data/raw/crossref_records.json`: 24 record |
| Fetch có retry và fallback | `fetch_source_records` | Retry các mã 429/5xx; lưu raw response; dùng snapshot khi API lỗi | Kiểm tra code và hai artifact trong `data/raw/` |
| Làm sạch dữ liệu trước embedding | `build_clean_dataframe` | Chuẩn hóa text/list, parse ngày, khử trùng lặp theo `paper_id`, tính `age_days` | Đối chiếu `data/clean/papers_clean.json` và `.csv` |
| Tạo nội dung embedding có cấu trúc | Cột `text_for_embedding` | Mỗi document gồm Title, Authors, Published, Categories và Summary | Kiểm tra cột trong clean artifacts |
| Bàn giao dữ liệu cho pipeline baseline | Bốn raw/clean artifacts | 24/24 record đi vào index; baseline quality gate đạt 6/6 | `data/quality/baseline_quality_report.json` |

Output cụ thể của phần việc là `data/clean/papers_clean.json`: tập 24 bài báo đã được làm sạch, khử trùng lặp và chuyển thành schema 16 cột. Artifact này là nguồn trực tiếp để tạo embedding và ChromaDB index.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Crossref trả về payload lồng nhau, nhiều trường có thể thiếu hoặc mang nhiều biểu diễn khác nhau. Pipeline cần chuyển dữ liệu đó thành một contract ổn định, tái lập được và phù hợp để embedding. Đồng thời, bước ingestion không được mất khả năng chạy chỉ vì API tạm thời rate-limit hoặc mất mạng.

### Cách triển khai

Trong `crossref.py`, tôi định nghĩa `PaperRecord` làm schema trung gian bất biến. `parse_crossref_payload` duyệt `message.items`, chuẩn hóa text, loại JATS/HTML khỏi abstract, ghép tên tác giả, lấy danh mục và thử nhiều trường ngày theo thứ tự ưu tiên. Record thiếu DOI, title hoặc summary bị loại; DOI đã gặp được loại trùng ngay khi parse.

`fetch_source_records` gọi Crossref với timeout và retry/backoff cho 429, 500, 502, 503, 504. Response gốc được lưu trước khi parse để bảo toàn lineage. Nếu request hoặc payload lỗi, hàm đọc snapshot `crossref_response.json`; nếu cả API lẫn snapshot đều không dùng được thì fail rõ ràng thay vì sinh dữ liệu rỗng.

Trong `cleaning.py`, `build_clean_dataframe` tiếp tục chuẩn hóa title, summary, authors và categories; parse `published`/`updated` về UTC; loại record thiếu trường cốt lõi; khử trùng lặp theo `paper_id`; tính `age_days` từ `run_date`; và tạo `text_for_embedding` theo cấu trúc năm phần. DataFrame cuối cùng được sắp xếp xác định theo `published` và `paper_id`, giúp kết quả ổn định giữa các lần chạy.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Crossref JSON payload hoặc `list[PaperRecord]`; `run_date` kiểu `datetime` |
| Output | DataFrame 16 cột và các artifact JSON/CSV trong `data/raw/`, `data/clean/` |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py`, `requests`, `pandas` |
| Module sử dụng output | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, `src/observability/quality.py`, `src/evaluation/testset.py`, `src/pipelines/phase1.py` |
| Điều kiện lỗi cần xử lý | API timeout/rate-limit/5xx; payload sai schema; thiếu DOI/title/summary; ngày không parse được; DOI trùng; thiếu snapshot fallback |

### Cách xác minh

Lệnh dùng trong môi trường dự án sau khi cài dependency:

```bash
uv sync
PYTHONPATH=src uv run python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); records=load_raw_records(s.paths.raw_records_json); df=build_clean_dataframe(records, datetime.now(timezone.utc)); print(len(records), len(df), df.paper_id.nunique(), df.text_for_embedding.isna().sum())"
```

- **Kết quả mong đợi:** 24 raw records, 24 clean rows, 24 `paper_id` duy nhất và 0 giá trị thiếu ở `text_for_embedding`.
- **Kết quả artifact đã đối chiếu:** `baseline_quality_report.json` ghi nhận 24 records, quality gate thành công 6/6; `freshness_report.json` ghi nhận 24 rows và 1 stale row.
- **Giới hạn lần kiểm tra báo cáo này:** máy hiện tại không có lệnh `uv`; Python hệ thống thiếu `python-dotenv`, vì vậy tôi không tuyên bố đã chạy lại E2E trong phiên này. Các số liệu trong báo cáo được đọc từ artifact đã commit.
- **Artifact/log:** `data/raw/crossref_records.json`, `data/clean/papers_clean.json`, `data/quality/baseline_quality_report.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** dữ liệu cần lấy từ Crossref nhưng môi trường lab có thể mất mạng hoặc bị rate-limit.
- **Các phương án đã cân nhắc:** (1) chỉ gọi API trực tiếp; (2) chỉ dùng snapshot cố định; (3) ưu tiên API, có retry và fallback sang snapshot đã lưu.
- **Phương án đã chọn:** phương án (3).
- **Lý do:** API-first cho phép cập nhật dữ liệu; retry xử lý lỗi tạm thời; snapshot giữ tính reproducibility và giúp pipeline không phụ thuộc hoàn toàn vào mạng. Việc luôn ghi raw response và normalized records cũng tạo lineage rõ ràng. Đổi lại, snapshot có thể cũ nên freshness phải được giám sát ở module observability.
- **Bằng chứng quyết định phù hợp:** cả `crossref_response.json` và `crossref_records.json` tồn tại; pipeline tạo đủ 24 clean records; baseline đạt quality gate 6/6 và freshness SLA với stale ratio 0.0417.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** request Crossref có thể thất bại do timeout, HTTP 429 hoặc 5xx; nếu không xử lý, ingestion dừng và các module sau không có dữ liệu.
- **Bước tái hiện:** chạy ingestion trong điều kiện không có mạng hoặc khi endpoint trả mã thuộc nhóm retry.
- **Nguyên nhân gốc:** nguồn dữ liệu là dịch vụ ngoài, nên tính sẵn sàng và rate limit không nằm trong kiểm soát của pipeline.
- **Cách xử lý:** cấu hình `Retry(total=4, backoff_factor=1.0)`, retry GET cho 429/500/502/503/504, đặt timeout và fallback sang raw snapshot. Nếu snapshot cũng không tồn tại, hàm báo `RuntimeError` rõ ràng.
- **Cách xác minh sau khi sửa:** kiểm tra `load_raw_records` đọc được 24 record từ `data/raw/crossref_records.json`; bốn artifact raw/clean tồn tại và được pipeline downstream sử dụng thành công.
- **Điều học được:** external API phải đi kèm retry, timeout, snapshot và lỗi fail-fast; chỉ retry mà không lưu nguồn thô vẫn chưa đủ để tái lập pipeline dữ liệu.

## 7. Hiểu biết về luồng end-to-end

1. Crossref `/works` trả payload gốc. Pipeline lưu raw response, parse thành `PaperRecord`, làm sạch thành DataFrame, tạo `text_for_embedding`, sinh vector bằng `sentence-transformers/all-MiniLM-L6-v2`, rồi index document cùng `paper_id` và metadata vào ChromaDB.
2. Evaluation set có 10 câu thuộc bốn nhóm `summary`, `authors`, `date`, `categories`. Mỗi câu giữ `ground_truth_doc_ids`. Retrieval hit khi ít nhất một ID đúng xuất hiện trong top-k; answer quality được đo bằng token F1 và judge metrics so với ground truth.
3. Quality checks kiểm tra cấu trúc và tính hợp lệ tại thời điểm chạy: row count, null, uniqueness và độ dài summary. Freshness monitoring tập trung vào tuổi dữ liệu qua `age_days > 180`, tính stale ratio và so với SLA tối đa 25%. Một dataset có thể đúng schema nhưng vẫn cũ.
4. Phải dùng cùng test set cho baseline, corrupted và repaired để giữ biến kiểm soát. Nếu đổi câu hỏi hoặc ground truth giữa các trạng thái thì chênh lệch metric có thể do benchmark thay đổi, không thể quy cho corruption/repair.
5. Repair thành công khi clean/repaired artifacts được tái tạo từ raw source tin cậy, quality gate trở lại 6/6, freshness trở lại FRESH, và các metric retrieval/answer quay về mức baseline. Trong kết quả hiện tại, hit rate, token F1, judge accuracy và mean judge score đều phục hồi hoàn toàn.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 | Corruption làm mất 40 điểm phần trăm hit rate; repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.8526 | 1.0000 | Context lỗi/rỗng làm chất lượng answer giảm dù hệ thống không crash |
| `judge_accuracy` | 1.0000 | 0.9000 | 1.0000 | Một phần answer bị judge đánh giá không chính xác sau corruption |
| `mean_judge_score` | 5.0000 | 4.6000 | 5.0000 | Mức giảm nhỏ hơn retrieval vì một số câu vẫn lấy được context đủ dùng |
| Quality checks | PASS 6/6 | FAIL 4/6 | PASS 6/6 | Corrupted vi phạm uniqueness và độ dài summary |
| Freshness status | FRESH | STALE | FRESH | Stale-date/drop-latest đẩy dataset vượt SLA; repair khôi phục |

### Kết luận từ số liệu

1. Blank summary, noise, stale date, drop-latest và duplicate rows → quality gate giảm từ 6/6 xuống 4/6 và freshness chuyển FRESH thành STALE → retrieval hit rate giảm từ 1.0 xuống 0.6, token F1 giảm còn 0.8526.
2. Rebuild từ raw records sạch, chạy lại cleaning và re-index → quality/freshness trở lại PASS 6/6 và FRESH → toàn bộ bốn agent metrics trở về đúng baseline.

Corruption ảnh hưởng rõ nhất đến retrieval là nhóm làm mất hoặc làm méo nội dung dùng để embedding: `blank_summary`, `inject_noise` và `drop_latest_records`. Corruption log cho thấy 7 summary bị làm rỗng, 4 summary bị chèn noise và 4 record mới nhất bị bỏ. Vì summary là một trong năm phần của `text_for_embedding`, thay đổi này tác động trực tiếp đến vector và khả năng xuất hiện trong top-k.

Điểm khác kỳ vọng là dữ liệu corrupted vẫn giữ judge accuracy 0.9 và mean judge score 4.6 dù retrieval hit rate chỉ còn 0.6. Giả thuyết hợp lý là top-k vẫn chứa ngữ cảnh có phần nội dung gần đúng, và các câu hỏi metadata như tác giả/ngày/danh mục ít nhạy hơn với summary corruption. Việc đối chiếu `corrupted_answers.json` cùng test set cố định là cách kiểm tra từng sample thay vì chỉ nhìn metric tổng hợp.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data lineage cần cả response gốc lẫn records đã parse; clean artifact không thể thay thế nguồn thô khi cần audit hoặc repair.
2. Data quality và freshness là hai tín hiệu bổ sung: đúng schema/unique không đồng nghĩa dữ liệu đủ mới, và freshness tốt không đảm bảo text đủ chất lượng để embedding.
3. RAG có thể gặp silent failure: pipeline và agent vẫn chạy nhưng retrieval/answer metric giảm. Vì vậy cần gate dữ liệu trước indexing và benchmark cố định sau mỗi thay đổi.

### Nếu có thêm thời gian

Tôi sẽ bổ sung pytest cho parser và cleaner với các fixture: payload thiếu field, abstract có JATS tag, ngày chỉ có năm/tháng, duplicate DOI, HTTP 429 và snapshot fallback. Mục tiêu đo được là coverage của `src/ingestion/` trên 90%, mọi case tạo schema đúng và test offline không phụ thuộc Crossref.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Vũ Gia Huy  
**Ngày xác nhận:** 2026-09-26
