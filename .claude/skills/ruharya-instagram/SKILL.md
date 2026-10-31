---
name: ruharya-instagram
description: Ruharya Nefes için günlük Instagram carousel'i üretir, GitHub'a yükler ve Buffer üzerinden @ruharya hesabına zamanlar. Günlük otomatik paylaşım, yeni gönderi üretme veya içerik ritmi soruları için kullan.
---

# Ruharya Nefes · Günlük Instagram Gönderisi

Amaç: Her gün 20:30'da (Europe/Istanbul) @ruharya'da nefesle ilgili kadim öğretileri doğru, kaynaklı ve
etkileşim toplayan bir carousel yayınlamak. Şu an yalnızca **Ruharya Nefes** uygulaması yayında; tüm içerik
nefes ekseninde kalır. Kimlik: Ruharya Studio, kurucu Ali Çam. Dil: Türkçe.

## Sabitler
- Buffer organizasyon: `6a85e621746545c1e15adfb1` (My Organization)
- Buffer Instagram kanal (@ruharya, business): `6a85fd6cccaf649a67d98165`
- Görsel adresi: `https://raw.githubusercontent.com/ruharyastudio/ruharya-content/main/posts/<klasör>/<NN>.jpg`
- Yayın saati: her gün 20:30, `+03:00`

## Haftalık ritim (İstanbul gününe göre)
| Gün | Format | Tema |
|---|---|---|
| Pazartesi | Öğreti carousel'i (5-6 slayt) | dark |
| Salı | Pratik carousel'i (3-4 slayt, `steps` slaytı) | light |
| Çarşamba | Öğreti carousel'i | dark |
| Perşembe | Nefes ve bilim (kaynaklı, abartısız) | dark |
| Cuma | Öğreti carousel'i | dark |
| Cumartesi | Pratik carousel'i | light |
| Pazar | Etkileşim: "hangisi sana yakın?", doğru/yanlış, kısa test | dark |

Gelenekleri dönüşümlü kullan; aynı gelenek art arda iki gün gelmesin. Pratik günleri mümkünse o haftanın
öğretisine bağlansın ("Pazartesi prana'yı konuştuk, bugün nāḍī śodhana").

## Adımlar
1. **Hazırlık:** `npm ci` (veya `npm i`), gerekirse `python3 -m playwright install chromium`.
2. **Konu seç:** `content/yayin-kaydi.md` ve `content/konu-havuzu.md` oku. Bugünün formatına uyan,
   kayıtta olmayan ilk konuyu al. Havuz azaldıysa (formata uygun < 5 konu) yeni konular ekle.
3. **Araştır ve doğrula (zorunlu):** Her olgusal iddiayı WebSearch/WebFetch ile birincil veya akademik
   kaynaktan doğrula (metnin kendisi, ansiklopedi, hakemli makale). Doğrulayamadığın bilgiyi kullanma.
   Kaynak künyesini ilgili slaytın `src` alanına yaz (ör. "Haṭha Yoga Pradīpikā 2.2").
4. **İçeriği yaz:** `content/YYYY-MM-DD-konu.json` + `content/YYYY-MM-DD-konu.caption.txt`.
   Şema `tools/carousel.py` başındaki açıklamada. Kapak bir merak sorusu ya da çarpıcı bir iddia olsun.
5. **Üret:** `python3 tools/carousel.py content/<dosya>.json posts/YYYY-MM-DD-konu`.
   "UYARI ... taşıyor" çıkarsa metni kısalt ve yeniden üret. En az kapak ve bir iç slaytı Read ile aç ve gözle kontrol et.
6. **Yükle:** `posts/` ve `content/` değişikliklerini commit'le, `git push origin HEAD:main`.
   Her görsel adresinin `curl -o /dev/null -w "%{http_code}"` ile 200 döndüğünü doğrula.
7. **Zamanla:** `mcp__Buffer__create_post` → channelId yukarıdaki, `schedulingType: automatic`,
   `mode: customScheduled`, `dueAt: <bugün>T20:30:00+03:00`, `metadata.instagram = {type: "post", shouldShareToFeed: true}`,
   her görsel için `altText`. Saat 20:30 geçtiyse `mode: shareNow` kullan.
8. **Kaydet:** `content/yayin-kaydi.md`'ye satır ekle (tarih, format, konu, gelenek, Buffer post id), commit + push.
9. **Pazar ek görevi:** `mcp__Buffer__get_aggregated_post_metrics` ile son 7 günü al; `content/haftalik-rapor.md`'ye
   tarihli kısa not ekle (en iyi/en zayıf format, gözlem, gelecek hafta için tek değişiklik). Ritmi buna göre ayarla.

## İçerik kuralları
- **Doğruluk her şeyden önce.** Uydurma alıntı yok. İnternette dolaşan "Mevlânâ/Buda/Lao Tzu sözü"
  türü atıfları birincil kaynakta görmeden kullanma.
- **Telif:** Yalnızca 1929 öncesi metinlerden kısa alıntı. Modern çevirileri kopyalama; kendi Türkçe aktarımını yap.
- **Sağlık:** Tıbbi iddia yok ("tedavi eder", "kaygıyı yok eder", "bağışıklığı güçlendirir" yasak).
  Bilim gönderilerinde yalnızca hakemli çalışmaların gerçekten gösterdiğini söyle, sınırlılığı belirt.
  Pratiklerde güvenlik notu zorunlu. Hiperventilasyon, uzun nefes tutma ve "Wim Hof" tarzı yoğun teknikleri anlatma.
- **Din ve gelenek:** Saygılı ve tarafsız; "X geleneği şöyle anlatır" kipi. Övme, yerme, karşılaştırıp üstün ilan etme yok.
- **Ton:** Sakin, bilge, merak uyandıran; vaaz değil. "Sen" hitabı.
- **Slayt:** En fazla ~70 kelime. Kelime kökü, kısa hikâye, tek fikir. Sanskritçe/Arapça terimlerde doğru transliterasyon.

## Açıklama (caption) kalıbı
1. Kanca (tek cümle, merak)
2. 2-3 kısa paragraf: öğretinin özü, kendi cümlelerinle
3. "Kaydır ➡️" yönlendirmesi
4. 💬 tek, cevaplaması kolay bir soru
5. 🔖 kaydet çağrısı
6. "Nefesle kendi pratiğine başlamak istersen: Ruharya Nefes (profildeki link)"
7. 6-10 hashtag: sabitler `#RuharyaNefes #Ruharya` + konuya özel Türkçe/İngilizce karışık

## Hata durumunda
Push, görsel adresi veya Buffer adımı başarısız olursa bir kez yeniden dene. Yine olmazsa gönderiyi
`saveToDraft: true` ile taslak bırak ve SendUserMessage ile Ali'ye kısa, net bir not gönder.
