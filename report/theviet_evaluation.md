# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Ngô Thế Việt |
| MSSV | [Điền MSSV] |
| Khóa/Lớp | K4-L3B-DAY10 |
| Tên nhóm | onedayonename |
| Vai trò chính | Evaluation Integration & Test Flow (Tích hợp luồng đánh giá RAG & Kiểm thử đối chiếu Benchmark) |
| Repository | https://github.com/MinhTienNguyen05/K4-L3B-DAY10-onedayonename-DataPipelineDataObservability |
| Branch | `theviet-evaluation` |
| Commit | `06efb82` (merged to `main`) |
| Ngày hoàn thành | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

Theo đúng bảng phân công trong `docs/TEAM.md` và `report/group_report.md`, tôi phụ trách khối **Evaluation Integration & Test Flow**, đồng sở hữu module Evaluation cùng Anh Minh:

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Evaluation Benchmark & Testset | `src/evaluation/testset.py`: `build_test_set` | Cleaned DataFrame (`papers_clean.json`), đường dẫn output | `data/eval/test_set.json` (bộ 10 câu hỏi chuẩn hóa gồm 4 nhóm câu hỏi nghiệp vụ) | Hoàn thành |
| Synthetic Corruption Suite & Logging | `src/ingestion/corruption.py`: `corrupt_clean_dataframe` | Cleaned DataFrame, đường dẫn log | `papers_clean_corrupted.json`, `.csv` và `data/results/corruption_log.json` (6 kịch bản tiêm lỗi) | Hoàn thành |
| Evaluation Integration & Benchmark Flow | `script/run_phase1.py`, `script/run_corruption_flow.py` | Vector Index (ChromaDB), `test_set.json`, LLM QA Agent | Bộ đối chiếu 3 trạng thái: `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |

Tôi trực tiếp sở hữu và đảm bảo tính toàn vẹn của luồng kiểm thử đánh giá (Test Flow): bảo đảm tập câu hỏi đánh giá bất biến (`test_set.json`), xác thực các kịch bản tiêm lỗi tổng hợp (`corruption.py`), và thẩm định kết quả đo lường chất lượng truy hồi và sinh câu trả lời xuyên suốt 3 trạng thái.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Tích hợp luồng Evaluation vào Pipeline Orchestration | Minh Tiến (`src/pipelines/phase1.py`, `corruption_flow.py`) | Đảm bảo runner đánh giá `evaluate_pipeline` nhận đúng vector index tương ứng từng trạng thái (`papers-baseline`, `papers-corrupted`, `papers-repaired`) và xuất đúng file answers/metrics. |
| Kiểm chứng phát hiện lỗi với Observability | Mạnh Hùng (`src/observability/quality.py`) | Xác minh rằng các kịch bản tiêm lỗi (như duplicate rows, blank summary) được Data Quality Gate (GX 1.x) phát hiện chính xác với cờ `success=False` trước khi bước vào evaluation. |
| Rà soát số liệu thực nghiệm nhóm | Nhóm `onedayonename` (`report/group_report.md`) | Đồng bộ các chỉ số đo lường thực tế từ `data/results/` vào báo cáo nhóm và bảng đối chiếu `data/reports/corruption_report.md`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng và xác thực bộ Test Set chuẩn | `src/evaluation/testset.py` | `data/eval/test_set.json` (10 câu hỏi, 4 dạng: summary, authors, date, categories) | Đọc file JSON: đủ 10 câu, ground truth và ground_truth_doc_ids chuẩn theo DOI |
| Thiết kế và kiểm thử 6 kịch bản tiêm lỗi | `src/ingestion/corruption.py` | `data/results/corruption_log.json` và bộ dữ liệu bẩn `papers_clean_corrupted.json` | Kiểm tra nhật ký ghi nhận đầy đủ 6 kịch bản, số lượng dòng và danh sách paper_id bị tác động |
| Thực thi và kiểm thử luồng Benchmark 3 trạng thái | Evaluation Flow trong pipeline runner | 3 bộ metrics: `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Đối chiếu định lượng trong `data/reports/corruption_report.md` |

### Output cụ thể tạo ra và bàn giao:

1. **`data/eval/test_set.json`:** Bộ test set chuẩn gồm 10 câu hỏi bao phủ 4 tác vụ tra cứu học thuật:
   - 3 câu hỏi tóm tắt (`summary`): Ground truth trích xuất câu đầu tiên của abstract.
   - 3 câu hỏi tác giả (`authors`): Ground truth là danh sách tác giả nối chuỗi (`authors_joined`).
   - 2 câu hỏi ngày xuất bản (`date`): Ground truth là ngày phát hành chuẩn ISO.
   - 2 câu hỏi danh mục (`categories`): Ground truth là chủ đề bài báo (`categories_joined`).
   Mỗi câu hỏi đều được gán `ground_truth_doc_ids` (DOI) để làm chuẩn đo lường `retrieval_hit_rate`.

2. **`data/results/corruption_log.json`:** Nhật ký tiêm lỗi chi tiết, ghi nhận 6 kịch bản:
   - `drop_latest_records`: Cắt giảm 4 bài báo mới nhất (20%) để kích hoạt cảnh báo Freshness.
   - `blank_summary`: Xóa trắng tóm tắt của 7 bài báo (30%) để thử thách Quality Gate.
   - `inject_noise`: Chèn chuỗi `"!!!CORRUPTED_SYNTHETIC_NOISE_VECTOR_SHIFT!!!"` vào 4 bài báo làm lệch vector.
   - `truncate_title`: Cắt ngắn tiêu đề của 3 bài báo xuống dưới 8 ký tự.
   - `stale_date`: Lùi ngày xuất bản về quá khứ 365 ngày trên 4 bài báo.
   - `duplicate_rows`: Nhân đôi 4 bài báo để kiểm tra vi phạm Uniqueness.

3. **Bộ dữ liệu đo lường định lượng 3 trạng thái:**
   - Baseline: Hit Rate **100%**, Mean Token F1 **1.0000**, LLM Judge Accuracy **100%**, Judge Score **5.00/5.0**.
   - Corrupted: Hit Rate giảm sâu còn **60%**, Token F1 giảm còn **0.8526**, Judge Accuracy còn **90%**, Judge Score còn **4.60**.
   - Repaired: Phục hồi hoàn toàn về Hit Rate **100%**, Token F1 **1.0000**, Judge Accuracy **100%**, Judge Score **5.00/5.0**.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG Agent, lỗi dữ liệu hiếm khi làm chương trình sập ngay lập tức mà thường gây ra hiện tượng **Silent Failure**: mã nguồn vẫn chạy bình thường với exit code 0, embedding vẫn tạo vector, nhưng vector bị sai lệch ngữ nghĩa (semantic drift), dẫn đến việc tìm kiếm sai tài liệu và mô hình LLM đưa ra câu trả lời bịa đặt (hallucination).

Nhiệm vụ kỹ thuật của tôi là:
1. Thiết kế bộ công cụ tiêm lỗi có chủ đích (`corruption.py`) để mô phỏng các sự cố dữ liệu thực tế (mất mát dữ liệu, dữ liệu rác, lỗi bản ghi trùng lặp, dữ liệu lỗi thời).
2. Xây dựng bộ test set benchmark bất biến (`testset.py`) làm thước đo cố định giúp đo lường định lượng chính xác sự suy giảm của hệ thống khi gặp dữ liệu bẩn và sự phục hồi sau khi sửa chữa.
3. Tích hợp và kiểm thử toàn bộ luồng evaluation (Test Flow) để trích xuất số liệu khách quan cho nhóm.

### Cách triển khai

#### 1. Xây dựng Test Set Benchmark (`src/evaluation/testset.py`)
- Định nghĩa 10 cấu hình câu hỏi đại diện cho 4 loại câu hỏi nghiệp vụ.
- Duyệt qua DataFrame dữ liệu sạch theo chỉ số modulo `idx % n_docs` để phân bổ đều các câu hỏi trên các bài báo.
- Trích xuất ground-truth tự động bằng các hàm chuẩn hóa: `first_sentence` cho tóm tắt, ghép danh sách cho tác giả/danh mục, và chuỗi ngày chuẩn.
- Gắn chuẩn xác DOI vào mảng `ground_truth_doc_ids` phục vụ thuật toán so khớp Top-$K$ Retrieval.

#### 2. Kỹ thuật Tiêm Lỗi Đa Chiều (`src/ingestion/corruption.py`)
- Tác động trực tiếp vào các chiều chất lượng dữ liệu:
  - Tính mới (Freshness): `drop_latest_records` (loại bỏ 20% bài báo mới nhất) và `stale_date` (lùi 365 ngày).
  - Tính toàn vẹn (Completeness): `blank_summary` (xóa tóm tắt của 7 bài báo).
  - Độ chính xác ngữ nghĩa (Semantic Validity): `inject_noise` (chèn chuỗi nhiễu vào summary) và `truncate_title` (rút ngắn tiêu đề).
  - Tính duy nhất (Uniqueness): `duplicate_rows` (nhân bản 4 bản ghi).
- Tái tạo lại trường `summary_chars` và cấu trúc 5 phần của `text_for_embedding` (Title, Authors, Published, Categories, Summary) để khi vectorizer chạy, embedding sẽ bị ô nhiễm thực sự.
- Ghi nhật ký chi tiết danh sách `paper_id` bị ảnh hưởng ra `data/results/corruption_log.json`.

#### 3. Tích hợp và Xác Thực Test Flow
- Phối hợp thực thi luồng test: nạp `test_set.json` cố định vào module đánh giá `src/evaluation/metrics.py`.
- Thuật toán đo lường:
  - `retrieval_hit_rate`: Kiểm tra xem trong Top-$K=4$ văn bản được retrieve từ ChromaDB có chứa ít nhất một `ground_truth_doc_ids` hay không.
  - `mean_token_f1`: Tách từ (tokenize) câu trả lời của QA Agent và `ground_truth` để tính toán Precision, Recall và F1-score trên từng token.
  - `judge_accuracy` & `mean_judge_score`: Sử dụng LLM Judge chấm điểm theo rubric định tính (1–5) và nhị phân (Đúng/Sai).

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Cleaned DataFrame (`papers_clean.json`), cấu hình settings hệ thống |
| Output | `data/eval/test_set.json`, `data/results/corruption_log.json`, dữ liệu bẩn `papers_clean_corrupted.json`, các file metrics định lượng |
| Module phụ thuộc | `src/core/utils.py`, `pandas`, `pathlib` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `src/evaluation/metrics.py`, `src/observability/reporting.py` |
| Điều kiện lỗi cần xử lý | Xử lý an toàn khi DataFrame rỗng; định dạng dữ liệu tác giả là list hoặc string; bảo đảm serialization JSON không bị lỗi khi tiêm ký tự đặc biệt. |

### Cách xác minh

Lệnh kiểm thử độc lập cho hai module:

```bash
# 1. Kiểm thử sinh testset:
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'✅ Testset generated: {len(ts)} questions')"

# 2. Kiểm thử bộ tiêm lỗi:
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); cdf=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'✅ Corrupted data size: {len(cdf)}, blanks: {(cdf[\"summary\"] == \"\").sum()}')"
```

- **Kết quả mong đợi:** Sinh đủ 10 câu hỏi test với 4 loại; tập corrupt ghi nhận đầy đủ 6 kịch bản lỗi và nhật ký `corruption_log.json` được tạo thành công.
- **Kết quả thực tế đối chiếu từ artifact:**
  - `data/eval/test_set.json` chứa đúng 10 câu hỏi chuẩn.
  - `data/results/corruption_log.json` thể hiện rõ 24 bản ghi ban đầu bị tác động bởi 6 kịch bản lỗi.
  - `data/reports/corruption_report.md` ghi nhận sự suy giảm rõ nét trên bộ câu hỏi test này.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi thiết kế cơ chế đo lường hiệu năng 3 trạng thái (Baseline vs Corrupted vs Repaired), nhóm cần quyết định cách tạo và sử dụng tập dữ liệu đánh giá (Evaluation Set).
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Dynamic Generation):* Mỗi lần đánh giá ở từng pha, tự động sinh ngẫu nhiên một tập câu hỏi mới từ tập dữ liệu của pha đó.
  2. *Phương án B (Static Golden Benchmark):* Tạo một tập 10 câu hỏi benchmark chuẩn từ tập dữ liệu sạch ban đầu, lưu trữ bất biến tại `data/eval/test_set.json`, và tái sử dụng nguyên vẹn tập câu hỏi này để kiểm thử cho cả 3 trạng thái Baseline, Corrupted và Repaired.
- **Phương án đã chọn:** Phương án B (Static Golden Benchmark).
- **Lý do:**
  - Để đo lường chính xác tác động của biến số độc lập là chất lượng dữ liệu (sạch vs bẩn vs phục hồi), thước đo đánh giá (test set) bắt buộc phải là một **biến kiểm soát bất biến (controlled variable)**.
  - Nếu sinh test set động trên dữ liệu bẩn, câu hỏi sinh ra từ văn bản rác sẽ không có ground-truth hợp lệ hoặc câu hỏi bị thay đổi độ khó, làm sai lệch hoàn toàn kết quả so sánh.
  - Giữ nguyên test set cho phép quan sát trực tiếp hiện tượng: cùng một câu hỏi, tại sao ở Baseline hệ thống tìm ra tài liệu (Hit Rate 100%), nhưng khi dữ liệu bị corrupt thì hệ thống không còn tìm thấy tài liệu liên quan nữa (Hit Rate rơi xuống 60%).
- **Bằng chứng quyết định phù hợp:**
  - Bảng đối chiếu thực nghiệm chứng minh sự sụt giảm chính xác: Trên cùng 10 câu hỏi, Retrieval Hit Rate giảm từ **100%** xuống **60%**, và khi Repaired thì phục hồi chính xác trở lại **100%**.
  - Token F1 giảm từ **1.0000** xuống **0.8526** và phục hồi về **1.0000**. Kết quả này phản ánh chân thực 100% tác động của chất lượng dữ liệu mà không bị nhiễu bởi sự thay đổi của câu hỏi.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Hiện tượng **Silent Failure** — Khi chạy luồng đánh giá ban đầu trên dữ liệu bị corrupt, chương trình chạy hoàn toàn bình thường, không ném exception nào, exit code = 0. Tuy nhiên, khi kiểm tra kỹ các file kết quả `corrupted_answers.json` và `corrupted_metrics.json`, chỉ số `retrieval_hit_rate` bị tụt giảm nghiêm trọng từ 1.0 xuống 0.6, và mô hình LLM bắt đầu sinh câu trả lời sai lệch hoặc bịa đặt (hallucination) do không nhận được context đầy đủ.
- **Lệnh tái hiện:**
  ```bash
  python script/run_corruption_flow.py
  ```
- **Nguyên nhân gốc:**
  1. Thư viện vector store (ChromaDB) và model embedding (`sentence-transformers`) vẫn nhận chuỗi rỗng `""` hoặc chuỗi rác `!!!CORRUPTED...` như một đoạn văn bản hợp lệ và tính vector bình thường.
  2. Không có lỗi cú pháp xảy ra ở tầng mã nguồn ứng dụng, nhưng chất lượng biểu diễn không gian vector bị phá hủy, dẫn tới thuật toán tìm kiếm Nearest Neighbors trả về các văn bản không liên quan.
- **Cách xử lý:**
  1. Bổ sung việc tái tạo trường `text_for_embedding` ngay sau bước tiêm lỗi trong `src/ingestion/corruption.py` để bảo đảm vector store phản ánh đúng trạng thái ô nhiễm của dữ liệu.
  2. Phối hợp với module Observability (Mạnh Hùng) thiết lập Quality Gate thông qua **Great Expectations 1.x** (với các ràng buộc nghiêm ngặt: kiểm tra độ dài summary >= 30 ký tự, kiểm tra tính duy nhất của paper_id, kiểm tra null). Khi dữ liệu bị corrupt, Quality Gate lập tức kích hoạt cờ `success=False` để chặn đứng dữ liệu bẩn trước khi đưa vào embedding index.
  3. Phối hợp với module Orchestration (Minh Tiến) triển khai cơ chế **Idempotent Repair**: khi phát hiện lỗi, hệ thống tự động tái nạp từ snapshot thô tin cậy (`crossref_records.json`), chạy lại quy trình làm sạch và tái lập lại index ChromaDB sạch.
- **Cách xác minh sau khi sửa:**
  - Báo cáo `corrupted_quality_report.json` kích hoạt **FAILED** đúng như mong đợi (phát hiện lỗi độ dài summary và bản ghi duplicate).
  - Báo cáo `repaired_quality_report.json` đạt trạng thái **PASSED 6/6**.
  - Báo cáo `repaired_metrics.json` ghi nhận Retrieval Hit Rate lấy lại mốc **100%**, Mean Token F1 đạt **1.0000**.
- **Điều học được:**
  Unit test chỉ kiểm tra được logic code (logic không crash). Trong kỷ nguyên AI và Data-centric, bắt buộc phải có **Data Quality Testing** và **Continuous Benchmark Evaluation** để phát hiện các lỗi suy thoái ngầm (Silent Data Degradation).

---

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời chi tiết cho 5 câu hỏi trọng tâm:**

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu thô bắt đầu từ Crossref REST API qua endpoint `/works`, được lưu trữ nguyên bản vào `data/raw/crossref_response.json` và parse thành các đối tượng `PaperRecord` chuẩn trong `data/raw/crossref_records.json` (bảo toàn Data Lineage).
   - Module cleaning chuẩn hóa dữ liệu, loại bỏ ký tự rác, tính toán `age_days` phục vụ giám sát độ tươi mới, và cấu trúc hóa trường `text_for_embedding` gồm 5 thành phần: Title, Authors, Published, Categories, Summary.
   - Dữ liệu sạch được ghi vào `data/clean/papers_clean.json`. Mô hình embedding `sentence-transformers/all-MiniLM-L6-v2` chuyển đổi `text_for_embedding` thành vector dense 384 chiều và nạp cùng metadata vào collection `papers-baseline` trong cơ sở dữ liệu vector ChromaDB (`data/chroma/`).

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Tập `test_set.json` cung cấp 10 câu hỏi truy vấn chuẩn.
   - Để đo **Retrieval Quality:** Mỗi câu hỏi có danh sách `ground_truth_doc_ids` (chính là DOI của bài báo chứa thông tin). Khi truy vấn, hệ thống lấy Top-$K=4$ tài liệu gần nhất từ ChromaDB. Nếu ít nhất một trong các tài liệu trả về có DOI nằm trong `ground_truth_doc_ids`, chỉ số `retrieval_hit` của câu hỏi đó được tính là 1 (ngược lại là 0). Trung bình trên 10 câu hỏi cho ra chỉ số `retrieval_hit_rate`.
   - Để đo **Answer Quality:** Context tìm được cùng câu hỏi được đưa vào LLM để sinh câu trả lời. Câu trả lời của LLM được so sánh với `ground_truth` thông qua chỉ số `Token-level F1` (độ trùng khớp từ vựng) và đưa qua `LLM Judge` để đánh giá ngữ nghĩa theo thang điểm nhị phân (`judge_accuracy`) và thang điểm định tính 1-5 (`judge_score`).

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (Great Expectations 1.x):** Tập trung kiểm định tính toàn vẹn cấu trúc, tính hợp lệ và phân bố tĩnh của dữ liệu tại thời điểm ingest (Schema validation, Not Null, Uniqueness của `paper_id`, độ dài tối thiểu của tóm tắt).
   - **Freshness monitoring (Data Freshness SLA):** Tập trung vào chiều thời gian và tính thời sự của dữ liệu. Module tính toán số ngày trôi qua kể từ khi bài báo xuất bản (`age_days = (run_date - published).days`). Nếu `age_days > 180 ngày`, bài báo bị coi là "stale". Nếu tỷ lệ stale vượt quá ngưỡng SLA quy định (25%), hệ thống sẽ cảnh báo trạng thái **STALE**.
   - *Khác biệt cốt lõi:* Một tập dữ liệu có thể hoàn hảo về mặt cấu trúc (Quality Gate PASS 6/6), nhưng nếu toàn bộ bài báo đều xuất bản từ nhiều năm trước thì hệ thống vẫn vi phạm Freshness SLA (STALE), dẫn tới việc LLM bị cung cấp kiến thức lỗi thời.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Nhằm tuân thủ nguyên lý kiểm soát biến số trong thực nghiệm khoa học. Mục tiêu của bài lab là cô lập và đo lường ảnh hưởng của chất lượng dữ liệu đối với hiệu năng của hệ thống RAG.
   - Nếu mỗi trạng thái sử dụng một tập câu hỏi khác nhau, sự biến động của Hit Rate hoặc Judge Score có thể bắt nguồn từ việc câu hỏi ở pha đó quá dễ hoặc quá khó, chứ không phản ánh đúng tác động của dữ liệu. Dùng chung một test set cố định bảo đảm mọi sự thay đổi trong kết quả đều bắt nguồn trực tiếp từ sự biến đổi của vector index và ngữ cảnh tài liệu.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Repair được xem là thành công khi thỏa mãn đồng thời cả 3 điều kiện được chứng minh qua các artifacts:
     1. **Data Quality Gate:** Báo cáo `data/quality/repaired_quality_report.json` đạt trạng thái **PASS 6/6 Expectations** (loại bỏ hoàn toàn lỗi duplicate và summary rỗng).
     2. **Freshness SLA:** Báo cáo `data/quality/freshness_report.json` đạt trạng thái **FRESH** (tỷ lệ bài báo cũ giảm về 4.17%, nhỏ hơn rất nhiều so với ngưỡng 25%).
     3. **Agent Benchmarks:** Báo cáo `data/results/repaired_metrics.json` chứng minh toàn bộ các chỉ số hiệu năng phục hồi hoàn toàn về mốc Baseline:
        - `retrieval_hit_rate`: Phục hồi từ **60.00%** lên **100.00%**.
        - `mean_token_f1`: Phục hồi từ **0.8526** lên **1.0000**.
        - `judge_accuracy`: Phục hồi từ **90.00%** lên **100.00%**.
        - `mean_judge_score`: Phục hồi từ **4.60** lên **5.00 / 5.0**.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.00% | 60.00% | 100.00% | Bị sụt giảm nặng nề nhất (-40%); việc xóa summary và loại bỏ bài báo mới làm mất ngữ cảnh truy hồi. |
| `mean_token_f1` | 1.0000 | 0.8526 | 1.0000 | Giảm đáng kể (-0.1474); LLM thiếu từ khóa chính xác để tổng hợp câu trả lời chuẩn xác. |
| `judge_accuracy` | 100.00% | 90.00% | 100.00% | Giảm nhẹ (-10%); LLM vẫn trả lời đúng được một số câu hỏi đơn giản về tác giả/danh mục. |
| `mean_judge_score` | 5.00 | 4.60 | 5.00 | Điểm định tính giảm từ mức tuyệt đối 5.0 xuống 4.6 do một số câu trả lời bị mơ hồ hoặc thiếu ý. |
| Quality checks (GX 1.x) | PASS (6/6) | **FAIL** | PASS (6/6) | Quality Gate hoạt động nhạy bén, bắt trúng lỗi duplicate rows và blank summary. |
| Freshness status | FRESH (4.2%) | **STALE** | FRESH (4.2%) | Cơ chế tiêm ngày cũ (stale date) và drop latest đã kích hoạt cảnh báo vi phạm SLA kịp thời. |

### Kết luận từ số liệu

**Hai chuỗi nguyên nhân – bằng chứng định lượng:**

1. **Chuỗi suy thoái (Corruption chain):**  
   Tiêm lỗi dữ liệu (`blank_summary`, `inject_noise`, `drop_latest_records`, `duplicate_rows`) $\rightarrow$ Kích hoạt vi phạm Quality Gate (`success=False` trên 2 expectations) và Freshness SLA báo động `STALE` $\rightarrow$ Vector space bị ô nhiễm làm `retrieval_hit_rate` sụt giảm 40 điểm phần trăm (từ 100% xuống 60%), kéo theo `mean_token_f1` giảm từ 1.0000 xuống 0.8526.
2. **Chuỗi phục hồi (Repair chain):**  
   Thực thi Idempotent Repair tái tạo dữ liệu từ snapshot thô `crossref_records.json` $\rightarrow$ Tái lập clean dataframe, Quality Gate trở lại `PASS 6/6` và Freshness trở lại `FRESH` $\rightarrow$ Tái lập ChromaDB index sạch, phục hồi `retrieval_hit_rate` về 100%, đưa toàn bộ các chỉ số của RAG Agent quay về trạng thái Baseline ban đầu.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**  
Kịch bản `blank_summary` và `drop_latest_records` gây ảnh hưởng nặng nề nhất đến hiệu năng truy hồi:
- `blank_summary` làm rỗng trường thông tin chứa mật độ từ khóa và ngữ nghĩa cao nhất của bài báo. Khi ghép vào `text_for_embedding`, văn bản bị cụt ngủn, khiến thuật toán tìm kiếm tương đồng vector không thể nhận diện được bài báo liên quan đối với các câu hỏi loại `summary`.
- `drop_latest_records` loại bỏ hoàn toàn các bài báo mới ra khỏi index, khiến các câu hỏi truy vấn về các bài báo này hoàn toàn không có khả năng được tìm thấy (Hit = 0).

**Kết quả nào khác với kỳ vọng ban đầu?**  
Ban đầu, tôi dự đoán rằng khi `retrieval_hit_rate` giảm sâu xuống 60%, điểm số của LLM Judge (`judge_accuracy`) sẽ sụt giảm mạnh xuống dưới 60%. Tuy nhiên, kết quả thực tế cho thấy `judge_accuracy` vẫn đạt **90%** và `mean_judge_score` vẫn đạt **4.60/5.0**.  
*Giải thích:* Khi phân tích sâu vào `corrupted_answers.json`, các câu hỏi về tác giả (`authors`), ngày xuất bản (`date`) hoặc danh mục (`categories`) vẫn có thể được LLM trích xuất một phần chính xác từ tiêu đề hoặc ngữ cảnh còn sót lại của các tài liệu khác trong Top-$K$, hoặc các bài báo đó không nằm trong nhóm bị tiêm lỗi nặng. Điều này chứng minh rằng `retrieval_hit_rate` là chỉ số nhạy bén hơn rất nhiều so với LLM Judge trong việc phát hiện suy thoái dữ liệu sớm.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Kiến trúc Data-Centric AI và sự nguy hiểm của Silent Failure:** Trong các hệ sinh thái AI hiện đại, chất lượng của Agent phụ thuộc hoàn toàn vào chất lượng của dữ liệu đầu vào. Lỗi dữ liệu không làm chương trình crash mà âm thầm phá hủy độ chính xác của mô hình. Do đó, việc xây dựng Data Quality Gate chặn trước vector index là bắt buộc đối với mọi hệ thống production.
2. **Giá trị của Idempotent Pipeline và Data Lineage:** Việc bảo lưu snapshot dữ liệu thô (`crossref_records.json`) giúp hệ thống có khả năng tự chữa lành (Self-healing) một cách xác định và tái lập được (reproducible) mà không cần phụ thuộc vào việc gọi lại external API.
3. **Phương pháp luận đánh giá RAG khoa học:** Việc xây dựng một tập Benchmark Test Set cố định, chuẩn hóa và kiểm soát biến số là chìa khóa để đo lường khách quan mọi thay đổi kiến trúc và chất lượng pipeline.

### Nếu có thêm thời gian

Tôi sẽ nghiên cứu và tích hợp sâu bộ khung đánh giá tự động đa tiêu chí **Ragas** (kích hoạt bằng cấu hình `RUN_RAGAS=1`), đo lường toàn diện 4 khía cạnh:
- *Faithfulness:* Đánh giá câu trả lời có bám sát ngữ cảnh tài liệu hay không (phát hiện hallucination).
- *Answer Relevance:* Đánh giá độ phù hợp của câu trả lời với câu hỏi.
- *Context Precision & Context Recall:* Đánh giá chất lượng của bộ lọc truy hồi vector.  
Đồng thời, tôi muốn mở rộng bộ test set từ 10 câu hỏi lên 50–100 câu hỏi thông qua kỹ thuật sinh câu hỏi tự động (LLM Testset Generation) dựa trên cây phân loại chủ đề của Crossref.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngô Thế Việt  
**Ngày xác nhận:** 2026-09-26  
