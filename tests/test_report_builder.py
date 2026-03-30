"""Tests for PDF report builder."""
import pytest
from utils.report_builder import ReportPDF, _sanitize


def test_sanitize_unicode():
    assert _sanitize("test\u2014value") == "test-value"
    assert _sanitize("hello\u2019s") == "hello's"
    assert _sanitize("\u201cquoted\u201d") == '"quoted"'


def test_create_report_pdf():
    pdf = ReportPDF(title="Test Report", user_name="Test User")
    assert pdf.report_title == "Test Report"
    assert pdf.user_name == "Test User"


def test_add_title_page():
    pdf = ReportPDF(title="Test", user_name="User")
    pdf.add_title_page(date_range="Jan - Dec 2024")
    assert pdf.page_no() == 1


def test_add_section_header():
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_section_header("Summary")
    # Should not raise


def test_add_summary_box():
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_summary_box({"Income": "$5,000", "Expenses": "$3,000"})
    # Should not raise


def test_add_stat_line():
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_stat_line("Total:", "$1,000")
    # Should not raise


def test_get_bytes():
    pdf = ReportPDF(title="Test", user_name="User")
    pdf.add_title_page(date_range="2024")
    pdf.add_page()
    pdf.add_section_header("Test Section")
    pdf.add_stat_line("Key:", "Value")
    result = pdf.get_bytes()
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:4] == b"%PDF"
