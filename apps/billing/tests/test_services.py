"""Bill generation and GePG payment-notification handling."""

from decimal import Decimal

import pytest

from apps.billing import services as billing_services
from apps.billing.enums import BillStatus
from apps.billing.models import Payment
from apps.billing.services import (
    generate_bill_for_order,
    handle_bill_response_callback,
    process_payment_notification,
)
from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.core.tests.factories import StoneTypeFactory
from apps.orders.services import create_order
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def no_gepg(monkeypatch):
    """Stub the GePG submission so bill generation stays offline."""

    def _fake(bill, customer, username):
        return {
            "success": True, "control_number": "994400000123",
            "status_code": "7101", "status_desc": "ok",
            "is_sync": True, "raw_response": "<x/>",
        }

    monkeypatch.setattr(billing_services, "submit_bill", _fake)


def _order(user, stone_type, weight="2.0"):
    return create_order(
        customer=CustomerFactory(),
        stones=[{"stone_type": stone_type, "weight": Decimal(weight)}],
        user=user,
    )


def _payment_xml(bill_number, amount, trx_id):
    return f"""<Gepg><pmtSpNtfReq>
      <PmtHdr><ReqId>REQ</ReqId><GrpBillId>{bill_number}</GrpBillId><SpGrpCode>SP</SpGrpCode><CustCntrNum>255700000000</CustCntrNum><EntryCnt>1</EntryCnt></PmtHdr>
      <PmtDtls><PmtTrxDtl>
        <SpCode>SP</SpCode><BillId>{bill_number}</BillId><BillCtrNum>994400000123</BillCtrNum>
        <PspCode>PSP</PspCode><PspName>M-Pesa</PspName><TrxId>{trx_id}</TrxId><PayRefId>REF</PayRefId>
        <BillAmt>{amount}</BillAmt><PaidAmt>{amount}</PaidAmt><BillPayOpt>3</BillPayOpt><Ccy>TZS</Ccy>
        <CollAccNum>ACC</CollAccNum><TrxDtTm>2026-08-28T10:00:00</TrxDtTm><UsdPayChnl>USSD</UsdPayChnl>
        <PyrCellNum>255700000000</PyrCellNum><PyrName>P</PyrName><PyrEmail></PyrEmail>
      </PmtTrxDtl></PmtDtls>
    </pmtSpNtfReq><signature>x</signature></Gepg>"""


def test_generate_bill_snapshots_and_bills_stones(user, priced_stone_type, no_gepg):
    order = _order(user, priced_stone_type)
    bill = generate_bill_for_order(order, user=user)
    assert bill.bill_number.startswith("BILL-")
    item = bill.items.first()
    assert item.amount == item.unit_price * item.weight
    assert bill.total_amount == item.amount
    assert order.stones.first().status == StoneStatus.BILLED
    assert bill.control_number == "994400000123"


def test_generate_bill_twice_raises(user, priced_stone_type, no_gepg):
    order = _order(user, priced_stone_type)
    generate_bill_for_order(order, user=user)
    with pytest.raises(ServiceError):
        generate_bill_for_order(order, user=user)


def test_generate_bill_without_price_raises(user, no_gepg):
    order = create_order(
        customer=CustomerFactory(),
        stones=[{"stone_type": StoneTypeFactory(), "weight": Decimal("1.0")}],
        user=user,
    )
    with pytest.raises(ServiceError):
        generate_bill_for_order(order, user=user)


def test_payment_notification_settles_bill(user, priced_stone_type, no_gepg):
    order = _order(user, priced_stone_type)
    bill = generate_bill_for_order(order, user=user)
    ack = process_payment_notification(_payment_xml(bill.bill_number, bill.total_amount, "TRX-1"))
    assert "7101" in ack
    bill.refresh_from_db()
    assert bill.status == BillStatus.PAID
    assert order.stones.first().status == StoneStatus.PAID
    assert Payment.objects.filter(trx_id="TRX-1").exists()


def test_payment_notification_dedupes(user, priced_stone_type, no_gepg):
    order = _order(user, priced_stone_type)
    bill = generate_bill_for_order(order, user=user)
    xml = _payment_xml(bill.bill_number, bill.total_amount, "TRX-DUP")
    process_payment_notification(xml)
    process_payment_notification(xml)
    assert Payment.objects.filter(trx_id="TRX-DUP").count() == 1


def test_payment_notification_unknown_bill_errors():
    ack = process_payment_notification(_payment_xml("NOPE", Decimal("100"), "TRX-X"))
    assert "7102" in ack


def test_bill_response_callback_sets_control_number(user, priced_stone_type, no_gepg):
    order = _order(user, priced_stone_type)
    bill = generate_bill_for_order(order, user=user)
    xml = (
        f"<Gepg><billSubRes><BillHdr><ReqId>R</ReqId><ResId>RES1</ResId></BillHdr>"
        f"<BillDtls><BillDtl><BillId>{bill.bill_number}</BillId>"
        f"<BillCntrNum>994400000999</BillCntrNum><BillStsCode>7101</BillStsCode>"
        f"<BillStsDesc>ok</BillStsDesc></BillDtl></BillDtls></billSubRes>"
        f"<signature>x</signature></Gepg>"
    )
    ack = handle_bill_response_callback(xml)
    bill.refresh_from_db()
    assert bill.control_number == "994400000999"
    assert "7101" in ack
