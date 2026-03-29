import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from django.utils import timezone

API_KEY = 'avs-wallet-api-key-2024'  # move to settings/env in production


def _api_auth(request):
    return request.headers.get('X-API-Key') == API_KEY


@csrf_exempt
@require_POST
def wallet_transaction_api(request):
    """
    External API to push wallet transactions.
    For duplicate transaction_id: only the latest entry is considered —
    the wallet balance is adjusted by reversing the previous entry and applying the new one.

    Required JSON fields:
        transaction_id, avs_customer_id, avs_customer_name, mobile,
        amount, type (Credit/Debit), transaction_date (ISO 8601),
        transaction_for (optional), transaction_by (optional)
    """
    if not _api_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    transaction_id   = data.get('transaction_id', '').strip()
    avs_customer_id  = data.get('avs_customer_id', '').strip()
    avs_customer_name = data.get('avs_customer_name', '').strip()
    mobile           = data.get('mobile', '').strip()
    txn_type         = data.get('type', '').strip()
    transaction_for  = data.get('transaction_for', '')
    transaction_by   = data.get('transaction_by', 'API')
    raw_date         = data.get('transaction_date', '')

    if not all([transaction_id, avs_customer_id, txn_type]):
        return JsonResponse({'error': 'transaction_id, avs_customer_id and type are required'}, status=400)

    if txn_type not in ('Credit', 'Debit'):
        return JsonResponse({'error': 'type must be Credit or Debit'}, status=400)

    try:
        amount = Decimal(str(data.get('amount', '')))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    transaction_date = parse_datetime(raw_date) if raw_date else timezone.now()
    if transaction_date is None:
        transaction_date = timezone.now()

    from management.models import Wallet, WalletTransaction

    wallet = Wallet.objects.filter(customer_id=avs_customer_id, wallet_type='AVS').first()
    if not wallet:
        # Auto-create wallet for new AVS customer
        wallet = Wallet.objects.create(
            wallet_type='AVS',
            customer_name=avs_customer_name,
            customer_id=avs_customer_id,
            customer_mobile=mobile,
            created_by='API',
        )


    wallet.modified_by = transaction_by
    wallet.save()

    WalletTransaction.objects.create(
        transaction_id=transaction_id,
        avs_customer_name=avs_customer_name or wallet.customer_name,
        avs_customer_id=avs_customer_id,
        avs_customer_mobile=mobile or wallet.customer_mobile,
        transaction_type=txn_type,
        amount=amount,
        reference_order=None,
        transaction_date=transaction_date,
        transaction_for=transaction_for,
        transaction_by=transaction_by,
    )

    return JsonResponse({
        'success': True,
        'wallet_id': wallet.wallet_id,
        'new_balance': str(wallet.wallet_amount),
    })
