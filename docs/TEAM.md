# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `onedayonename`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-onedayonename-DataPipeline`

---

## # Thành viên

| STT | Họ và tên | Branch | Vai trò & Phân công công việc | Commit |
|---:|---|---|---|---|
| 1 | Gia Huy | `giahuy-ingestion` | Data Foundation: `crossref.py`, `cleaning.py`, raw data | 0c22d60 |
| 2 | Mạnh Hùng | `manhhung-observability` | Data Observability: `quality.py` (GX 1.x), `reporting.py` | 94fb267 |
| 3 | Anh Minh | `anhminh-evaluation` | Evaluation & Corruption: `testset.py`, `corruption.py`, Support | 06efb82 |
| 4 | Thế Việt | `theviet-evaluation` | Evaluation Integration: test flow | 671651c |
| 5 | Minh Tiến | `minhtien-pipeline` | Pipeline Orchestration: `phase1.py`, `corruption_flow.py` | 1a463a9 |

---

## # Báo Cáo Chi Tiết Theo Module

### 1. Data Foundation (Gia Huy)

**Branch:** `giahuy-ingestion`

**Files:**
- `src/ingestion/crossref.py` - Crossref API integration với retry và fallback offline
- `src/ingestion/cleaning.py` - Data cleaning, normalization, text_for_embedding

**Output:**
- `data/raw/crossref_response.json`
- `data/raw/crossref_records.json`
- `data/clean/papers_clean.json`
- `data/clean/papers_clean.csv`

**Commit:** `0c22d60 feat: implement Crossref ingestion and data cleaning`

---

### 2. Data Observability (Mạnh Hùng)

**Branch:** `manhhung-observability`

**Files:**
- `src/observability/quality.py` - Great Expectations 1.x Quality Gate
- `src/observability/reporting.py` - Phase1 & Corruption reports

**Features:**
- 6 expectations kiểm tra: row count, null values, uniqueness, text length
- Freshness SLA monitoring (180-day threshold)
- Markdown reports generation

**Commit:** `94fb267 feat(task2): observability`

---

### 3. Evaluation & Corruption (Anh Minh)

**Branch:** `anhminh-evaluation`

**Files:**
- `src/evaluation/testset.py` - 10 câu hỏi benchmark (summary, authors, date, categories)
- `src/ingestion/corruption.py` - 6 corruption scenarios

**Commit:** `06efb82 feat: complete evaluation testset and corruption suite by Anh Minh`

---

### 4. Pipeline Orchestration (Minh Tiến)

**Branch:** `minhtien-pipeline`

**Files:**
- `src/pipelines/phase1.py` - End-to-end baseline pipeline
- `src/pipelines/corruption_flow.py` - Corruption → Evaluate → Repair → Compare

**Features:**
- Idempotent pipeline design
- ChromaDB indexing với 3 collections
- Automatic quality gate và freshness monitoring

**Commit:** `1a463a9 feat(task2): complete pipeline orchestration by Minh Tien`

---

### 5. Evaluation Integration & Test Flow (Thế Việt)

**Branch:** `theviet-evaluation`

**Vai trò & Đóng góp:**
- Tích hợp và kiểm thử luồng Benchmark Evaluation (Test Flow) cho cả 3 trạng thái: Baseline, Corrupted, Repaired
- Đo lường và xác thực tính suy giảm (Hit Rate 100% → 60%) và phục hồi (100%) của RAG Agent
- Báo cáo cá nhân: [`report/theviet_evaluation.md`](../report/theviet_evaluation.md)

**Commit:** `06efb82 feat: complete evaluation testset and corruption suite by Anh Minh` (merged)

---

## # Kết Quả Pipeline

### Phase 1 (Baseline)
| Metric | Value |
|--------|-------|
| Retrieval Hit Rate | 100% |
| Quality Gate | PASSED (6/6 expectations) |
| Freshness | FRESH (4.2% stale ratio) |

### Corruption Flow
| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Hit Rate | 100% | 60% | 100% |
| Quality Gate | PASSED | **FAILED** | PASSED |
| Freshness | FRESH | STALE | FRESH |

---

## # Tài Liệu Tham Khảo

- `teamwork.md` - Phân công chi tiết và timeline
- `data/reports/phase1_report.md` - Baseline report
- `data/reports/corruption_report.md` - Corruption comparison report
