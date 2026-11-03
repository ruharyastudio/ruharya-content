# ruharya-content

Ruharya Studio'nun @ruharya Instagram hesabı için otomatik içerik deposu. Bu repo herkese açıktır;
görseller `raw.githubusercontent.com` üzerinden Buffer'a verilir. Gizli bilgi (anahtar, şifre) koyma.

- Günlük gönderi süreci ve tüm kurallar: `.claude/skills/ruharya-instagram/SKILL.md`
- Üretici: `tools/carousel.py` (JSON → 1080×1350 JPEG, `dark` / `light` tema); `tools/reel.py` (JSON → 1080×1920 statik Reels mp4, telifsiz sentez ses)
- İçerik: `content/` (JSON + açıklama metni, konu havuzu, yayın kaydı, haftalık rapor)
- Görseller: `posts/YYYY-MM-DD-konu/NN.jpg`

Marka (Ruharya Nefes): gece mavisi #1A1A2E, #2D2D44, altın #D4AF37, beyaz #F5F5F5; açık tema krem #F5F0E6.
Yazı tipleri: Cormorant Garamond (başlık), Inter (gövde). Slogan: "Nefes, En Eski Rehberindir".
Dil: Türkçe. Commit kimliği: `Claude <noreply@anthropic.com>`.
