from pathlib import Path
import math
import struct
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
PRINTS = ROOT / "prints-reais"
WIDTH, HEIGHT, FPS = 720, 1280, 24
SECONDS_PER_SCENE = 3
FRAMES_PER_SCENE = FPS * SECONDS_PER_SCENE

SCENES = [
    ("1.jpg", "AGENDA CHEIA", "Gestão leve para o seu negócio"),
    ("2.jpg", "TUDO EM UM SÓ LUGAR", "Agenda, WhatsApp, financeiro e equipe"),
    ("3.jpg", "RESULTADOS REAIS", "Mais organização no dia a dia"),
    ("4.jpg", "30 DIAS PARA TESTAR", "Conheça o SalãoPro"),
    ("visão do gestor 1.jpg", "AGENDA ORGANIZADA", "Acompanhe cada atendimento"),
    ("visão do gestor 3.jpg", "SERVIÇOS SOB CONTROLE", "Duração, preço e disponibilidade"),
    ("visão do gestor 6.jpg", "FINANCEIRO CLARO", "Faturamento, comissões e lucro"),
    ("visão do gestor 7.jpg", "DO SEU JEITO", "Horários e fidelidade configuráveis"),
    ("visão do gestor 9.jpg", "SINAL VIA PIX", "Mais segurança para a sua agenda"),
    ("visão do gestor 10.jpg", "WHATSAPP CONECTADO", "SALAOPRO.SITE"),
]


def get_font(size, bold=False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def fit_cover(image, width, height):
    ratio = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def fit_inside(image, width, height):
    ratio = min(width / image.width, height / image.height)
    return image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def make_scene(source, headline, subtitle, progress):
    source = source.convert("RGB")
    background = fit_cover(source, WIDTH, HEIGHT).filter(ImageFilter.GaussianBlur(30))
    background = ImageEnhance.Brightness(background).enhance(0.22)
    tint = Image.new("RGBA", (WIDTH, HEIGHT), (7, 17, 31, 150))
    frame = Image.alpha_composite(background.convert("RGBA"), tint)

    zoom = 1.0 + progress * 0.018
    screen = fit_inside(source, int(680 * zoom), int(430 * zoom))
    screen = ImageEnhance.Contrast(screen).enhance(1.04)
    x = (WIDTH - screen.width) // 2
    y = 385 + round(8 * math.sin(progress * math.pi)) - (screen.height - fit_inside(source, 680, 430).height) // 2

    shadow = Image.new("RGBA", (screen.width + 30, screen.height + 30), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((15, 15, screen.width + 14, screen.height + 14), radius=24, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    frame.alpha_composite(shadow, (x - 15, y - 8))
    frame.paste(screen, (x, y), rounded_mask(screen.size, 18))

    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle((52, 85, 250, 127), radius=20, fill="#ff5c6c")
    draw.text((151, 106), "SALÃOPRO", font=get_font(19, True), fill="white", anchor="mm")
    draw.text((WIDTH // 2, 205), headline, font=get_font(45, True), fill="#f7fbff", anchor="mm")
    draw.text((WIDTH // 2, 270), subtitle, font=get_font(26), fill="#b6c6d9", anchor="mm")
    draw.line((215, 320, 505, 320), fill="#21d4d8", width=4)
    draw.text((WIDTH // 2, 950), "Simples para sua equipe.", font=get_font(31, True), fill="#f7fbff", anchor="mm")
    draw.text((WIDTH // 2, 1000), "Prático para seus clientes.", font=get_font(31, True), fill="#ff7a45", anchor="mm")
    draw.rounded_rectangle((110, 1080, WIDTH - 110, 1168), radius=28, fill="#ff5c6c")
    cta = "ACESSE SALAOPRO.SITE" if "SALAOPRO.SITE" in subtitle else "GESTÃO QUE TRABALHA POR VOCÊ"
    draw.text((WIDTH // 2, 1124), cta, font=get_font(25, True), fill="white", anchor="mm")
    return frame.convert("RGB")


def create_music(path, seconds=30, rate=44100):
    notes = [261.63, 329.63, 392.00, 493.88, 293.66, 369.99, 440.00, 523.25]
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        data = bytearray()
        for i in range(seconds * rate):
            t = i / rate
            note = notes[int(t * 2) % len(notes)]
            pulse = t % 0.5
            env = min(1, pulse / 0.04) * math.exp(-1.8 * pulse)
            value = (
                math.sin(2 * math.pi * note / 2 * t) * 0.13
                + math.sin(2 * math.pi * note * t) * 0.09 * env
                + math.sin(2 * math.pi * 62 * t) * 0.07 * math.exp(-12 * pulse)
            )
            fade = min(1, t / 1.0, (seconds - t) / 1.0)
            sample = int(max(-1, min(1, value * fade)) * 32767)
            data.extend(struct.pack("<hh", sample, sample))
        wav.writeframes(data)


def main():
    missing = [name for name, _, _ in SCENES if not (PRINTS / name).exists()]
    if missing:
        raise SystemExit(f"Prints ausentes: {missing}")

    sys.path.insert(0, str(ROOT.parent.parent / ".video_tools"))
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    sources = [(Image.open(PRINTS / name), title, subtitle) for name, title, subtitle in SCENES]
    silent = ROOT / "salaopro-real-silent.mp4"
    soundtrack = ROOT / "salaopro-real-trilha.wav"
    output = ROOT / "salaopro-video-30s-prints-reais.mp4"

    command = [
        ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-", "-an",
        "-vcodec", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(silent),
    ]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    previous = None
    for source, headline, subtitle in sources:
        for local_frame in range(FRAMES_PER_SCENE):
            progress = local_frame / max(1, FRAMES_PER_SCENE - 1)
            frame = make_scene(source, headline, subtitle, progress)
            if previous is not None and local_frame < 10:
                frame = Image.blend(previous, frame, local_frame / 10)
            encoder.stdin.write(frame.tobytes())
            previous = frame
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise SystemExit("Falha ao renderizar o vídeo")

    create_music(soundtrack)
    subprocess.run([
        ffmpeg, "-y", "-i", str(silent), "-i", str(soundtrack), "-c:v", "copy", "-c:a", "aac",
        "-b:a", "160k", "-t", "30", "-movflags", "+faststart", str(output),
    ], check=True)
    silent.unlink(missing_ok=True)
    soundtrack.unlink(missing_ok=True)
    print(output)


if __name__ == "__main__":
    main()
