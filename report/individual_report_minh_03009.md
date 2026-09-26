# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Phạm Anh Minh |
| MSSV | 2A202603009 |
| Khóa/Lớp | K4-L3B-DAY10 |
| Tên nhóm | onedayonename |
| Vai trò chính | Evaluation & Corruption, Support |
| Repository | https://github.com/MinhTienNguyen05/K4-L3B-DAY10-onedayonename-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Evaluation test set | src/evaluation/testset.py, build_test_set | Cleaned dataframe | data/eval/test_set.json, 10 câu hỏi | Hoàn thành |
| Corruption suite | src/ingestion/corruption.py, corrupt_clean_dataframe | Cleaned dataframe | 6 scenarios, corruption_log.json | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Review và tích hợp evaluation/corruption | Minh Tiến, pipeline orchestration | Ba trạng thái dùng chung evaluation set và có comparison report |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Tạo evaluation benchmark | src/evaluation/testset.py | 10 câu hỏi, 4 question types | data/eval/test_set.json |
| Tiêm lỗi dữ liệu | src/ingestion/corruption.py | 6 corruption scenarios | data/results/corruption_log.json |
| Đối chiếu tác động RAG | data/results/*metrics.json | Hit rate 100% → 60% → 100% | data/reports/corruption_report.md |

Output cụ thể: test set gồm summary (3), authors (3), date (2), categories (2); log ghi drop latest 4, blank summary 7, noise 4, truncate title 3, stale date 4 và duplicate rows 4.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần có evaluation set cố định để đo chất lượng retrieval/answer và mô phỏng các lỗi dữ liệu để kiểm tra Quality Gate cùng mức suy giảm của RAG agent.

### Cách triển khai

Evaluation set được tạo từ cleaned dataframe, mỗi câu hỏi giữ question type, ground truth và ground-truth document ID. Corruption áp dụng drop latest, blank summary, inject noise, truncate title, stale date và duplicate rows; đồng thời ghi log record bị tác động. Repair đọc lại raw snapshot và chạy lại cleaning.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | data/clean/papers_clean.json và cleaned dataframe |
| Output | data/eval/test_set.json, corrupted dataset, corruption_log.json |
| Module phụ thuộc | src/ingestion/cleaning.py, core/config.py |
| Module sử dụng output | src/pipelines/phase1.py, corruption_flow.py, evaluation metrics |
| Điều kiện lỗi cần xử lý | Missing summary, duplicate paper_id, stale date, thiếu record, text noise |

### Cách xác minh

    uv run python script/run_phase1.py
    uv run python script/run_corruption_flow.py

- Kết quả mong đợi: baseline tạo test set; corruption tạo log và metrics; repair phục hồi.
- Kết quả thực tế: baseline hit rate 100%; corrupted 60%; repaired 100%.
- Artifact/log: data/eval/test_set.json, data/results/corruption_log.json, data/results/*metrics.json.

## 5. Một quyết định kỹ thuật quan trọng

- Bối cảnh: Cần so sánh công bằng ba trạng thái.
- Các phương án đã cân nhắc: tạo test set riêng hoặc giữ một test set chung.
- Phương án đã chọn: dùng chung data/eval/test_set.json.
- Lý do: metric phản ánh thay đổi dữ liệu/index, không bị nhiễu bởi câu hỏi khác.
- Bằng chứng: baseline và repaired cùng đạt 100% hit rate, corrupted giảm còn 60% trên cùng 10 câu hỏi.

## 6. Một lỗi hoặc blocker đã xử lý

- Triệu chứng: corrupted dataset vẫn chạy nhưng retrieval và answer metrics giảm.
- Lệnh tái hiện: uv run python script/run_corruption_flow.py.
- Nguyên nhân gốc: blank summary, duplicate và stale date là silent failure ở tầng dữ liệu.
- Cách xử lý: ghi corruption log, chạy Quality Gate, re-ingest raw records, clean và re-index.
- Cách xác minh: corrupted quality FAIL/hit rate 60%; repaired PASS 6/6/hit rate 100%.
- Điều học được: không thể chỉ dựa vào exit code để đánh giá pipeline.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. Crossref tạo raw records; ingestion lưu snapshot, cleaning chuẩn hóa và tạo text_for_embedding; embedding được lưu trong ChromaDB.
2. Evaluation set chứa câu hỏi, type, ground truth và document IDs; retrieval hit rate đo đúng tài liệu, còn F1/judge đo câu trả lời.
3. Quality checks kiểm tra schema/giá trị như null, uniqueness, row count và summary length; freshness kiểm tra tuổi dữ liệu theo threshold 180 ngày.
4. Dùng cùng test set để metric chỉ phản ánh corruption/repair.
5. Repair thành công khi Quality Gate trở lại 6/6, freshness FRESH và metrics về baseline: hit rate 100%, F1 1.0000, judge accuracy 100%, score 5.00.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| retrieval_hit_rate | 100% | 60% | 100% | Ngữ cảnh lỗi làm mất tài liệu liên quan. |
| mean_token_f1 | 1.0000 | 0.8526 | 1.0000 | Text bẩn làm câu trả lời kém chính xác. |
| judge_accuracy | 100% | 90% | 100% | Context lỗi làm giảm accuracy. |
| mean_judge_score | 5.00 | 4.60 | 5.00 | Chất lượng giảm nhưng không crash. |
| Quality checks | PASS 6/6 | FAIL | PASS 6/6 | Quality Gate phát hiện lỗi. |
| Freshness status | FRESH | STALE | FRESH | Stale date/drop latest vi phạm SLA. |

### Kết luận từ số liệu

1. Data corruption → Quality Gate FAIL và freshness STALE → hit rate giảm 100% xuống 60%, F1 giảm 1.0000 xuống 0.8526.
2. Repair từ raw snapshot → Quality Gate PASS 6/6 và freshness FRESH → toàn bộ agent metrics trở lại baseline.

Corruption ảnh hưởng rõ nhất là nhóm làm mất hoặc làm méo ngữ cảnh embedding, thể hiện qua hit rate giảm 40 điểm phần trăm. Pipeline không crash dù dữ liệu lỗi, nên observability là cần thiết.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw snapshot và data lineage giúp repair reproducibly.
2. Quality/freshness là tín hiệu độc lập với việc pipeline có exit code thành công.
3. Lỗi dữ liệu nhỏ có thể làm RAG suy giảm âm thầm; cần benchmark cố định.

### Nếu có thêm thời gian

Bổ sung schema-drift checks, nhiều mức corruption và bật Ragas với RUN_RAGAS=1. Đo bằng Quality Gate pass rate, freshness ratio và retrieval/answer metrics trên cùng test set.

## 10. Cam kết của thành viên

- [x] Nội dung phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi giải thích được luồng end-to-end.
- [x] Kết luận đều có artifact hoặc metric đối chiếu.
- [x] Không ghi đã chạy thành công cho phần chưa kiểm chứng.
- [x] Không chứa .env, API key, token hoặc secret.
- [x] Không sao chép nguyên văn báo cáo nhóm/thành viên khác.

**Họ và tên:** Phạm Anh Minh  
**Ngày xác nhận:** 2026-09-26

