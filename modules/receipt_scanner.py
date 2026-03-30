import streamlit as st
import pandas as pd
import io
import plotly.express as px
from utils.pdf_parser import parse_pdf, guess_category
from utils.data_persistence import load_json, save_json
from utils.ui_helpers import render_module_header
from utils.chart_config import apply_layout
from utils.formatting import format_currency, get_currency_symbol
from utils.notifications import create_notification
from utils.i18n import t

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
            "vendor": t("rs_ocr_unavailable"),
            "total": "",
            "category": t("rs_unknown"),
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
    render_module_header("", t("rs_title"),
                         t("rs_subtitle"))

    ocr_available = False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_available = True
    except Exception:
        pass

    if not ocr_available:
        st.caption(t("rs_ocr_not_installed"))

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
                monthly.columns = [t("rs_chart_month"), t("rs_chart_total")]
                fig = px.bar(
                    monthly, x=t("rs_chart_month"), y=t("rs_chart_total"),
                    title=t("rs_monthly_spending"),
                    color_discrete_sequence=["#6366f1"],
                    text=t("rs_chart_total"),
                )
                fig.update_traces(texttemplate=f"{get_currency_symbol()}%{{text:,.0f}}", textposition="outside")
                apply_layout(fig, height=280)
                st.plotly_chart(fig, width='stretch')
            except Exception:
                pass

    # ── Upload Section (v4.9 — simplified, camera tab removed) ─────────
    st.markdown("---")
    st.markdown(f"### {t('rs_upload_receipts')}")
    st.caption(t("rs_upload_label"))

    uploaded_files = st.file_uploader(
        t("rs_upload_receipts"),
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files and st.button(t("rs_scan_add"), type="primary"):
        with st.spinner(t("rs_scanning")):
            progress = st.progress(0, text=t("rs_starting_scan"))
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
                        "date": "", "vendor": t("rs_err_scan_fail", err=str(e)),
                        "total": "", "category": "", "raw_text": "",
                    })
                progress.progress((i + 1) / len(uploaded_files),
                                  text=t("rs_scan_progress", current=i + 1, total=len(uploaded_files)))

            _save(st.session_state.receipt_data)
            progress.empty()

        # Notifications for large receipts and batch uploads
        if new_count > 1:
            total_amt = 0
            for r in st.session_state.receipt_data[-new_count:]:
                try:
                    total_amt += float(str(r.get("total", "0")).replace("$", "").replace(",", ""))
                except (ValueError, TypeError):
                    pass
            create_notification(
                "success", "receipts",
                t("rs_processed_n", n=new_count),
                t("rs_processed_detail", n=new_count, total=f"{get_currency_symbol()}{total_amt:,.2f}"),
                action_module="receipt_scanner",
                dedup_hours=1,
            )
        for r in st.session_state.receipt_data[-new_count:]:
            try:
                _total = float(str(r.get("total", "0")).replace("$", "").replace(",", ""))
                if _total > 500:
                    create_notification(
                        "info", "receipts",
                        t("rs_large_receipt", amount=f"{get_currency_symbol()}{_total:,.2f}"),
                        t("rs_large_receipt_detail", amount=f"{get_currency_symbol()}{_total:,.2f}", vendor=r.get('vendor', t("rs_unknown"))),
                        action_module="receipt_scanner",
                        dedup_hours=1,
                    )
            except (ValueError, TypeError):
                pass

        st.toast(t("rs_added", n=new_count))
        st.rerun()

    if not st.session_state.receipt_data:
        from utils.ui_helpers import render_empty_state
        render_empty_state("", t("rs_no_receipts"),
                           t("rs_no_receipts_hint"))
        return

    # ── Stats (v4.9) ────────────────────────────────────────────────────
    st.markdown("---")
    totals_parsed = []
    for r in st.session_state.receipt_data:
        try:
            totals_parsed.append(float(str(r.get("total", "")).replace("$", "").replace(",", "")))
        except (ValueError, TypeError):
            pass
    _avg_receipt = sum(totals_parsed) / len(totals_parsed) if totals_parsed else 0

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{t("rs_stat_receipts")}</div>'
            f'<div class="widget-value">{len(st.session_state.receipt_data)}</div>'
            f'<div class="widget-sub">{t("rs_stat_total_scanned")}</div></div>',
            unsafe_allow_html=True,
        )
    with sc2:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{t("rs_stat_total_value")}</div>'
            f'<div class="widget-value">{format_currency(sum(totals_parsed)) if totals_parsed else "—"}</div>'
            f'<div class="widget-sub">{t("rs_stat_with_amounts", n=len(totals_parsed))}</div></div>',
            unsafe_allow_html=True,
        )
    with sc3:
        st.markdown(
            f'<div class="dash-widget"><div class="widget-title">{t("rs_stat_avg_receipt")}</div>'
            f'<div class="widget-value">{format_currency(_avg_receipt) if _avg_receipt else "—"}</div>'
            f'<div class="widget-sub">{t("rs_stat_per_receipt")}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Editable Table ────────────────────────────────────────────────────
    st.markdown(f"### {t('rs_all_receipts')}")
    st.caption(t("rs_review_hint"))

    display_data = []
    for r in st.session_state.receipt_data:
        display_data.append({
            t("rs_filename"): r.get("filename", ""),
            t("rs_date"): r.get("date", ""),
            t("rs_vendor"): r.get("vendor", ""),
            t("rs_total"): r.get("total", ""),
            t("rs_category"): r.get("category", ""),
        })

    edit_df = pd.DataFrame(display_data)
    edited = st.data_editor(
        edit_df,
        width='stretch',
        num_rows="fixed",
        column_config={
            t("rs_category"): st.column_config.SelectboxColumn(
                options=[t("rs_cat_groceries"), t("rs_cat_dining"), t("rs_cat_transport"),
                         t("rs_cat_utilities"), t("rs_cat_shopping"), t("rs_cat_health"),
                         t("rs_cat_entertainment"), t("rs_cat_subscription"), t("rs_cat_other")],
            ),
        },
        hide_index=True,
    )

    ac1, ac2, ac3 = st.columns([1, 1, 3])
    with ac1:
        if st.button(t("rs_save_changes"), width='stretch'):
            for i, row in edited.iterrows():
                if i < len(st.session_state.receipt_data):
                    st.session_state.receipt_data[i]["date"] = row[t("rs_date")]
                    st.session_state.receipt_data[i]["vendor"] = row[t("rs_vendor")]
                    st.session_state.receipt_data[i]["total"] = row[t("rs_total")]
                    st.session_state.receipt_data[i]["category"] = row[t("rs_category")]
            _save(st.session_state.receipt_data)
            st.toast(t("rs_changes_saved"))
    with ac2:
        if "confirm_clear_receipts" not in st.session_state:
            st.session_state.confirm_clear_receipts = False
        if not st.session_state.confirm_clear_receipts:
            if st.button(t("rs_clear_all"), width='stretch'):
                st.session_state.confirm_clear_receipts = True
                st.rerun()
        else:
            if st.button(t("rs_confirm_clear"), width='stretch', type="primary"):
                st.session_state.receipt_data = []
                _save([])
                st.session_state.confirm_clear_receipts = False
                st.rerun()

    with st.expander(t("rs_view_raw_text")):
        for r in st.session_state.receipt_data:
            st.markdown(f"**{r['filename']}**")
            st.code(r.get("raw_text", t("rs_no_text_extracted")), language=None)

    # ── Export ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('rs_export')}")
    ec1, ec2 = st.columns(2)
    csv_bytes = edited.to_csv(index=False).encode("utf-8")
    ec1.download_button(t("rs_export_csv"), data=csv_bytes,
                        file_name="receipts_export.csv", mime="text/csv")
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as writer:
        edited.to_excel(writer, index=False, sheet_name=t("rs_stat_receipts"))
    ec2.download_button(t("rs_export_excel"), data=xlsx_buf.getvalue(),
                        file_name="receipts_export.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
