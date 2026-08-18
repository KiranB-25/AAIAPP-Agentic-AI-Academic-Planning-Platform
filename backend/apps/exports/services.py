from textwrap import wrap


def _escape_pdf(value: str) -> str:
    return value.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def study_plan_pdf(plan) -> bytes:
    """Render a deliberately small, dependency-free PDF from public plan fields only."""
    lines = ["AAIAPP Study Plan", f"Plan status: {plan.get_status_display()}", "", plan.summary, ""]
    for task in plan.tasks.all():
        lines.extend([f"Week {task.week}: {task.title}", f"Objective: {task.objective}", f"Method: {task.method}", task.description, ""])
    wrapped = [piece for line in lines for piece in (wrap(line, width=88) or [""])]
    pages = [wrapped[index:index + 44] for index in range(0, len(wrapped), 44)] or [[""]]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", ""]
    page_ids, content_ids = [], []
    for _ in pages:
        page_ids.append(len(objects) + 1)
        objects.append("")
        content_ids.append(len(objects) + 1)
        objects.append("")
    font_id = len(objects) + 1
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>"
    for page_id, content_id, page_lines in zip(page_ids, content_ids, pages):
        content = "BT /F1 11 Tf 50 780 Td 15 TL " + " ".join(f"({_escape_pdf(line)}) Tj T*" for line in page_lines) + " ET"
        objects[page_id - 1] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        objects[content_id - 1] = f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}\nendstream"
    payload = "%PDF-1.4\n"
    offsets = [0]
    for number, object_data in enumerate(objects, start=1):
        offsets.append(len(payload.encode("latin-1")))
        payload += f"{number} 0 obj\n{object_data}\nendobj\n"
    xref = len(payload.encode("latin-1"))
    payload += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    payload += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return payload.encode("latin-1")
