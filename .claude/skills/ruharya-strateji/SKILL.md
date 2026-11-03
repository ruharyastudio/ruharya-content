---
name: ruharya-strateji
description: Ruharya Nefes Instagram'ı için haftalık performans, rakip ve pazar analizi yapar; raporu ve yeni fikirleri kontrol paneline yazar. Haftalık strateji görevi veya "rapor hazırla / rakipleri incele / yeni fikir üret" istekleri için kullan.
---

# Ruharya · Haftalık Strateji Raporu

Amaç: Her pazar @ruharya'nın son haftasını ölçmek, pazarı ve rakipleri taramak, sonuçları kontrol
paneline rapor olarak yazmak ve Ali'nin onayına yeni fikirler sunmak. Dil: Türkçe.
Sabitler, panel veri modeli ve içerik kuralları: `.claude/skills/ruharya-instagram/SKILL.md`.

## Adımlar
1. **Kendi verimiz (Buffer):**
   - `mcp__Buffer__get_aggregated_post_metrics` son 7 gün ve önceki 7 gün (Instagram kanalı).
   - `mcp__Buffer__list_posts` `includeMetrics: true`, son 7 günün gönderileri. Panelin `posts` kayıtlarıyla eşleştir
     ve formata göre (öğreti/pratik/bilim/etkileşim) erişim, kaydetme, paylaşım, yorum karşılaştır.
   - Metrikler günde bir güncellenir; az gönderiyle güçlü sonuç çıkarma, "erken veri" diye belirt.
   - **Reels hunisi:** Panelde `funnels` koleksiyonunu oku. Her huni için Buffer'dan Reels ve carousel metriklerini
     (reach, saves, shares, follows) al; kaydetme/erişim ve paylaşım/erişim oranlarını karşılaştır. Ali'nin panele
     girdiği profil ziyareti/takip verisini kullan; girilmemişse "Insights verisi girilmedi" yaz. Rapora
     "Reels hunisi" bölümü ekle. En az 2-3 huni birikmeden kesin karar önerme.
2. **Rakip ve pazar taraması (web):**
   - Türkçe nefes uygulamaları: en az Breath Hub ve Nefes Al'ın mağaza sayfalarını yeniden oku (fiyat, puan, yeni özellik).
   - Yeni giren var mı: "nefes egzersizi uygulaması", "nefes koçu", "breathwork Türkiye" aramaları.
   - Platform: Instagram'ın resmi duyuruları, Adam Mosseri açıklamaları, Buffer/Later gibi veri yayınlayan kaynaklar.
   - Instagram profil sayfaları çoğunlukla okunamaz; okuyamadığın veriyi tahmin etme, raporda "erişilemedi" yaz.
3. **Rapor yaz:** Panelde `reports/<YYYY-MM-DD>-haftalik` (ayın ilk pazarı ise ek olarak `-rakip` türünde
   kapsamlı rakip raporu). Bölümler: "Bu hafta (kendi verimiz)", "Rakiplerde değişenler", "Platformda değişenler",
   "Öneriler". Her dış bilgiye kaynak ekle. Kendi verini ve ikincil kaynak iddialarını ayrı tut.
4. **Fikir üret:** Mevcut `ideas` koleksiyonunu oku, tekrar etme. 5-8 yeni fikir ekle (`status: oneri`, `source: claude`,
   her birine somut `rationale`: hangi veri ya da gözlemden çıktığı). Karışım: en az 3 içerik konusu
   (öğreti/pratik/bilim/etkileşim), en az 1 `strateji` (süreç, format, büyüme), uygunsa 1 `reels`.
5. **Eski önerileri temizle:** 30 günden eski ve hâlâ `oneri` durumundaki fikirlere dokunma; raporda "bekleyen eski öneri sayısı"nı belirt.
6. **Özet:** Bitince tek paragraf: haftanın en önemli bulgusu, eklenen fikir sayısı, panel bağlantısı.

## Kurallar
- Uydurma sayı, istatistik ya da alıntı yok. Doğrulayamadığını yazma.
- Ritim ya da kurallarda değişiklik önerirsen bunu `strateji` fikri olarak ekle; SKILL dosyalarını kendin değiştirme.
  Ali onayladığında günlük görev uygular.
- Rakipleri kötüleme; gözlemi nesnel yaz.
