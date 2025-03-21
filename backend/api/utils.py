from io import BytesIO

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_shopping_list(ingredients):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = ('attachment;'
                                       'filename="shopping_cart.pdf"')

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    pdfmetrics.registerFont(TTFont('DejaVu', 'static/fonts/DejaVuSans.ttf'))
    p.setFont('DejaVu', 12)
    x = 100
    y = 750

    p.drawString(x, y, "Список покупок")
    y -= 20

    for ingredient, details in ingredients.items():
        p.drawString(
            x, y, f'{ingredient}'
            f'({details["measurement_unit"]}):'
            f'{details["total_amount"]}'
        )
        y -= 20

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
