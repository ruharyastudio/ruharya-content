# Ruharya · Haftalık Strateji Raporu (Zeus sunucu sürümü)

Bu dosya `.claude/skills/ruharya-strateji/SKILL.md` becerisinin **Zeus sunucusunda** çalışan sürümüdür.
**Amaç, adımlar, rapor bölümleri ve kurallar için orijinal SKILL.md'yi oku ve aynen uygula.** Farklar yalnızca araçlarda:

## Araçlar
- Veri (**R**): `/home/zeus/zeus-panel/.venv/bin/python /home/zeus/zeus-panel/ruharya_veri.py <komut>`
- Buffer (**B**): `/home/zeus/zeus-panel/.venv/bin/python /home/zeus/zeus-panel/buffer_api.py <komut>`
- Komutlarda boru, `&&` ya da yönlendirme kullanma; JSON'u önce Write ile `build/` altına yaz, dosya yolunu ver.

| Eski | Yeni |
|---|---|
| `mcp__Buffer__get_aggregated_post_metrics` (son 7 gün / önceki 7 gün) | `B metrikler --gun 7 --zorla` ve `B metrikler --gun 14 --zorla` (14 − 7 = önceki hafta) |
| `mcp__Buffer__list_posts` `includeMetrics` | `B gonderiler --gun 7` + her gönderi için `B gonderi <id>` (metrikler dahil) |
| panel `posts` / `funnels` | `R yayinlar 14`, `R huniler` |
| panel `ideas` oku | `R fikirler` |
| `reports/<YYYY-MM-DD>-haftalik` yaz | `R rapor-yaz build/rapor.json` — alanlar: `id, kind (haftalik/rakip), date, title, summary, sections[{heading, items[]}], recommendations[], sources[{title,url}]` |
| fikir ekle (`status: oneri`, `source: claude`) | `R fikir-ekle-json build/fikirler.json` (liste; her biri `title, summary, format, tradition, rationale`) |

Buffer metrik komutu hata verirse ("BUFFER HATA") bunu raporda "Buffer verisi alınamadı: <neden>" diye yaz; sayı uydurma.

## Son mesaj (Telegram'a aynen gider)
TEK paragraf: haftanın en önemli bulgusu, eklenen fikir sayısı, rapor id'si ("Zeus paneli → Ruharya'da görünür").
