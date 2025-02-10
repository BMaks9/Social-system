import segno
import base64
from io import BytesIO


def generate_disability_qr(disability, patronages, data_dilivery):
    # Формируем информацию для QR-кода
    info = f"Заявка №{disability.id}\n\nНомер телефона: {disability.phone}\nАдрес: {disability.address}\n\nУслуги:\n"

    # Генерация QR-кода
    for patronage in patronages:
        info += f'\t+ {patronage["title"]}\n'
        info += f"\t\t\tКомментарий: {patronage['comment']}\n"

    info += f"\nДата доставки: {data_dilivery}\n-----------------------------------\nДата создания: {disability.data_created}"

    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind="png")
    buffer.seek(0)

    # Конвертация изображения в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return qr_image_base64
