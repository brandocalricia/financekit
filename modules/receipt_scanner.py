import streamlit as st
import pandas as pd
import io
import plotly.express as px
from utils.pdf_parser import parse_pdf, guess_category
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout
from utils.formatting import format_currency, get_currency_symbol

DATA_FILE = "receipts.json"


def _load():
    return load_json(DATA_FILE, default=[])


def _save(data):
    save_json(DATA_FILE, data)


def _parse_image(file_bytes: bytes, filename: str) -> dict:
    """Parse a JPG/PNG receipt image using OCR."""
    text = ""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
    except Exception:
        pass

    if not text.strip():
        return {
            "filename": filename,
            "date": "",
            "vendor": "Could not extract text (install Tesseract for OCR)",
            "total": "",
            "category": "Unknown",
            "raw_text": "",
        }

    from utils.pdf_parser import _extract_date, _extract_total, _extract_vendor
    vendor = _extract_vendor(text)
    return {
        "filename": filename,
        "date": _extract_date(text),
        "vendor": vendor,
        "total": _extract_total(text),
        "category": guess_category(vendor),
        "raw_text": text[:2000],
    }


def render():
    render_module_header("🧾", "Receipt & Invoice Scanner",
                         "Upload PDFs or photos. Extract date, vendor, total, and category — then export to Excel or CSV.")

    ocr_available = False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_available = True
    except Exception:
        pass

    if not ocr_available:
        st.caption(
            "ℹ️ Tesseract OCR not installed. Image-based PDFs and photos won't extract text. "
            "Text-based PDFs work fine. Install Tesseract to enable full OCR support."
        )

    if "receipt_data" not in st.session_state:
        st.session_state.receipt_data = _load()

    # ── Monthly Summary Chart ─────────────────────────────────────────────
    if st.session_state.receipt_data:
        receipts_with_totals = []
        for r in st.session_state.receipt_data:
            try:
                total_str = str(r.get("total", "")).replace("$", "").replace(",", "").strip()
                total_val = float(total_str)
                date_str = r.get("date", "")
                if date_str and total_val > 0:
                    receipts_with_totals.append({"date": date_str, "total": total_val, "vendor": r.get("vendor", "")})
            except (ValueError, TypeError):
                pass

        if len(receipts_with_totals) >= 3:
            rdf = pd.DataFrame(receipts_with_totals)
            try:
                rdf["date"] = pd.to_datetime(rdf["date"], errors="coerce")
                rdf = rdf.dropna(subset=["date"])
                rdf["month"] = rdf["date"].dt.to_period("M").astype(str)
                monthly = rdf.groupby("month")["total"].sum().reset_index()
                monthly.columns = ["Month", "Total ($)"]
                fig = px.bar(
                    monthly, x="Month", y="Total ($)",
                    title="Monthly Receipt Spending",
                    color_discrete_sequence=["#6366f1"],
                    text="Total ($)",
                )
                fig.update_traces(texttemplate=f"{get_currency_symbol()}%{{text:,.0f}}", textposition="outside")
                apply_layout(fig, height=280)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

    # ── Upload Section ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Upload Receipts")

    tab_upload, tab_camera = st.tabs(["📁 Upload Files", "📷 Camera"])

    with tab_upload:
        uploaded_files = st.file_uploader(
            "Upload receipt files (PDF, JPG, or PNG)",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Drag and drop multiple files. PDFs extract text directly; images use OCR.",
        )

        if uploaded_files and st.button("🔍 Scan & Add Receipts", type="primary"):
            with st.spinner("Scanning receipts..."):
                progress = st.progress(0, text="Starting scan...")
                new_count = 0
                for i, file in enumerate(uploaded_files):
                    try:
                        file_bytes = file.read()
                        ext = file.name.lower().split(".")[-1]
                        if ext == "pdf":
                            result = parse_pdf(file_bytes, file.name)
                        else:
                            result = _parse_image(file_bytes, file.name)
                        st.session_state.receipt_data.append(result)
                        new_count += 1
                    except Exception as e:
                        st.session_state.receipt_data.append({
                            "filename": file.name,
                            "date": "", "vendor": f"Error: {e}",
                            "total": "", "category": "", "raw_text": "",
                        })
                    progress.progress((i + 1) / len(uploaded_files),
                                      text=f"Scanned {i + 1} of {len(uploaded_files)}...")

                _save(st.session_state.receipt_data)
                progress.empty()
            st.toast(f"Added {new_count} receipt(s)! Total: {len(st.session_state.receipt_data)}", icon="✅")
            st.rerun()

    with tab_camera:
        if ocr_available:
            st.markdown("**Snap a photo of your receipt:**")
            camera_image = st.camera_input("Take a photo", key="receipt_camera")
            if camera_image and st.button("📷 Scan Photo", type="primary", key="scan_camera"):
                with st.spinner("Scanning photo..."):
                    try:
                        result = _parse_image(camera_image.read(), "camera_receipt.jpg")
                        st.session_state.receipt_data.append(result)
                        _save(st.session_state.receipt_data)
                        st.toast("Receipt scanned!", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not process photo: {e}")
        else:
            st.info("Install Tesseract OCR to enable camera scanning. See the README for instructions.")

    if not st.session_state.receipt_data:
        from utils.ui_helpers import render_empty_state
        render_empty_state("🧾", "No receipts yet",
                           "Upload PDF or image files above to scan and organize your receipts.")
        return

    # ── Stats ─────────────────────────────────────────────────────────────
    st.markdown("---")
    sc1, sc2 = st.columns(2)
    sc1.metric("Total Receipts Saved", len(st.session_state.receipt_data))
    totals_parsed = []
    for r in st.session_state.receipt_data:
        try:
            totals_parsed.append(float(str(r.get("total", "")).replace("$", "").replace(",", "")))
        except (ValueError, TypeError):
            pass
    if totals_parsed:
        sc2.metric("Total Value Scanned", format_currency(sum(totals_parsed)))

    # ── Editable Table ────────────────────────────────────────────────────
    st.markdown("### All Receipts")
    st.caption("Review and correct fields. Click 'Save Changes' to persist edits.")

    display_data = []
    for r in st.session_state.receipt_data:
        display_data.append({
            "Filename": r.get("filename", ""),
            "Date": r.get("date", ""),
            "Vendor": r.get("vendor", ""),
            "Total": r.get("total", ""),
            "Category": r.get("category", ""),
        })

    edit_df = pd.DataFrame(display_data)
    edited = st.data_editor(
        edit_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Category": st.column_config.SelectboxColumn(
                options=["Groceries", "Dining", "Transport", "Utilities", "Shopping",
                         "Health", "Entertainment", "Subscription", "Other"],
            ),
        },
        hide_index=True,
    )

    ac1, ac2, ac3 = st.columns([1, 1, 3])
    with ac1:
        if st.button("💾 Save Changes", use_container_width=True):
            for i, row in edited.iterrows():
                if i < len(st.session_state.receipt_data):
                    st.session_state.receipt_data[i]["date"] = row["Date"]
                    st.session_state.receipt_data[i]["vendor"] = row["Vendor"]
                    st.session_state.receipt_data[i]["total"] = row["Total"]
                    st.session_state.receipt_data[i]["category"] = row["Category"]
            _save(st.session_state.receipt_data)
            st.toast("Changes saved!", icon="✅")
    with ac2:
        if "confirm_clear_receipts" not in st.session_state:
            st.session_state.confirm_clear_receipts = False
        if not st.session_state.confirm_clear_receipts:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.confirm_clear_receipts = True
                st.rerun()
        else:
            if st.button("⚠️ Confirm Clear?", use_container_width=True, type="primary"):
                st.session_state.receipt_data = []
                _save([])
                st.session_state.confirm_clear_receipts = False
                st.rerun()

    with st.expander("🔎 View raw extracted text"):
        for r in st.session_state.receipt_data:
            st.markdown(f"**{r['filename']}**")
            st.code(r.get("raw_text", "(no text extracted)"), language=None)

    # ── Export ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Export")
    ec1, ec2 = st.columns(2)
    csv_bytes = edited.to_csv(index=False).encode("utf-8")
    ec1.download_button("⬇️ Download CSV", data=csv_bytes,
                        file_name="receipts_export.csv", mime="text/csv")
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as writer:
        edited.to_excel(writer, index=False, sheet_name="Receipts")
    ec2.download_button("⬇️ Download Excel", data=xlsx_buf.getvalue(),
                        file_name="receipts_export.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
