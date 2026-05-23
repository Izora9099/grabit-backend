# GrabIT — Mock Data Sheet (Local Testing)

> All passwords: **`Grabit2024!`**
> Currency: **XAF (Cameroon Francs)**
> Designed to match the frontend mock data at `/src/data/`

---

## 1. USERS (14 accounts)

| # | Email | First | Last | Role | Phone | City | KYC |
|---|-------|-------|------|------|-------|------|-----|
| 1 | admin@grabit.cm | Platform | Admin | admin | +237 670 000 001 | Douala | ✓ |
| 2 | amina.nji@gmail.com | Amina | Nji | buyer | +237 677 123 456 | Douala | — |
| 3 | paul.etonde@gmail.com | Paul | Etonde | buyer | +237 691 234 567 | Yaoundé | — |
| 4 | claire.mbah@gmail.com | Claire | Mbah | buyer | +237 652 345 678 | Buea | — |
| 5 | eric.tabi@sonichub.cm | Eric | Tabi | vendor | +237 677 500 100 | Douala | ✓ |
| 6 | adele.fonkou@gmail.com | Adèle | Fonkou | vendor | +237 691 500 200 | Yaoundé | ✓ |
| 7 | jeanpaul.nkeng@gmail.com | Jean-Paul | Nkeng | vendor | +237 653 500 300 | Kribi | ✓ |
| 8 | sophie.abouem@gmail.com | Sophie | Abouem | vendor | +237 677 500 400 | Douala | ✓ |
| 9 | ndeh.wirba@gmail.com | Ndeh | Wirba | vendor | +237 691 500 500 | Bamenda | ✓ |
| 10 | victor.ngum@gmail.com | Victor | Ngum | vendor | +237 652 500 600 | Buea | — |
| 11 | pulsetech.yde@gmail.com | Romuald | Kom | vendor | +237 677 500 700 | Yaoundé | — |
| 12 | ecocharge.dla@gmail.com | Grace | Neba | vendor | +237 691 500 800 | Douala | ✓ |
| 13 | moses.che@grabit.cm | Moses | Che | agent | +237 677 700 001 | Douala | ✓ |
| 14 | diane.fokam@grabit.cm | Diane | Fokam | agent | +237 691 700 002 | Yaoundé | ✓ |

---

## 2. ADDRESSES

| User | Label | Street Line | City | Primary |
|------|-------|-------------|------|---------|
| Amina Nji (#2) | Home | Rue Njo Njo, Akwa | Douala | ✓ |
| Amina Nji (#2) | Office | Immeuble Wouri, Bonapriso | Douala | — |
| Paul Etonde (#3) | Home | Quartier Bastos, Av. Foch | Yaoundé | ✓ |
| Claire Mbah (#4) | Home | Mile 17, Bonduma | Buea | ✓ |

---

## 3. SHOPS (8 shops)

| # | Name | Handle | Owner | Category | City | Neighbourhood | Plan | Status | Verified |
|---|------|--------|-------|----------|------|---------------|------|--------|---------|
| 1 | SonicHub Cameroun | sonichub | Eric Tabi | electronics | Douala | Akwa | growth | active | ✓ |
| 2 | Maison Adèle | maison-adele | Adèle Fonkou | fashion | Yaoundé | Bastos | premium | active | ✓ |
| 3 | Cocoa Coast Co-op | cocoa-coast | Jean-Paul Nkeng | food | Kribi | Centre-ville | starter | active | ✓ |
| 4 | Maison du Café | maison-du-cafe | Sophie Abouem | home | Douala | Bonanjo | growth | active | ✓ |
| 5 | Atelier Ndeh | atelier-ndeh | Ndeh Wirba | fashion | Bamenda | Nkwen | starter | active | ✓ |
| 6 | Mt Cameroon Bikes | mt-cameroon-bikes | Victor Ngum | sports | Buea | Molyko | starter | active | — |
| 7 | PulseTech | pulsetech | Romuald Kom | electronics | Yaoundé | Melen | starter | active | — |
| 8 | EcoCharge | ecocharge | Grace Neba | electronics | Douala | Akwa | growth | active | ✓ |

### Shop Details

| Handle | Tagline | Delivery Fee | Free Ship At | Rating | Followers | Response Time | WhatsApp |
|--------|---------|-------------|-------------|--------|-----------|---------------|----------|
| sonichub | Your sound, delivered fast | 1,500 | 30,000 | 4.80 | 1,240 | < 2 hours | +237 677 500 100 |
| maison-adele | Elegance woven in Cameroon | 2,000 | 50,000 | 4.90 | 2,105 | < 1 hour | +237 691 500 200 |
| cocoa-coast | Farm-to-table cacao & spices | 3,500 | 20,000 | 4.70 | 876 | < 4 hours | +237 653 500 300 |
| maison-du-cafe | Coffee culture in Douala | 1,000 | 40,000 | 4.60 | 654 | < 3 hours | +237 677 500 400 |
| atelier-ndeh | Crafted in the highlands | 2,500 | 25,000 | 4.50 | 412 | < 6 hours | +237 691 500 500 |
| mt-cameroon-bikes | Ride the mountain | 5,000 | 0 | 3.90 | 187 | < 8 hours | +237 652 500 600 |
| pulsetech | Fast tech at fair prices | 1,500 | 35,000 | 3.70 | 93 | < 4 hours | +237 677 500 700 |
| ecocharge | Clean energy, everywhere | 2,000 | 45,000 | 4.75 | 763 | < 2 hours | +237 691 500 800 |

---

## 4. KYC DOCUMENTS (verified shops only)

| Shop | Doc Type | Label | Status |
|------|----------|-------|--------|
| sonichub | identity | National ID Card | approved |
| sonichub | address | Utility bill — ENEO | approved |
| maison-adele | identity | National ID Card | approved |
| maison-adele | business | Business registration (RCCM) | approved |
| cocoa-coast | identity | National ID Card | approved |
| maison-du-cafe | identity | National ID Card | approved |
| maison-du-cafe | business | Business registration (RCCM) | approved |
| atelier-ndeh | identity | National ID Card | approved |
| ecocharge | identity | National ID Card | approved |
| ecocharge | address | Utility bill — CAMWATER | approved |
| mt-cameroon-bikes | identity | National ID Card | pending |
| pulsetech | identity | National ID Card | not_submitted |

---

## 5. PRODUCTS (16 products — 2 per shop)

| # | Name | Shop | Category | Condition | Price (XAF) | Stock | Status | Premium |
|---|------|------|----------|-----------|-------------|-------|--------|---------|
| 1 | Wireless Noise-Cancelling Headphones | sonichub | electronics | new | 24,500 | 18 | live | ✓ |
| 2 | Smart Fitness Watch | sonichub | electronics | new | 45,000 | 7 | live | — |
| 3 | Ankara Print Wrap Dress | maison-adele | fashion | new | 18,500 | 24 | live | ✓ |
| 4 | Hand-Embroidered Kente Headwrap | maison-adele | fashion | new | 7,500 | 40 | live | — |
| 5 | Organic Cocoa Beans 1kg | cocoa-coast | food | new | 4,500 | 200 | live | — |
| 6 | Single-Origin Cameroon Coffee 500g | cocoa-coast | food | new | 6,000 | 120 | live | ✓ |
| 7 | Compact Espresso Machine | maison-du-cafe | home | new | 65,000 | 5 | live | ✓ |
| 8 | Stainless Steel French Press 600ml | maison-du-cafe | home | new | 14,500 | 22 | live | — |
| 9 | Bamenda Woven Market Bag | atelier-ndeh | fashion | new | 8,500 | 35 | live | — |
| 10 | Leather-Stitched Raffia Clutch | atelier-ndeh | fashion | new | 12,000 | 15 | live | — |
| 11 | Mountain Bike 26" Alloy Frame | mt-cameroon-bikes | sports | new | 195,000 | 3 | live | — |
| 12 | Cycling Helmet & Gloves Set | mt-cameroon-bikes | sports | new | 22,000 | 8 | live | — |
| 13 | Dual-Core Android Tablet 10" | pulsetech | electronics | new | 78,000 | 6 | live | — |
| 14 | USB-C Fast Charging Hub 7-port | pulsetech | electronics | new | 16,500 | 30 | draft | — |
| 15 | Solar Power Bank 30,000mAh | ecocharge | electronics | new | 35,000 | 14 | live | ✓ |
| 16 | Foldable Solar Panel 60W | ecocharge | electronics | new | 89,000 | 9 | live | — |

---

## 6. ORDERS (7 orders — cover all status stages)

| Order ID | Buyer | Shop | Product(s) | Qty | Total (XAF) | Status | Agent | City |
|----------|-------|------|-----------|-----|-------------|--------|-------|------|
| GR-10001 | Amina Nji | sonichub | Headphones ×1 | 1 | 26,000 | completed | Moses Che | Douala |
| GR-10002 | Amina Nji | maison-adele | Ankara Dress ×1 | 1 | 20,500 | delivered_confirm | — | Douala |
| GR-10003 | Paul Etonde | cocoa-coast | Cocoa Beans ×2 | 2 | 12,500 | in_transit | Diane Fokam | Yaoundé |
| GR-10004 | Claire Mbah | sonichub | Smart Watch ×1 | 1 | 46,500 | preparing | — | Buea |
| GR-10005 | Paul Etonde | mt-cameroon-bikes | Mountain Bike ×1 | 1 | 200,000 | awaiting_payment | — | Yaoundé |
| GR-10006 | Amina Nji | ecocharge | Solar Power Bank ×1 | 1 | 37,000 | paid_escrow | — | Douala |
| GR-10007 | Claire Mbah | maison-du-cafe | French Press ×1 + Espresso Machine ×1 | 2 | 81,500 | disputed | Moses Che | Buea |

> Totals include delivery fee from each shop

### Order Delivery Addresses

| Order | Address |
|-------|---------|
| GR-10001 | Rue Njo Njo, Akwa, Douala |
| GR-10002 | Rue Njo Njo, Akwa, Douala |
| GR-10003 | Quartier Bastos, Av. Foch, Yaoundé |
| GR-10004 | Mile 17, Bonduma, Buea |
| GR-10005 | Quartier Bastos, Av. Foch, Yaoundé |
| GR-10006 | Immeuble Wouri, Bonapriso, Douala |
| GR-10007 | Mile 17, Bonduma, Buea |

---

## 7. PAYMENTS (6 payments — GR-10005 is unpaid)

| Payment ID | Order | Method | Amount (XAF) | Phone | Status | External Ref |
|-----------|-------|--------|-------------|-------|--------|-------------|
| PAY-1000 | GR-10001 | mtn_momo | 26,000 | +237 677 123 456 | paid | MTN-20240112-001 |
| PAY-1001 | GR-10002 | orange_money | 20,500 | +237 677 123 456 | paid | OM-20240114-002 |
| PAY-1002 | GR-10003 | mtn_momo | 12,500 | +237 691 234 567 | paid | MTN-20240115-003 |
| PAY-1003 | GR-10004 | mtn_momo | 46,500 | +237 652 345 678 | paid | MTN-20240116-004 |
| PAY-1004 | GR-10006 | orange_money | 37,000 | +237 677 123 456 | paid | OM-20240117-005 |
| PAY-1005 | GR-10007 | bank_transfer | 81,500 | — | paid | BANK-20240118-006 |

---

## 8. ESCROW EVENTS

| Order | Event | Amount (XAF) | Note |
|-------|-------|-------------|------|
| GR-10001 | held | 26,000 | Funds held at payment |
| GR-10001 | released | 26,000 | Buyer confirmed delivery |
| GR-10002 | held | 20,500 | Funds held at payment |
| GR-10003 | held | 12,500 | Funds held at payment |
| GR-10004 | held | 46,500 | Funds held at payment |
| GR-10006 | held | 37,000 | Funds held at payment |
| GR-10007 | held | 81,500 | Funds held at payment |

---

## 9. REVIEWS (6 reviews)

| Product | Reviewer | Rating | Text | Verified Purchase |
|---------|----------|--------|------|------------------|
| Wireless Headphones | Amina Nji | 5 | "Incredible sound isolation! Arrived well-packaged and 2 hours early. SonicHub is now my go-to." | ✓ |
| Smart Watch | Paul Etonde | 4 | "Great watch for the price, accurate heart rate. Strap is a bit rough but does the job." | — |
| Ankara Dress | Claire Mbah | 5 | "Maison Adèle never disappoints. The fabric quality is top-tier — every compliment I get, I send people here." | — |
| Cocoa Beans | Amina Nji | 5 | "These cocoa beans smell like the rainforest. Perfect for hot chocolate season." | ✓ |
| Espresso Machine | Paul Etonde | 4 | "Solid machine for home use. Took a week to deliver to Yaoundé but worth the wait." | — |
| Solar Power Bank | Claire Mbah | 5 | "Light-out hero! Charged my phone and laptop 3× during that outage last month." | ✓ |

---

## 10. DISPUTE (1 open dispute)

| Dispute ID | Order | Opened By | Reason | Status | Description |
|-----------|-------|-----------|--------|--------|-------------|
| DSP-300 | GR-10007 | Claire Mbah | wrong_item | in_review | "I ordered a French Press and Espresso Machine but received a drip coffee maker and a mug. The items are not what was listed. Please review my order and arrange a pick-up for the wrong items." |

---

## 11. MESSAGES (2 threads)

### Thread 1: Amina → SonicHub (Order GR-10001)
| Sender | Recipient | Body | Order |
|--------|-----------|------|-------|
| Amina Nji | Eric Tabi | "Hi, can you confirm dispatch for my headphones order?" | GR-10001 |
| Eric Tabi | Amina Nji | "Hi Amina! Yes, your order is packed and ready. Agent Moses will pick up in ~1 hour." | GR-10001 |
| Amina Nji | Eric Tabi | "Great, thank you! 🙏" | GR-10001 |

### Thread 2: Claire → Maison du Café (Order GR-10007, disputed)
| Sender | Recipient | Body | Order |
|--------|-----------|------|-------|
| Claire Mbah | Sophie Abouem | "Hi, I received the wrong items. This is not what I ordered at all." | GR-10007 |
| Sophie Abouem | Claire Mbah | "I'm really sorry, Claire. Let me check with the warehouse immediately." | GR-10007 |
| Claire Mbah | Sophie Abouem | "I've raised a formal dispute. Please resolve quickly." | GR-10007 |

---

## 12. PAYOUTS (3 vendor payouts)

| Payout ID | Recipient | Method | Amount (XAF) | Status | Payout Date |
|----------|-----------|--------|-------------|--------|-------------|
| PO-1 | Eric Tabi (sonichub) | mtn_momo | 24,700 | paid | 2026-05-10 |
| PO-2 | Adèle Fonkou (maison-adele) | orange_money | 18,880 | paid | 2026-05-10 |
| PO-3 | Jean-Paul Nkeng (cocoa-coast) | mtn_momo | 11,875 | processing | 2026-05-24 |

> After platform commission (5% starter, 3.5% growth, 2.8% premium)

---

## 13. NOTIFICATIONS (per user sample)

| User | Type | Title | Body |
|------|------|-------|------|
| Amina Nji | order | Order GR-10001 completed | Your order from SonicHub has been completed. Escrow released. |
| Amina Nji | delivery | Agent assigned to GR-10002 | Moses Che will deliver your Maison Adèle order today. |
| Amina Nji | price | Price drop on Solar Power Bank | EcoCharge dropped the price from 40,000 to 35,000 XAF! |
| Paul Etonde | order | Order GR-10003 in transit | Diane Fokam is on the way with your cocoa beans. |
| Paul Etonde | shop | Cocoa Coast posted new items | Cameroon single-origin coffee is back in stock. |
| Claire Mbah | dispute | Dispute DSP-300 under review | Our team is reviewing your dispute. Expect a response in 24 hours. |
| Claire Mbah | order | Order GR-10007 disputed | Your order has been flagged. Escrow funds are held until resolved. |
| Eric Tabi | order | New order received — GR-10004 | Claire Mbah ordered a Smart Fitness Watch. Prepare for pickup. |
| Eric Tabi | system | Payout PO-1 sent | 24,700 XAF has been sent to your MTN MoMo account. |
| Moses Che | delivery | New pickup assignment | Pick up GR-10003 from Cocoa Coast Co-op in Kribi. |

---

## 14. SHOP FOLLOWS

| Follower | Shop |
|----------|------|
| Amina Nji | sonichub |
| Amina Nji | maison-adele |
| Amina Nji | ecocharge |
| Paul Etonde | cocoa-coast |
| Paul Etonde | maison-du-cafe |
| Claire Mbah | atelier-ndeh |
| Claire Mbah | ecocharge |

---

## 15. WISHLIST ITEMS

| User | Product |
|------|---------|
| Amina Nji | Solar Power Bank 30,000mAh |
| Amina Nji | Mountain Bike 26" |
| Paul Etonde | Smart Fitness Watch |
| Claire Mbah | Wireless Headphones |

---

## Summary

| Entity | Count |
|--------|-------|
| Users | 14 (1 admin, 3 buyers, 8 vendors, 2 agents) |
| Addresses | 4 |
| Shops | 8 |
| KYC Documents | 12 |
| Products | 16 |
| Orders | 7 |
| Order Items | 9 (multi-item on GR-10007) |
| Payments | 6 |
| Escrow Events | 8 |
| Reviews | 6 |
| Disputes | 1 |
| Messages | 6 |
| Payouts | 3 |
| Notifications | 10 |
| Shop Follows | 7 |
| Wishlist Items | 4 |

---

## Quick-Login Reference Card

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Admin | admin@grabit.cm | Grabit2024! | Full console access |
| Buyer | amina.nji@gmail.com | Grabit2024! | Has orders, wishlist, follows |
| Buyer | paul.etonde@gmail.com | Grabit2024! | Active in-transit order |
| Buyer | claire.mbah@gmail.com | Grabit2024! | Has open dispute |
| Vendor | eric.tabi@sonichub.cm | Grabit2024! | Verified, paid out, active |
| Vendor | adele.fonkou@gmail.com | Grabit2024! | Premium plan, verified |
| Vendor | sophie.abouem@gmail.com | Grabit2024! | Order under dispute |
| Agent | moses.che@grabit.cm | Grabit2024! | Completed + active deliveries |
