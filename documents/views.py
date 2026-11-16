"""
Views za documents.
Inazalisha PDF kupitia documents/utils.py.
"""
import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from customers.models import Customer
from expenses.models import Expense
from inventory.models import StockLevel
from products.models import Product
from sales.models import Order, OrderItem, Payment
from staff.models import Salary
from stores.models import Store

from .models import Document
from .serializers import DocumentSerializer
from .utils import generate_pdf


# ==================================================================
# HELPERS — mahesabu ya data
# ==================================================================
def _compute_mauzo(store_id=None, start=None, end=None):
    qs = Order.objects.filter(status=Order.Status.COMPLETED)
    if store_id:
        qs = qs.filter(store_id=store_id)
    if start:
        qs = qs.filter(order_date__date__gte=start)
    if end:
        qs = qs.filter(order_date__date__lte=end)

    total_sales = qs.aggregate(s=Sum("total"))["s"] or Decimal("0")

    items = OrderItem.objects.filter(order__in=qs)
    total_cogs = sum(
        Decimal(str(it.unit_cost)) * Decimal(str(it.quantity)) for it in items
    )

    count = qs.count()
    return {
        "mauzo": float(total_sales),
        "cogs": float(total_cogs),
        "faida": float(total_sales - total_cogs),
        "orders": count,
        "wastani_kwa_order": (float(total_sales) / count if count > 0 else 0),
    }


def _compute_stoki(store_id=None):
    qs = StockLevel.objects.select_related("product", "store")
    if store_id:
        qs = qs.filter(store_id=store_id)

    products = Product.objects.all()
    if store_id:
        product_ids = StockLevel.objects.filter(
            store_id=store_id
        ).values_list("product_id", flat=True)
        products = products.filter(id__in=product_ids)

    levels = {s.product_id: s for s in qs}

    jumla_bidhaa = products.count()
    jumla_stoki = 0
    zimeisha = 0
    zinaribia = 0
    thamani = 0

    for p in products:
        level = levels.get(p.id)
        qty = float(level.quantity) if level else 0
        jumla_stoki += qty
        if qty <= 0:
            zimeisha += 1
        elif qty <= (p.low_stock_alert or 5):
            zinaribia += 1
        thamani += qty * float(p.cost_price)

    return {
        "bidhaa_zote": jumla_bidhaa,
        "stoki_jumla": jumla_stoki,
        "zimeisha": zimeisha,
        "zinaribia": zinaribia,
        "thamani": thamani,
    }


def _compute_wateja(store_id=None):
    customers = Customer.objects.all()

    orders = Order.objects.all()
    if store_id:
        orders = orders.filter(store_id=store_id)

    total_manunuzi = orders.aggregate(s=Sum("total"))["s"] or Decimal("0")

    total_deni = 0
    for o in orders:
        confirmed = (
            Payment.objects.filter(
                order=o, status=Payment.Status.CONFIRMED
            ).aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        baki = float(o.total) - float(confirmed)
        if baki > 0:
            total_deni += baki

    return {
        "wateja_wote": customers.count(),
        "manunuzi_jumla": float(total_manunuzi),
        "deni_jumla": total_deni,
    }


def _compute_madeni(store_id=None):
    orders = Order.objects.filter(status=Order.Status.PENDING)
    if store_id:
        orders = orders.filter(store_id=store_id)

    total = orders.aggregate(s=Sum("total"))["s"] or Decimal("0")
    return {
        "orders_deni": orders.count(),
        "deni_jumla": float(total),
    }


def _compute_gharama(store_id=None, start=None, end=None):
    expenses = Expense.objects.all()
    salaries = Salary.objects.filter(status=Salary.Status.PAID)

    if store_id:
        expenses = expenses.filter(store_id=store_id)
        salaries = salaries.filter(store_id=store_id)
    if start:
        expenses = expenses.filter(expense_date__gte=start)
        salaries = salaries.filter(month__gte=start)
    if end:
        expenses = expenses.filter(expense_date__lte=end)
        salaries = salaries.filter(month__lte=end)

    total_opex = expenses.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    total_salaries = (
        salaries.aggregate(s=Sum("total_paid"))["s"] or Decimal("0")
    )

    return {
        "opex": float(total_opex),
        "mishahara": float(total_salaries),
        "gharama_jumla": float(total_opex + total_salaries),
    }


def _compute_jumla(store_id=None, start=None, end=None):
    mauzo = _compute_mauzo(store_id, start, end)
    gharama = _compute_gharama(store_id, start, end)
    stoki = _compute_stoki(store_id)
    wateja = _compute_wateja(store_id)
    madeni = _compute_madeni(store_id)

    faida_safi = mauzo["mauzo"] - mauzo["cogs"] - gharama["gharama_jumla"]
    zaka = faida_safi * 0.1 if faida_safi > 0 else 0
    sadaka = faida_safi * 0.1 if faida_safi > 0 else 0

    return {
        "mauzo": mauzo,
        "gharama": gharama,
        "stoki": stoki,
        "wateja": wateja,
        "madeni": madeni,
        "faida_safi": faida_safi,
        "zaka": zaka,
        "sadaka": sadaka,
        "inayobaki": faida_safi - zaka - sadaka,
    }


# ==================================================================
# Helper — chagua compute function kulingana na aina
# ==================================================================
def _compute_data(aina, store_id=None, start=None, end=None):
    if aina == Document.Aina.MAUZO:
        return _compute_mauzo(store_id, start, end)
    if aina == Document.Aina.STOKI:
        return _compute_stoki(store_id)
    if aina == Document.Aina.WATEJA:
        return _compute_wateja(store_id)
    if aina == Document.Aina.MADENI:
        return _compute_madeni(store_id)
    if aina == Document.Aina.GHARAMA:
        return _compute_gharama(store_id, start, end)
    return _compute_jumla(store_id, start, end)


def _get_kipindi(start=None, end=None):
    if start and end:
        return f"{start} → {end}"
    if start:
        return f"Kuanzia {start}"
    return "Mwezi huu"


# ==================================================================
# GENERATE — zalisha document + PDF
# ==================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_document(request):
    """
    POST /api/documents/generate/
    Body: {
      aina: "mauzo" | "stoki" | "wateja" | "madeni" | "gharama" | "jumla",
      format: "pdf" | "csv" | "excel" (default "pdf"),
      store_id: uuid (optional),
      start: YYYY-MM-DD (optional),
      end: YYYY-MM-DD (optional)
    }
    """
    aina = request.data.get("aina")
    if aina not in Document.Aina.values:
        return Response(
            {"aina": ["Aina si sahihi."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    format_ = request.data.get("format", Document.Format.PDF)
    if format_ not in Document.Format.values:
        return Response(
            {"format": ["Format si sahihi."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    store_id = request.data.get("store_id") or None
    start = request.data.get("start") or None
    end = request.data.get("end") or None

    # Chukua store
    store = None
    if store_id:
        store = Store.objects.filter(pk=store_id).first()
        if not store:
            return Response(
                {"store_id": ["Duka haipo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Hesabu data
    try:
        data = _compute_data(aina, store_id, start, end)
    except Exception as exc:
        return Response(
            {"detail": f"Imeshindikana kuhesabu data: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Jina
    tarehe_str = date.today().isoformat()
    jina_map = {
        Document.Aina.MAUZO: "Ripoti ya Mauzo",
        Document.Aina.STOKI: "Ripoti ya Stoki",
        Document.Aina.WATEJA: "Ripoti ya Wateja",
        Document.Aina.MADENI: "Ripoti ya Madeni",
        Document.Aina.GHARAMA: "Ripoti ya Gharama",
        Document.Aina.JUMLA: "Ripoti ya Jumla",
    }
    jina = f"{jina_map[aina]} — {tarehe_str}"

    kipindi = _get_kipindi(start, end)

    # Unda document
    doc = Document.objects.create(
        jina=jina,
        aina=aina,
        format=format_,
        hali=Document.Hali.TAYARI,
        ukubwa="0 KB",
        kipindi=kipindi,
        store=store,
        aliyezalisha=request.user,
        data_snapshot=data,
    )

    # Zalisha PDF (au CSV)
    store_name = store.name if store else "Maduka Yote"
    try:
        if format_ == Document.Format.PDF:
            pdf_bytes = generate_pdf(
                aina=aina,
                jina=jina,
                store_name=store_name,
                kipindi=kipindi,
                aliyezalisha=request.user.full_name,
                data=data,
            )
            size_kb = max(1, len(pdf_bytes) // 1024)
            doc.ukubwa = f"{size_kb} KB"
        else:
            # CSV — hesabu size tu
            snapshot_json = json.dumps(data, default=str)
            size_kb = max(1, len(snapshot_json) // 1024 + 1)
            doc.ukubwa = f"{size_kb} KB"

        doc.save(update_fields=["ukubwa"])
    except Exception as exc:
        # Futa document kama PDF imeshindikana
        doc.delete()
        return Response(
            {"detail": f"Imeshindikana kuzalisha PDF: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        DocumentSerializer(doc).data,
        status=status.HTTP_201_CREATED,
    )


# ==================================================================
# LIST
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def documents_list(request):
    """
    GET /api/documents/
    Filters: ?aina=mauzo  ?store=<uuid>  ?limit=50
    """
    qs = (
        Document.objects.select_related("store", "aliyezalisha")
        .order_by("-created_at")
    )

    aina = request.query_params.get("aina")
    store_id = request.query_params.get("store")

    if aina:
        qs = qs.filter(aina=aina)
    if store_id:
        qs = qs.filter(store_id=store_id)

    try:
        limit = int(request.query_params.get("limit", 200))
    except ValueError:
        limit = 200
    limit = max(1, min(limit, 500))

    qs = qs[:limit]
    return Response(DocumentSerializer(qs, many=True).data)


# ==================================================================
# DETAIL + DELETE
# ==================================================================
@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def document_detail(request, pk):
    """
    GET    /api/documents/<uuid>/
    DELETE /api/documents/<uuid>/
    """
    doc = get_object_or_404(Document, pk=pk)

    if request.method == "GET":
        return Response(DocumentSerializer(doc).data)

    doc.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ==================================================================
# DOWNLOAD PDF
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_pdf(request, pk):
    """
    GET /api/documents/<uuid>/download/
    Zalisha PDF upya na rudisha kama file.
    """
    doc = get_object_or_404(Document, pk=pk)

    # Zalisha PDF upya (data_snapshot imehifadhiwa)
    try:
        pdf_bytes = generate_pdf(
            aina=doc.aina,
            jina=doc.jina,
            store_name=doc.store.name if doc.store else "Maduka Yote",
            kipindi=doc.kipindi,
            aliyezalisha=doc.aliyezalisha.full_name,
            data=doc.data_snapshot or {},
        )
    except Exception as exc:
        return Response(
            {"detail": f"Imeshindikana kuzalisha PDF: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    filename = f"{doc.aina}-{doc.id}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ==================================================================
# DOWNLOAD CSV
# ==================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_csv(request, pk):
    """
    GET /api/documents/<uuid>/download-csv/
    Zalisha CSV na rudisha kama file.
    """
    doc = get_object_or_404(Document, pk=pk)
    data = doc.data_snapshot or {}

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["SMART HARDWARE"])
    writer.writerow([doc.jina])
    writer.writerow([f"Kipindi: {doc.kipindi}"])
    writer.writerow([f"Aliyezalisha: {doc.aliyezalisha.full_name}"])
    writer.writerow([f"Tarehe: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    writer.writerow([])

    # Data
    if doc.aina == Document.Aina.JUMLA:
        writer.writerow(["Kipengele", "Thamani"])
        writer.writerow(["Mauzo", data.get("mauzo", {}).get("mauzo", 0)])
        writer.writerow(["COGS", data.get("mauzo", {}).get("cogs", 0)])
        writer.writerow(["Faida Ghafi", data.get("mauzo", {}).get("faida", 0)])
        writer.writerow(["Gharama", data.get("gharama", {}).get("gharama_jumla", 0)])
        writer.writerow(["Faida Safi", data.get("faida_safi", 0)])
        writer.writerow(["Zaka (10%)", data.get("zaka", 0)])
        writer.writerow(["Sadaka (10%)", data.get("sadaka", 0)])
        writer.writerow(["Inayobaki", data.get("inayobaki", 0)])
    else:
        writer.writerow(["Kipengele", "Thamani"])
        for key, value in data.items():
            writer.writerow([key, value])

    response = HttpResponse(
        output.getvalue(), content_type="text/csv"
    )
    filename = f"{doc.aina}-{doc.id}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response