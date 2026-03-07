from __future__ import annotations

from datetime import date
from pathlib import Path
from random import Random
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

CLIENT_PROFILES = [
    ("北辰 Northwind", "northwind"),
    ("凌峰 Apex Labs", "apex_labs"),
    ("蓝河 Blue River", "blue_river"),
    ("港点 Harbor Point", "harbor_point"),
    ("流明 Lumen Works", "lumen_works"),
    ("星轨 Orbit Health", "orbit_health"),
    ("顶点 Vertex Union", "vertex_union"),
    ("银松 Silver Pine", "silver_pine"),
]

CATEGORY_PROFILES = [
    ("合同 Contract", "contract"),
    ("发票 Invoice", "invoice"),
    ("报告 Report", "report"),
    ("备忘 Memo", "memo"),
    ("证据 Evidence", "evidence"),
    ("复核 Review", "review"),
]

REGION_PROFILES = [
    ("华东 East", "east"),
    ("华西 West", "west"),
    ("华北 North", "north"),
    ("华南 South", "south"),
]

STATUS_PROFILES = [
    "已批准 Approved",
    "待处理 Pending",
    "已归档 Archived",
    "审核中 In Review",
]

KEYWORD_PROFILES = [
    ("合规 Compliance", "compliance"),
    ("试点 Pilot", "pilot"),
    ("续签 Renewal", "renewal"),
    ("审计 Audit", "audit"),
    ("入驻 Onboarding", "onboarding"),
    ("扩展 Expansion", "expansion"),
]

OWNER_PROFILES = [
    "法务 Legal",
    "审计 Audit",
    "交付 Delivery",
    "运营 Operations",
    "采购 Procurement",
    "质量 Quality",
]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, title: str, doc_id: str) -> None:
    _write_text(
        path,
        '{\n'
        f'  "document_id": "{doc_id}",\n'
        f'  "title": "{title}",\n'
        '  "generated_by": "fileclassifier"\n'
        '}\n',
    )


def _write_xml(path: Path, title: str, doc_id: str) -> None:
    _write_text(
        path,
        f'<?xml version="1.0" encoding="UTF-8"?>\n<record id="{doc_id}"><title>{title}</title></record>\n',
    )


def _write_csv(path: Path, title: str, doc_id: str) -> None:
    _write_text(path, f"document_id,title\n{doc_id},{title}\n")


def _write_markdown(path: Path, title: str, doc_id: str) -> None:
    _write_text(path, f"# {title}\n\n- document_id: {doc_id}\n- generated_by: fileclassifier\n")


def _write_pdf(path: Path, title: str, doc_id: str) -> None:
    content = f"{doc_id} - {title}"
    escaped = content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        f"4 0 obj << /Length {len(escaped) + 33} >> stream\n"
        f"BT /F1 12 Tf 36 90 Td ({escaped}) Tj ET\n"
        "endstream endobj\n"
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        "xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n"
        "0000000117 00000 n \n0000000244 00000 n \n0000000360 00000 n \n"
        "trailer << /Root 1 0 R /Size 6 >>\nstartxref\n430\n%%EOF\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf.encode("utf-8"))


def _write_docx(path: Path, title: str, doc_id: str) -> None:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        f"<w:p><w:r><w:t>{doc_id}</w:t></w:r></w:p>"
        f"<w:p><w:r><w:t>{title}</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)


def _write_sample_file(path: Path, title: str, doc_id: str) -> None:
    suffix = path.suffix.casefold()
    if suffix == ".txt":
        _write_text(path, f"{doc_id}\n{title}\n")
    elif suffix == ".csv":
        _write_csv(path, title, doc_id)
    elif suffix == ".json":
        _write_json(path, title, doc_id)
    elif suffix == ".xml":
        _write_xml(path, title, doc_id)
    elif suffix == ".md":
        _write_markdown(path, title, doc_id)
    elif suffix == ".pdf":
        _write_pdf(path, title, doc_id)
    elif suffix == ".docx":
        _write_docx(path, title, doc_id)
    else:
        _write_text(path, f"{doc_id} | {title}\n")


def _build_records(record_total: int) -> pd.DataFrame:
    random = Random(20260307)

    records: list[dict[str, object]] = []
    for index in range(1, record_total + 1):
        year = 2024 + (index % 3)
        doc_id = f"FC-{year}-{index:04d}"
        project_code = f"PRJ-{year % 100}{(index * 7) % 97:02d}-{index:03d}"
        client, client_slug = CLIENT_PROFILES[index % len(CLIENT_PROFILES)]
        category, category_slug = CATEGORY_PROFILES[index % len(CATEGORY_PROFILES)]
        region, region_slug = REGION_PROFILES[index % len(REGION_PROFILES)]
        status = STATUS_PROFILES[(index * 2) % len(STATUS_PROFILES)]
        keyword, keyword_slug = KEYWORD_PROFILES[(index * 3) % len(KEYWORD_PROFILES)]
        amount = 1200 + ((index * 137) % 8800)
        day = ((index * 3) % 27) + 1
        month = (index % 12) + 1
        record_date = date(year, month, day)
        title = f"{client} {category} {keyword} 套件 Package {index}"
        if index % 17 == 0:
            title = title.replace("Compliance", "Complaince")

        records.append(
            {
                "doc_id": doc_id,
                "project_code": project_code,
                "client_name": client,
                "category": category,
                "region": region,
                "status": status,
                "keyword": keyword,
                "amount": amount,
                "record_date": record_date.isoformat(),
                "title": title,
                "owner": f"{OWNER_PROFILES[random.randint(0, len(OWNER_PROFILES) - 1)]}-{random.randint(1, 6)}",
                "client_slug": client_slug,
                "category_slug": category_slug,
                "region_slug": region_slug,
                "keyword_slug": keyword_slug,
            }
        )

    return pd.DataFrame(records)


def generate_mock_dataset(base_dir: Path, record_total: int = 240) -> dict[str, Path]:
    data_dir = Path(base_dir)
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    excel_path = data_dir / "sample_records.xlsx"

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataframe = _build_records(record_total)
    export_dataframe = dataframe.drop(
        columns=["client_slug", "category_slug", "region_slug", "keyword_slug"],
        errors="ignore",
    )
    extensions = [".txt", ".pdf", ".docx", ".csv", ".json", ".xml", ".md"]

    for _, row in dataframe.iterrows():
        doc_id = str(row["doc_id"])
        title = str(row["title"])
        region = str(row["region_slug"])
        year = doc_id.split("-")[1]
        extension = extensions[int(doc_id.split("-")[-1]) % len(extensions)]
        filename = f"{doc_id}_{row['category_slug']}_{row['keyword_slug']}{extension}"
        sequence_number = int(doc_id.split("-")[-1])

        if sequence_number <= 140:
            file_path = input_dir / filename
            _write_sample_file(file_path, title, doc_id)
        elif sequence_number <= 180:
            file_path = input_dir / "archive" / region / year / filename
            _write_sample_file(file_path, title, doc_id)
        elif sequence_number <= 210:
            continue
        elif sequence_number <= 230:
            primary = input_dir / filename
            secondary = input_dir / "conflicts" / f"{doc_id}_revision_b{extension}"
            _write_sample_file(primary, title, doc_id)
            _write_sample_file(secondary, f"{title} 修订 Revision B", doc_id)
        else:
            alt_name = input_dir / f"{doc_id}_{row['client_slug']}{extension}"
            _write_sample_file(alt_name, title, doc_id)

    for extra_index in range(1, 21):
        extension = extensions[extra_index % len(extensions)]
        extra_path = input_dir / "unindexed" / f"misc_note_{extra_index:02d}{extension}"
        _write_sample_file(
            extra_path,
            f"未索引 Unindexed supporting file {extra_index}",
            f"MISC-{extra_index:03d}",
        )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        export_dataframe.to_excel(writer, sheet_name="records", index=False)
        export_dataframe[export_dataframe["amount"] >= 8000].to_excel(
            writer,
            sheet_name="priority_view",
            index=False,
        )

    return {
        "data_dir": data_dir,
        "excel_path": excel_path,
        "input_dir": input_dir,
        "output_dir": output_dir,
    }
