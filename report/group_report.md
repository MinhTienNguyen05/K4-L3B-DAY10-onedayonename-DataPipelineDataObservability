# Báo cáo nhóm — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/Lớp | K4-L3B-DAY10 |
| Tên nhóm | onedayonename |
| Repository | https://github.com/MinhTienNguyen05/K4-L3B-DAY10-onedayonename-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

### Thành viên và phân công

| Thành viên | Vai trò |
|---|---|
| Gia Huy | Ingestion/cleaning: src/ingestion/crossref.py, cleaning.py |
| Mạnh Hùng | Observability: src/observability/quality.py, reporting.py |
| Anh Minh | Evaluation/corruption: testset.py, corruption.py |
| Thế Việt | Evaluation integration và test flow |
| Minh Tiến | Orchestration: src/pipelines/phase1.py, corruption_flow.py |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline end-to-end cho hệ thống RAG: lấy dữ liệu từ Crossref REST API, lưu raw records, làm sạch 24 bài báo, tạo text_for_embedding, xây dựng embedding/index ChromaDB, đánh giá baseline, kiểm tra quality/freshness, tiêm lỗi, đánh giá lại và repair từ raw snapshot. Evaluation set có 10 câu hỏi thuộc bốn nhóm summary, authors, date và categories.

Baseline đạt retrieval hit rate 100%, mean token F1 1.0000, judge accuracy 100% và mean judge score 5.00/5. Quality Gate đạt 6/6 expectations; freshness có 1/24 record stale, tương đương 4.2%, dưới SLA 25%. Sau sáu kịch bản corruption, hit rate giảm còn 60%, F1 còn 0.8526, judge accuracy còn 90%, score còn 4.60; Quality Gate FAIL và freshness STALE. Repair từ raw records khôi phục toàn bộ metric về baseline. Ragas chưa chạy vì chưa bật RUN_RAGAS=1.

## 3. Kiến trúc và luồng dữ liệu

Luồng dữ liệu: Crossref API/raw snapshot → raw records → cleaning → embedding/index ChromaDB → baseline evaluation → quality/freshness → corruption → re-index/evaluate → repair từ raw → comparison report.

| Khối | Output | Owner |
|---|---|---|
| Ingestion | data/raw/crossref_response.json, crossref_records.json | Gia Huy |
| Cleaning | data/clean/papers_clean.json/.csv | Gia Huy |
| Embedding/index | data/embeddings/, data/chroma/ | Minh Tiến |
| Evaluation | data/eval/test_set.json, data/results/ | Anh Minh, Thế Việt |
| Observability | data/quality/*.json | Mạnh Hùng |
| Corruption/repair | corruption_log.json, repaired artifacts | Minh Tiến |

## 4. Cách tái hiện kết quả

Cấu hình chính: embedding sentence-transformers/all-MiniLM-L6-v2, 24 Crossref records, retrieval top_k=4, freshness threshold 180 ngày, stale limit 25%. LLM provider/model đọc từ .env, mặc định Gemini / gemini-2.5-flash. Lệnh chạy:

    uv sync
    uv run python script/run_phase1.py
    uv run python script/run_corruption_flow.py

## 5. Ingestion, cleaning và data contract

Nguồn là Crossref REST API với query “agentic retrieval augmented generation large language model”, filter has-abstract=true và giới hạn 24 records. Raw response và raw records được lưu để bảo toàn lineage và fallback offline.

Các trường chính gồm paper_id, title, authors, published, categories, summary, age_days và text_for_embedding. Pipeline chuẩn hóa dữ liệu, parse ngày, tính age_days, tạo text_for_embedding từ title/authors/published/categories/summary và loại duplicate theo paper_id. Document ID là paper_id/DOI.

## 6. Evaluation setup

Evaluation gồm 10 câu hỏi: summary (3), authors (3), date (2), categories (2). Ground truth lấy từ cleaned dataset. Cùng một data/eval/test_set.json được dùng cho baseline, corrupted và repaired.

## 7. Kết quả baseline

Artifacts baseline gồm data/raw/, data/clean/, data/embeddings/, data/chroma/, data/eval/test_set.json, data/results/baseline_metrics.json và data/reports/phase1_report.md.

| Metric | Baseline |
|---|---:|
| retrieval_hit_rate | 100% |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 100% |
| mean_judge_score | 5.00/5 |
| Ragas | Chưa chạy; cần bật RUN_RAGAS=1 |

## 8. Quality và freshness

Quality Gate kiểm tra row count 5–5000, paper_id không null, paper_id unique, title không null, text_for_embedding không null và summary dài tối thiểu 30 ký tự. Baseline đạt 6/6 PASS.

Freshness report: 24 records, 1 stale record, stale ratio 0.0417 (4.2%), threshold 180 ngày, SLA limit 0.25; trạng thái FRESH. Latest publication là 2026-07-22 và oldest là 2026-03-28.

## 9. Corruption scenarios và repair

| Scenario | Số record |
|---|---:|
| Drop latest records | 4 |
| Blank summary | 7 |
| Inject noise | 4 |
| Truncate title | 3 |
| Stale date | 4 |
| Duplicate rows | 4 |

Chi tiết có trong data/results/corruption_log.json. Repair đọc data/raw/crossref_records.json, chạy lại cleaning và re-index thay vì chỉ che lỗi trên corrupted dataset.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| retrieval_hit_rate | 100% | 60% | 100% |
| mean_token_f1 | 1.0000 | 0.8526 | 1.0000 |
| judge_accuracy | 100% | 90% | 100% |
| mean_judge_score | 5.00 | 4.60 | 5.00 |
| Quality checks | PASS (6/6) | FAIL | PASS (6/6) |
| Freshness | FRESH | STALE | FRESH |

Corruption làm Quality Gate thất bại và làm retrieval/answer metrics suy giảm. Re-ingestion, cleaning và re-index khôi phục quality, freshness và toàn bộ metric về baseline. Đây là bằng chứng cho vai trò của observability và pipeline idempotent trong việc phát hiện, chẩn đoán và phục hồi silent failure.

## 11. Vấn đề tích hợp quan trọng

RAG vẫn có thể chạy khi dữ liệu corrupted, nên chỉ kiểm tra exit code là chưa đủ. Nhóm xử lý bằng Quality Gate và freshness checks trước khi index/evaluate, đồng thời lưu artifact riêng cho baseline, corrupted và repaired.

## 12. Giới hạn và hướng cải thiện

Ragas chưa bật; có thể chạy lại với RUN_RAGAS=1. Dataset chỉ có 24 bài và corruption còn synthetic, nên cần mở rộng record/domain và bổ sung schema drift, lỗi API, missing batch và index failure. Mỗi thành viên cần hoàn thiện individual report riêng.

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác; tên nhóm là `onedayonename`.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện baseline và corruption flow đã được ghi trong báo cáo.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Kết luận quality/freshness khớp với các file trong `data/quality/`.
- [x] Các đường dẫn report và artifact thực tế đã được ghi rõ.
- [x] Mỗi thành viên có phần vai trò/phân công trong báo cáo nhóm.
- [x] Không có `.env`, API key, token hoặc secret trong report.
