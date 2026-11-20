"""Testes TDD para geração da versão text/plain nos builders de e-mail (Fase 3)."""

from src.domain.events import OrderTransitionEvent, CartTransitionEvent
from src.services.email_builders.concrete_builders import (
    PaymentConfirmedBuilder,
    PaymentIncentiveBuilder,
    ShippingTrackerBuilder,
    Coupon4CartBuilder,
)


def _sample_order_event(new_stg: int = 1) -> OrderTransitionEvent:
    return OrderTransitionEvent(
        order_id="ord_plain_1",
        order_number="10948",
        new_stg=new_stg,
        customer_data={"name": "Lucas Duarte", "email": "lucas@exemplo.com"},
        order_data={
            "value_total": 250.0,
            "value_shipment": 23.5,
            "checkout_url": "https://elevemeloja.com.br/checkout/pay/10948",
            "track_code": "BR987654321BR",
            "track_url": "https://elevemeloja.com.br/rastreamento/10948",
            "pix": {"data": [{"pix_qr_code": "00020126580014BR.GOV.BCB.PIX"}]},
            "items": {
                "data": [
                    {"name": "Palmilha Eleveme Confort", "quantity": 1, "price": 250.0},
                ]
            },
        },
    )


def test_html_to_plain_text_strips_styles_scripts_and_preserves_links():
    builder = PaymentConfirmedBuilder()
    sample_html = """
    <!doctype html>
    <html>
      <head>
        <title>Ignorar Titulo</title>
        <style>.x { color: red; }</style>
        <!--[if mso]><table><tr><td>MSO ONLY</td></tr></table><![endif]-->
      </head>
      <body>
        <script>alert('nao incluir');</script>
        <div>Olá, <strong>Lucas</strong>!</div>
        <table>
          <tr><td>Produto A</td><td>1</td><td>R$ 150.00</td></tr>
        </table>
        <a href="https://elevemeloja.com.br/pedido/123">Acompanhar pedido</a>
      </body>
    </html>
    """
    plain = builder.html_to_plain_text(sample_html)

    assert "color: red" not in plain
    assert "alert(" not in plain
    assert "MSO ONLY" not in plain
    assert "Olá, Lucas!" in plain
    assert "Produto A" in plain
    assert "R$ 150.00" in plain
    assert "Acompanhar pedido (https://elevemeloja.com.br/pedido/123)" in plain


def test_build_with_plain_text_preserves_order_details_and_company_footer():
    event = _sample_order_event(new_stg=1)
    builder = PaymentConfirmedBuilder()

    subject, html_body, plain_text = builder.build_with_plain_text(event)

    assert subject == "Eleveme: Pagamento confirmado para o pedido #10948"
    assert "<html" in html_body.lower()
    assert "<div" not in plain_text
    assert "<style" not in plain_text
    assert "Lucas" in plain_text
    assert "10948" in plain_text
    assert "Eleveme" in plain_text


def test_build_with_plain_text_includes_pix_and_tracking_and_cart_recovery():
    # PIX pendente
    pending_event = _sample_order_event(new_stg=2)
    _, _, pending_plain = PaymentIncentiveBuilder().build_with_plain_text(pending_event)
    assert "00020126580014BR.GOV.BCB.PIX" in pending_plain
    assert "Palmilha Eleveme Confort" in pending_plain
    assert "R$ 250.00" in pending_plain
    assert "55.453.284/0001-63" in pending_plain

    # Pedido a caminho (rastreio)
    shipping_event = _sample_order_event(new_stg=3)
    _, _, shipping_plain = ShippingTrackerBuilder().build_with_plain_text(shipping_event)
    assert "BR987654321BR" in shipping_plain
    assert "https://elevemeloja.com.br/rastreamento/10948" in shipping_plain

    # Carrinho abandonado
    cart_event = CartTransitionEvent(
        cart_id="cart_plain_4",
        new_stc=15,
        customer_data={"name": "Marina Silva", "email": "marina@exemplo.com"},
        cart_data={
            "value_total": 180.0,
            "recovery_url": "https://elevemeloja.com.br/recover/abc",
            "items": {"data": [{"name": "Tenis Eleveme", "quantity": 1, "price": 180.0}]},
        },
    )
    _, _, cart_plain = Coupon4CartBuilder().build_with_plain_text(cart_event)
    assert "Marina" in cart_plain
    assert "ELEVEME10" in cart_plain
    assert "https://elevemeloja.com.br/recover/abc" in cart_plain
