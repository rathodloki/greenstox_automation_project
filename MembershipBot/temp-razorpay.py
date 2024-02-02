import json
json_data = '''{
    "account_id": "acc_FUYygrFV6Msc3E",
    "contains": [
        "payment_link",
        "order",
        "payment"
    ],
    "created_at": 1706790962,
    "entity": "event",
    "event": "payment_link.paid",
    "payload": {
        "order": {
            "entity": {
                "amount": 700,
                "amount_due": 0,
                "amount_paid": 700,
                "attempts": 1,
                "created_at": 1706790965,
                "currency": "INR",
                "entity": "order",
                "id": "order_NVcLIkv0TvbOGG",
                "notes": {
                    "telegram_user_id": "635834411"
                },
                "offer_id": null,
                "receipt": "order_NVcLFAo1oBKDDR",
                "status": "paid"
            }
        },
        "payment": {
            "entity": {
                "acquirer_data": {
                    "rrn": "249727216453",
                    "upi_transaction_id": "95F9C08EF8042B93242AFD815F8AD8ED"
                },
                "amount": 700,
                "amount_refunded": 0,
                "amount_transferred": 0,
                "bank": null,
                "base_amount": 700,
                "captured": true,
                "card": null,
                "card_id": null,
                "contact": "+918070172890",
                "created_at": 1706791001,
                "currency": "INR",
                "description": "#NVcLFj7FEEzhOA",
                "email": "void@razorpay.com",
                "entity": "payment",
                "error_code": null,
                "error_description": null,
                "error_reason": null,
                "error_source": null,
                "error_step": null,
                "fee": 16,
                "fee_bearer": "platform",
                "id": "pay_NVcLwcbtje3yCH",
                "international": false,
                "invoice_id": null,
                "method": "upi",
                "notes": {
                    "telegram_user_id": "635834411"
                },
                "order_id": "order_NVcLIkv0TvbOGG",
                "refund_status": null,
                "status": "captured",
                "tax": 2,
                "upi": {
                    "vpa": "8070172891@okicici"
                },
                "vpa": "8070172891@okicici",
                "wallet": null
            }
        },
        "payment_link": {
            "entity": {
                "accept_partial": false,
                "amount": 700,
                "amount_paid": 700,
                "cancelled_at": 0,
                "created_at": 1706790962,
                "currency": "INR",
                "customer": {
                    "contact": "8070273890",
                    "email": "sds@fsd",
                    "name": "loki sinfh"
                },
                "description": "1 Day plan",
                "expire_by": 0,
                "expired_at": 0,
                "first_min_partial_amount": 0,
                "id": "plink_NVcLFj7FEEzhOA",
                "notes": {
                    "telegram_user_id": "635834411"
                },
                "notify": {
                    "email": true,
                    "sms": true,
                    "whatsapp": false
                },
                "order_id": "order_NVcLIkv0TvbOGG",
                "reference_id": "order_NVcLFAo1oBKDDR",
                "reminder_enable": false,
                "reminders": {
                    "status": "failed"
                },
                "short_url": "https://rzp.io/i/hPmfxotce5",
                "status": "paid",
                "updated_at": 1706791002,
                "upi_link": false,
                "user_id": "",
                "whatsapp_link": false
            }
        }
    }
}'''

data = json.loads(json_data)

print(data)