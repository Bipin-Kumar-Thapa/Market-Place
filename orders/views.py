from django.shortcuts import render
from .forms import OrderForm
from . models import Order, Payment, OrderProduct
from django.shortcuts import redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from store.forms import ProductForm
from store.models import Product
from django.db.models import F
from carts.models import CartItem
import datetime
from django.urls import reverse
import base64, hmac, hashlib, uuid, json
from django.conf import settings

# Email verification

from django.template.loader import render_to_string
from django.core.mail import EmailMessage

# Create your views here.
def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order':order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)

        else:
            return redirect('checkout')
    
def _abs(request, name, *args, **kwargs):
    return request.build_absolute_uri(reverse(name, args=args, kwargs=kwargs))

def _order_amount(order):
    if hasattr(order, "order_total") and order.order_total:
        return int(round(float(order.order_total)))
    return int(sum(op.product_price * op.quantity for op in orderproduct_set.all()))

def _make_signature(total_amount: int, transaction_uuid: str) -> str:
    msg = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={settings.ESEWA_PRODUCT_CODE}"
    mac = hmac.new(
        settings.ESEWA_SECRET_KEY.encode("utf-8"),
        msg = msg.encode("utf-8"),
        digestmod = hashlib.sha256
    ).digest()
    return base64.b64encode(mac).decode("utf-8")

@login_required
def esewa_start(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total_amount = int(round(float(order.order_total or 0)))
    tax = int(round(float(order.tax or 0)))
    amount = total_amount - tax

    if amount < 0:
        amount = total_amount
    
    txn_uuid = f"{order.order_number or order.id} - {uuid.uuid4().hex[:8]}"

    form = {
        "amount": int(amount),
        "tax_amount": int(tax),
        "total_amount": int(total_amount),
        "transcation_uuid": txn_uuid,
        "product_code": settings.ESEWA_PRODUCT_CODE,
        "product_service_charge": 0,
        "product_delivery_charge": 0,
        "success_url": _abs(request,"esewa_return", order_id=order.id),
        "failure_url": _abs(request, "esewa_return", order_id=order.id),
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature": _make_signature(total_amount, txn_uuid),
    }
    return render(request, "orders/payments/esewa_redirect.html",{
        "ESEWA_FORM_URL": settings.ESEWA_FORM_URL,
        "form": form,
    })

@login_required
def esewa_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    encoded = request.GET.get("data") or request.POST.get("data") \
            or request.GET.get("response") or request.POST.get("response")
    payload, status, txn_code = {}, "", ""
    if encoded:
        try:
            payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
            status = str(payload.get("status","")).upper()
            txn_code = payload.get("transcation_code","")
        except Exception:
            pass
    
    if status == "COMPLETE":
        amount_paid = _order_amount(order)
        payment, _ = Payment.objects.get_or_create(
            user=order.user,
            payment_id=txn_code or f"esewa-{order.id}",
            defaults={
                "payment_method": "eSewa",
                "amount_paid": str(amount_paid),
                "status": "COMPLETED",
            }
        )

        if not order.orderproduct_set.exists() and CartItem:
            cart_items = CartItem.objects.filter(user=order.user).select_related("product")
            for item in cart_items:
                order_product = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=order.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    orderd=True,
                )

                if hasattr(item, "variations"):
                    order_product.variations.set(item.variations.all())
                
                Product.objects.filter(pk=item.product_id).update(stock=F("stock")-item.quantity)
            
            cart_items.delete()
        else:
            for order_product in order.orderproduct_set.all():
                if order_product.payment_id != payment.id:
                    order_product.payment = payment
                if not order_product.ordered:
                    order_product.ordered = True
                order_product.save(update_fields=["payment","ordered"])

        items = order.orderproduct_set.select_related("product").prefetch_related("variations")
        amount_paid = _order_amount(order)

        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_recevired_email.html', {
            'user': request.user,
            'order': order,
            'items': items,
            'amount_paid': amount_paid,
        })
        to_email = request.user.email
        try:
            send_email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            send_email.send()
        except Exception:
            messages.warning(request, "Order received, but we couldnot send the email. Contact admin.")
        
        order.payment = payment
        order.is_ordered = True
        if hasattr(order, "status"):
            order.status = "Accepted"
        order.save()

        url = reverse("order_completed")
        return redirect(f"{url}?order_numbers={order.order_number}&payment_id={payment.payment_id}")
    
    messages.error(request, "eSewa (TEST): Payment was not completed.")
    return redirect("home")


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
    except Order.DoesNotExist:
        return redirect('home')
    
    payment = order.payment

    if payment is None:
        qs = Payment.objects.filter(payment_id=transID, user=order.user).order_by('-created_at')
        payment = qs.first()
        if payment:
            order.payment = payment
            order.save(update_fields=['payment'])
        else:
            qs_any = Payment.objects.filter(payment_id=transID).order_by('-created_at')
            payment = qs_any.first()
            if payment:
                order.payment = payment
                order.save(update_fields=['payment'])
            else:
                return redirect('home')
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)