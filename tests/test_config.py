from app.config import api_error_message


def test_payment_required_error_is_explained():
    message = api_error_message(402, "Your prepayment credits are depleted.")

    assert "前払いクレジット" in message
    assert "Google AI Studio" in message
