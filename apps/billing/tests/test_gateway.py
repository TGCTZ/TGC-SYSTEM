"""GePG gateway helpers and XML parsing (no network)."""

from decimal import Decimal

from apps.billing.gateways import gepg


def test_format_amount():
    assert gepg.format_amount(Decimal("1234.5")) == "1234.50"
    assert gepg.format_amount(1000) == "1000.00"


def test_escape_xml():
    assert gepg.escape_xml("a&b<c>") == "a&amp;b&lt;c&gt;"
    assert gepg.escape_xml(None) == ""


def test_normalize_msisdn():
    assert gepg.normalize_msisdn("0712345678") == "255712345678"
    assert gepg.normalize_msisdn("712345678") == "255712345678"
    assert gepg.normalize_msisdn("255712345678") == "255712345678"
    assert gepg.normalize_msisdn("") == ""


def test_parse_datetime_variants():
    dt = gepg.parse_datetime("2026-08-28T10:00:00")
    assert (dt.year, dt.month, dt.day, dt.hour) == (2026, 8, 28, 10)
    assert dt.tzinfo is not None  # aware
    assert gepg.parse_datetime("2026-08-28T10:00:00:920").microsecond == 920000


def test_parse_payment_notification():
    xml = (
        "<Gepg><pmtSpNtfReq><PmtHdr><ReqId>R</ReqId><GrpBillId>B1</GrpBillId>"
        "<SpGrpCode>SP</SpGrpCode><CustCntrNum>255700000000</CustCntrNum><EntryCnt>1</EntryCnt></PmtHdr>"
        "<PmtDtls><PmtTrxDtl><BillId>B1</BillId><TrxId>T1</TrxId><PaidAmt>100.00</PaidAmt>"
        "<TrxDtTm>2026-08-28T10:00:00</TrxDtTm></PmtTrxDtl></PmtDtls></pmtSpNtfReq></Gepg>"
    )
    header, txns = gepg.parse_payment_notification(xml)
    assert header["grp_bill_id"] == "B1"
    assert txns[0]["trx_id"] == "T1"
    assert txns[0]["paid_amount"] == Decimal("100.00")


def test_parse_bill_response_sync():
    xml = (
        "<Gepg><billSubRes><BillDtls><BillDtl><BillCntrNum>994400000123</BillCntrNum>"
        "<BillStsCode>7101</BillStsCode></BillDtl></BillDtls></billSubRes></Gepg>"
    )
    result = gepg._parse_bill_response(xml)
    assert result["is_sync"] and result["control_number"] == "994400000123"


def test_parse_bill_response_async_ack():
    xml = "<Gepg><billSubReqAck><AckStsCode>7101</AckStsCode><AckStsDesc>ok</AckStsDesc></billSubReqAck></Gepg>"
    result = gepg._parse_bill_response(xml)
    assert result["success"] and result["control_number"] == "PENDING"


def test_parse_bill_response_error():
    xml = "<Gepg><billSubReqAck><AckStsCode>7102</AckStsCode><AckStsDesc>bad</AckStsDesc></billSubReqAck></Gepg>"
    result = gepg._parse_bill_response(xml)
    assert not result["success"]


def test_build_payment_ack_contains_code():
    ack = gepg.build_payment_ack("REQ", "7101")
    assert "7101" in ack and "pmtSpNtfReqAck" in ack


def test_sign_if_enabled_passthrough_when_off(settings):
    settings.GEPG_USE_DIGITAL_SIGNATURE = False
    xml = "<Gepg><x/><signature>SignatureGoesHere</signature></Gepg>"
    assert gepg.sign_if_enabled(xml) == xml
