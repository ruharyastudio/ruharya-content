# Ruharya Nefes · Günlük Instagram Gönderisi (Zeus sunucu sürümü)

Bu dosya `.claude/skills/ruharya-instagram/SKILL.md` becerisinin **Zeus sunucusunda** çalışan sürümüdür.
**İçerik kuralları, haftalık ritim, Reels hunisi, açıklama kalıbı ve sabitler için orijinal SKILL.md'yi oku ve
aynen uygula.** Bu dosya yalnızca şu farkları tanımlar: kontrol paneli (ArtifactData) yerine `~/zeus/ruharya/`
verisi, Buffer MCP yerine Buffer resmi API'si, SendUserMessage yerine son mesajın Telegram'a gitmesi.

## Araçlar (yalnızca bunları kullan)
- Veri: `/home/zeus/zeus-panel/.venv/bin/python /home/zeus/zeus-panel/ruharya_veri.py <komut>` (aşağıda **R**)
- Buffer: `/home/zeus/zeus-panel/.venv/bin/python /home/zeus/zeus-panel/buffer_api.py <komut>` (aşağıda **B**)
- Görsel/video: `.venv/bin/python tools/carousel.py ...`, `.venv/bin/python tools/reel.py ...`
  (`python3` yerine her zaman `.venv/bin/python`; playwright ve Chromium oradadır)
- Komutlarda boru (`|`), `&&` ya da yönlendirme kullanma; JSON vermek gereken yerde önce Write ile
  `build/` altına dosya yaz, sonra dosya yolunu argüman olarak ver (`build/` git'e girmez).

Eski panel → yeni karşılık:
| Eski (ArtifactData) | Yeni |
|---|---|
| `settings/main` oku | `R ayarlar` → `paused`, `postTime` |
| `ideas` oku | `R fikirler --durum onayli` (ya da `--format pratik` vb.) |
| fikir `status` → `kullanildi` | `R fikir-kullanildi <id>` |
| `posts/<id>` oluştur/güncelle | `R yayin-yaz build/yayin.json` (alanlar aynı: id, date, format, topic, tradition, bufferId, status) |
| `funnels/<id>` oluştur | `R huni-yaz build/huni.json` (alanlar aynı; `pinned: false`) |
| `mcp__Buffer__create_post` | `B olustur --metin content/<x>.caption.txt --gorsel <url> --alt "<alt>" [--gorsel ... --alt ...] --zaman <ISO+03:00>` |
| Reels | `B olustur --metin content/<x>.reel.caption.txt --video <url> --tur reel --zaman <Perşembe>T12:30:00+03:00` |
| `saveToDraft: true` | `B olustur ... --taslak` (zamanlama yok) |
| Buffer'dan gönderi durumu | `B gonderi <id>` |

## Çalışma modu
Ortam değişkeni `RUHARYA_TASLAK=1` ise (görev metni de bunu söyler) **TASLAK MODU**:
- `paused` ve çift gönderi kontrolünü atla (deneme amaçlıdır).
- Klasör ve dosya adlarını **`taslak-` önekiyle** kullan: `content/taslak-YYYY-MM-DD-konu.json`,
  `posts/taslak-YYYY-MM-DD-konu/`. (Önek zorunlu: claude.ai'deki eski görev `posts/` altında bugünün tarihiyle
  başlayan klasör görürse o günün paylaşımını atlar.)
- `content/yayin-kaydi.md`, `content/konu-havuzu.md` ve fikir durumlarını DEĞİŞTİRME.
- Buffer'a yalnızca `--taslak` ile koy; Reels üretme.
- `R yayin-yaz` ile `id: taslak-...`, `status: draft` kaydı yaz.

## Adımlar (normal mod)
0. `R ayarlar` → `paused: true` ise hiçbir şey üretme; son mesajın "Paylaşım panelden duraklatılmış." olsun ve bitir.
   Çift gönderi kontrolü: orijinal SKILL.md adım 0 ile aynı (`content/yayin-kaydi.md` + `posts/`), ayrıca
   `R yayinlar 5` içinde bugünün tarihli carousel kaydı varsa üretme.
1. Hazırlık gerekmez (`npm ci`, venv ve Chromium sunucuda kurulu). Yazı tipleri eksikse `npm ci`.
2. Konu seç: orijinal adım 2; panel yerine `R fikirler --durum onayli`.
3-5. Araştır, yaz, üret: orijinal adımlar 3-5 (WebSearch/WebFetch ile doğrulama zorunlu; görselleri Read ile kontrol et).
6. Yükle: `git add posts content`, `git commit -m "Gönderi: <konu> (<format>, <tarih>)"`, `git push origin HEAD:main`.
   Push reddedilirse `git pull --rebase origin main` ve tekrar push. Commit kimliği depoda ayarlıdır (Claude <noreply@anthropic.com>).
   Her görsel adresini `curl -s -o /dev/null -w "%{http_code}" <url>` ile kontrol et (200 olmalı; raw.githubusercontent
   önbelleği için 200 gelene kadar en fazla 3 kez, 20 sn arayla dene).
7. Zamanla: `B olustur ... --zaman <bugün>T20:30:00+03:00` (her görsele `--alt`). 20:30 geçtiyse `--simdi`.
   Çarşamba: Reels'i orijinal SKILL.md'ye göre üret, push et, `B olustur --video ... --tur reel --zaman <Perşembe>T12:30:00+03:00`.
8. Kaydet: orijinal adım 8; panel yerine `R yayin-yaz` (+ Çarşamba `R huni-yaz`), kullanılan fikir için `R fikir-kullanildi`.
   Dünkü kayıt `scheduled` ise `B gonderi <bufferId>` ile durumunu oku, `R yayin-yaz` ile güncelle (`sent`/`error`).

## Hata durumunda
Push, görsel adresi ya da Buffer adımı başarısız olursa bir kez yeniden dene. Yine olmazsa gönderiyi `--taslak` ile
Buffer'a taslak bırak, kaydı `status: error` yaz ve son mesajda nedeni açıkça belirt.

## Son mesaj (Telegram'a aynen gider)
TEK paragraf, Türkçe: konu ve format, slayt sayısı, Buffer gönderi id'si ve zamanı (ya da "taslak"), Reels varsa onun
id ve zamanı, Çarşamba ise "Çarşamba 20:30'dan sonra carousel'i profilde sabitle" hatırlatması, hata varsa nedeni.
