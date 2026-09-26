from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "checklist-funcoes-gestor-salaopro.png"
W, H = 1080, 1920


def font(size, bold=False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def fit_cover(img, width, height):
    ratio = max(width / img.width, height / img.height)
    img = img.resize((round(img.width * ratio), round(img.height * ratio)), Image.Resampling.LANCZOS)
    left = (img.width - width) // 2
    top = (img.height - height) // 2
    return img.crop((left, top, left + width, top + height))


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def draw_check(draw, x, y, text, max_width=390):
    draw.ellipse((x, y + 3, x + 24, y + 27), fill="#21d4d8")
    draw.line((x + 6, y + 15, x + 11, y + 20, x + 19, y + 10), fill="#07111f", width=3)
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font(25)) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    for index, line in enumerate(lines):
        draw.text((x + 38, y + index * 30), line, font=font(25), fill="#d8e3ef")
    return max(34, len(lines) * 30)


def card(canvas, box, title, items, accent):
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)
    shadow = Image.new("RGBA", (x2 - x1 + 30, y2 - y1 + 30), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((15, 15, x2 - x1 + 14, y2 - y1 + 14), radius=30, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(shadow, (x1 - 15, y1 - 6))
    draw.rounded_rectangle(box, radius=28, fill="#0d1b2e", outline="#24364c", width=2)
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 38, y1 + 72), radius=7, fill=accent)
    draw.text((x1 + 58, y1 + 28), title, font=font(31, True), fill="#f7fbff")
    y = y1 + 88
    for item in items:
        y += draw_check(draw, x1 + 28, y, item, x2 - x1 - 95) + 7


def main():
    canvas = Image.new("RGBA", (W, H), "#07111f")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, -240, 670, 680), fill=(33, 212, 216, 42))
    gd.ellipse((650, 80, 1430, 900), fill=(255, 92, 108, 45))
    gd.ellipse((500, 1300, 1300, 2150), fill=(255, 122, 69, 25))
    canvas = Image.alpha_composite(canvas, glow.filter(ImageFilter.GaussianBlur(70)))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((60, 48, 250, 100), radius=25, fill="#ff5c6c")
    draw.text((155, 74), "SALÃOPRO", font=font(25, True), fill="white", anchor="mm")
    draw.text((60, 145), "Tudo o que o gestor", font=font(61, True), fill="#f7fbff")
    draw.text((60, 213), "controla em um só lugar.", font=font(61, True), fill="#21d4d8")
    draw.text((62, 292), "Mais organização, visão do negócio e tempo para crescer.", font=font(29), fill="#b6c6d9")

    shot = Image.open(ROOT / "prints-reais" / "visão do gestor 1.jpg").convert("RGB")
    shot = fit_cover(shot, 960, 340)
    shot = ImageEnhance.Contrast(shot).enhance(1.04)
    canvas.paste(shot, (60, 355), rounded_mask(shot.size, 28))
    draw.rounded_rectangle((60, 355, 1020, 695), radius=28, outline="#ff5c6c", width=4)

    cards = [
        ("AGENDA E OPERAÇÃO", ["Visualizar e filtrar atendimentos", "Confirmar, concluir ou cancelar", "Bloquear e liberar horários"], "#ff5c6c"),
        ("SERVIÇOS", ["Cadastrar e editar serviços", "Definir duração e preço", "Ativar ou desativar opções"], "#ff7a45"),
        ("EQUIPE", ["Cadastrar profissionais", "Gerenciar acessos da equipe", "Organizar a rotina de atendimento"], "#21d4d8"),
        ("CLIENTES", ["Consultar clientes cadastrados", "Definir regra individual de sinal", "Preservar histórico de atendimento"], "#ff5c6c"),
        ("FINANCEIRO", ["Faturamento bruto e lucro líquido", "Comissões por profissional", "Filtro por período e PDF"], "#21d4d8"),
        ("CONFIGURAÇÕES", ["Definir horários e intervalo", "Limite de cancelamento", "Lembrete automático de retorno"], "#ff7a45"),
        ("AUTOMAÇÕES", ["Sinal de 50% via PIX", "Programa de fidelidade", "Confirmações pelo WhatsApp"], "#ff5c6c"),
        ("DIVULGAÇÃO E ACESSO", ["Link exclusivo de agendamento", "Placa com QR Code", "Gestão da assinatura do sistema"], "#21d4d8"),
    ]

    card_w, card_h = 465, 245
    start_y = 735
    for i, (title, items, accent) in enumerate(cards):
        col, row = i % 2, i // 2
        x = 60 + col * 495
        y = start_y + row * 265
        card(canvas, (x, y, x + card_w, y + card_h), title, items, accent)

    footer_y = 1810
    draw.rounded_rectangle((145, footer_y, W - 145, footer_y + 76), radius=32, fill="#ff5c6c")
    draw.text((W // 2, footer_y + 38), "TESTE GRÁTIS POR 30 DIAS", font=font(29, True), fill="white", anchor="mm")
    draw.text((W // 2, 1895), "SALAOPRO.SITE", font=font(33, True), fill="#f7fbff", anchor="mm")
    canvas.convert("RGB").save(OUT, quality=95)
    print(OUT)


if __name__ == "__main__":
    main()
