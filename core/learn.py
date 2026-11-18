# =====================================================
# learn.py — เนื้อหาของหน้า "ความรู้การลงทุน" (2 ภาษา: ลาว / อังกฤษ)
#   TOPICS     5 หมวด หมวดละ 3 บทเรียนสั้น
#   RED_FLAGS  สัญญาณเตือนการหลอกลวง (ใช้ในแบบตรวจสอบ)
#   GLOSSARY   อภิธานศัพท์
#   compound() คำนวณการเติบโตแบบดอกเบี้ยทบต้น
# อยากแก้/เพิ่มเนื้อหา → แก้ในไฟล์นี้ที่เดียว (เขียนเนื้อหาด้วย Markdown ได้)
# =====================================================

# หมวด: key = ชื่อหมวด, icon = ไอคอนบนแท็บ, link = หน้าที่ให้ลองใช้จริง (หรือ None)
TOPICS = [
    {"key": "basics", "icon": ":material/school:", "link": None,
     "title": {"lo": "ພື້ນຖານ", "en": "Basics"},
     "lessons": [
         {"title": {"lo": "ຮຸ້ນແມ່ນຫຍັງ?", "en": "What is a stock?"},
          "body": {"lo": "ຮຸ້ນແມ່ນສ່ວນແບ່ງຄວາມເປັນເຈົ້າຂອງໃນບໍລິສັດ. ເມື່ອທ່ານຖືຮຸ້ນ ທ່ານເປັນເຈົ້າຂອງສ່ວນໜຶ່ງຂອງທຸລະກິດນັ້ນ.\n\n"
                         "- **ກຳໄລຈາກລາຄາ**: ລາຄາຮຸ້ນຂຶ້ນ ເມື່ອທຸລະກິດເຕີບໂຕ ຫຼື ມີຄົນຕ້ອງການຊື້ຫຼາຍຂຶ້ນ.\n"
                         "- **ເງິນປັນຜົນ**: ບາງບໍລິສັດແບ່ງກຳໄລສ່ວນໜຶ່ງໃຫ້ຜູ້ຖືຮຸ້ນ.\n"
                         "- **ຄວາມສ່ຽງ**: ລາຄາຫຼຸດລົງໄດ້ເຊັ່ນກັນ ແລະ ທ່ານອາດຂາດທຶນ.",
                   "en": "A stock is a small share of ownership in a company. When you hold it, you own part of that business.\n\n"
                         "- **Price gain**: the share price rises when the business grows or more people want to buy it.\n"
                         "- **Dividend**: some companies pay part of their profit to shareholders.\n"
                         "- **Risk**: the price can fall too, and you can lose money."},
          "tip": {"lo": "ທ່ານກຳລັງຊື້ທຸລະກິດ ບໍ່ແມ່ນຕົວເລກໃນໜ້າຈໍ.", "en": "You are buying a business, not a number on a screen."}},
         {"title": {"lo": "ຄວາມສ່ຽງ ແລະ ຜົນຕອບແທນ", "en": "Risk and return"},
          "body": {"lo": "ຜົນຕອບແທນທີ່ສູງຂຶ້ນ ມາພ້ອມກັບຄວາມສ່ຽງທີ່ສູງຂຶ້ນສະເໝີ.\n\n"
                         "- **ເງິນຝາກ**: ສ່ຽງຕ່ຳ, ຜົນຕອບແທນຕ່ຳ.\n"
                         "- **ພັນທະບັດ**: ສ່ຽງປານກາງ, ຜົນຕອບແທນປານກາງ.\n"
                         "- **ຮຸ້ນ**: ສ່ຽງສູງ, ໂອກາດໄດ້ຜົນຕອບແທນສູງໃນໄລຍະຍາວ.\n\n"
                         "ບໍ່ມີການລົງທຶນໃດທີ່ໃຫ້ຜົນຕອບແທນສູງ ໂດຍບໍ່ມີຄວາມສ່ຽງ.",
                   "en": "A higher return always comes with higher risk.\n\n"
                         "- **Deposits**: low risk, low return.\n"
                         "- **Bonds**: medium risk, medium return.\n"
                         "- **Stocks**: high risk, with the chance of a high return over the long run.\n\n"
                         "No investment pays a high return with no risk."},
          "tip": {"lo": "ຖ້າມີຄົນສັນຍາວ່າ \"ກຳໄລສູງ ບໍ່ມີຄວາມສ່ຽງ\" ໃຫ້ສົງໄສໄວ້ກ່ອນ.", "en": "If someone promises \"high profit, no risk\", be suspicious first."}},
         {"title": {"lo": "ພະລັງຂອງດອກເບ້ຍທົບຕົ້ນ", "en": "The power of compounding"},
          "body": {"lo": "ດອກເບ້ຍທົບຕົ້ນຄືການທີ່ຜົນຕອບແທນຂອງທ່ານ ສ້າງຜົນຕອບແທນຕໍ່ໄປອີກ. ຍິ່ງປະໄວ້ດົນ ເງິນຍິ່ງເຕີບໂຕໄວຂຶ້ນ.\n\n"
                         "- ເວລາສຳຄັນກວ່າຈຳນວນເງິນ: ເລີ່ມໄວ ດີກວ່າເລີ່ມດ້ວຍເງິນຫຼາຍ.\n"
                         "- ການລົງທຶນສະໝ່ຳສະເໝີທຸກເດືອນ ຊ່ວຍໃຫ້ເງິນສະສົມເຕີບໂຕ.\n\n"
                         "ລອງປ່ຽນຕົວເລກໃນເຄື່ອງຄິດໄລ່ດ້ານລຸ່ມເພື່ອເບິ່ງຜົນ.",
                   "en": "Compounding is when your returns start earning returns of their own. The longer you leave it, the faster it grows.\n\n"
                         "- Time matters more than the amount: starting early beats starting big.\n"
                         "- Investing a steady amount every month keeps the pile growing.\n\n"
                         "Change the numbers in the calculator below to see the effect."},
          "tip": {"lo": "ເວລາຄືເພື່ອນທີ່ດີທີ່ສຸດຂອງນັກລົງທຶນ.", "en": "Time is an investor's best friend."}},
     ]},
    {"key": "value", "icon": ":material/monitoring:", "link": "page_valuation",
     "title": {"lo": "ການປະເມີນມູນຄ່າ", "en": "Valuation"},
     "lessons": [
         {"title": {"lo": "ລາຄາ ບໍ່ແມ່ນ ມູນຄ່າ", "en": "Price is not value"},
          "body": {"lo": "**ລາຄາ** ຄືສິ່ງທີ່ທ່ານຈ່າຍ. **ມູນຄ່າ** ຄືສິ່ງທີ່ທຸລະກິດມີຄ່າແທ້ຈິງ.\n\n"
                         "- ລາຄາປ່ຽນທຸກມື້ຕາມອາລົມຂອງຕະຫຼາດ; ມູນຄ່າປ່ຽນຊ້າກວ່າ ຕາມຜົນປະກອບການ.\n"
                         "- ຊື້ເມື່ອລາຄາຕ່ຳກວ່າມູນຄ່າ ເພື່ອໃຫ້ມີ **ສ່ວນເຜື່ອຄວາມປອດໄພ** (Margin of Safety).\n"
                         "- ໃນໜ້າວິເຄາະຮຸ້ນ ເສັ້ນປະແມ່ນມູນຄ່າທີ່ເໝາະສົມ ແລະ ເສັ້ນທຶບແມ່ນລາຄາ.",
                   "en": "**Price** is what you pay. **Value** is what the business is really worth.\n\n"
                         "- Price moves every day with the market's mood; value changes more slowly, with the company's results.\n"
                         "- Buy when price is below value so you have a **margin of safety**.\n"
                         "- On the Stock Analysis page the dashed line is fair value and the solid line is price."},
          "tip": {"lo": "ບໍລິສັດທີ່ດີ ອາດເປັນການລົງທຶນທີ່ບໍ່ດີ ຖ້າຊື້ໃນລາຄາແພງເກີນໄປ.", "en": "A great company can be a poor investment if you pay too much for it."}},
         {"title": {"lo": "ຕົວເລກທີ່ຄວນຮູ້: EPS, P/E, ROE", "en": "Numbers to know: EPS, P/E, ROE"},
          "body": {"lo": "- **EPS** (ກຳໄລຕໍ່ຮຸ້ນ) = ກຳໄລສຸດທິ ÷ ຈຳນວນຮຸ້ນ. ບອກວ່າຮຸ້ນ 1 ໜ່ວຍສ້າງກຳໄລເທົ່າໃດ.\n"
                         "- **P/E** = ລາຄາ ÷ EPS. ບອກວ່າທ່ານຈ່າຍຈັກເທົ່າຂອງກຳໄລ. ສູງ = ແພງ ຫຼື ຕະຫຼາດຄາດວ່າຈະເຕີບໂຕໄວ.\n"
                         "- **ROE** = ກຳໄລສຸດທິ ÷ ສ່ວນຂອງຜູ້ຖືຮຸ້ນ. ບອກວ່າບໍລິສັດໃຊ້ທຶນໄດ້ເກັ່ງປານໃດ; ສູງກວ່າ 15% ຕໍ່ເນື່ອງ ຖືວ່າດີ.",
                   "en": "- **EPS** (earnings per share) = net profit ÷ number of shares. How much profit one share produces.\n"
                         "- **P/E** = price ÷ EPS. How many times earnings you are paying. High means expensive, or that the market expects fast growth.\n"
                         "- **ROE** = net profit ÷ shareholders' equity. How well the company uses its capital; above 15% year after year is good."},
          "tip": {"lo": "ຢ່າເບິ່ງຕົວເລກດຽວ. ທຽບກັບປີກ່ອນ ແລະ ຄູ່ແຂ່ງໃນອຸດສາຫະກຳດຽວກັນ.", "en": "Never read one number alone. Compare it with past years and with rivals in the same industry."}},
         {"title": {"lo": "ທຸລະກິດທີ່ມີຄຸນນະພາບເປັນແນວໃດ?", "en": "What makes a quality business?"},
          "body": {"lo": "ຄະແນນຄຸນນະພາບໃນແພລັດຟອມນີ້ເບິ່ງ 5 ດ້ານ:\n\n"
                         "1. **ໂອກາດເຕີບໂຕ** — ລາຍຮັບ ແລະ ກຳໄລເພີ່ມຂຶ້ນ.\n"
                         "2. **ຜົນງານຫຼ້າສຸດ** — ປີຫຼ້າສຸດດີກວ່າປີກ່ອນ.\n"
                         "3. **ຄວາມແຂງແກ່ນທາງການເງິນ** — ໜີ້ສິນໜ້ອຍ, ມີເງິນສົດ.\n"
                         "4. **ຜົນຕອບແທນຄືນຜູ້ຖືຮຸ້ນ** — ປັນຜົນ ແລະ ຊື້ຮຸ້ນຄືນ.\n"
                         "5. **ຄວາມໄດ້ປຽບໃນການແຂ່ງຂັນ** — ອັດຕາກຳໄລສູງ ແລະ ສະໝ່ຳສະເໝີ.",
                   "en": "The quality score on this platform looks at five things:\n\n"
                         "1. **Growth opportunity** — revenue and profit are rising.\n"
                         "2. **Recent performance** — the latest year beats the one before.\n"
                         "3. **Financial strength** — little debt, cash to spare.\n"
                         "4. **Return to shareholders** — dividends and share buybacks.\n"
                         "5. **Competitive advantage** — high and steady profit margins."},
          "tip": {"lo": "ຊອກຫາ \"ບໍລິສັດທີ່ດີ ໃນລາຄາທີ່ເໝາະສົມ\".", "en": "Look for a good company at a fair price."}},
     ]},
    {"key": "risk", "icon": ":material/shield:", "link": "page_risk",
     "title": {"lo": "ຄວາມສ່ຽງ", "en": "Risk"},
     "lessons": [
         {"title": {"lo": "ຄວາມຜັນຜວນ", "en": "Volatility"},
          "body": {"lo": "ຄວາມຜັນຜວນບອກວ່າລາຄາແກວ່ງຂຶ້ນລົງແຮງປານໃດ. ຄິດຈາກສ່ວນບ່ຽງເບນມາດຕະຖານຂອງຜົນຕອບແທນ.\n\n"
                         "- ຕ່ຳກວ່າ 20% ຕໍ່ປີ: ຂ້ອນຂ້າງນິ້ງ.\n"
                         "- ສູງກວ່າ 35% ຕໍ່ປີ: ແກວ່ງແຮງ, ຕ້ອງໃຈແຂງ.\n\n"
                         "ຄວາມຜັນຜວນສູງ ບໍ່ໄດ້ແປວ່າບໍ່ດີ ແຕ່ແປວ່າທ່ານຕ້ອງຮັບການຂຶ້ນລົງໄດ້.",
                   "en": "Volatility tells you how hard the price swings up and down. It is the standard deviation of returns.\n\n"
                         "- Below 20% a year: fairly calm.\n"
                         "- Above 35% a year: big swings that take strong nerves.\n\n"
                         "High volatility is not bad in itself, but you must be able to sit through the swings."},
          "tip": {"lo": "ເລືອກຄວາມຜັນຜວນທີ່ທ່ານນອນຫຼັບໄດ້.", "en": "Pick a level of volatility you can sleep with."}},
         {"title": {"lo": "Beta ແລະ ຄວາມສ່ຽງຂອງຕະຫຼາດ", "en": "Beta and market risk"},
          "body": {"lo": "Beta ບອກວ່າຮຸ້ນເໜັງຕີງຈັກເທົ່າຂອງຕະຫຼາດ.\n\n"
                         "- **Beta = 1**: ເໜັງຕີງເທົ່າກັບຕະຫຼາດ.\n"
                         "- **Beta > 1**: ຂຶ້ນລົງແຮງກວ່າຕະຫຼາດ.\n"
                         "- **Beta < 1**: ຂຶ້ນລົງໜ້ອຍກວ່າຕະຫຼາດ.\n\n"
                         "ເມື່ອຕະຫຼາດທັງໝົດຕົກ ຮຸ້ນເກືອບທຸກຕົວກໍ່ຕົກຕາມ. ນີ້ແມ່ນຄວາມສ່ຽງທີ່ການກະຈາຍຮຸ້ນຫຼຸດບໍ່ໄດ້.",
                   "en": "Beta tells you how many times the market's move a stock tends to make.\n\n"
                         "- **Beta = 1**: moves about as much as the market.\n"
                         "- **Beta > 1**: swings harder than the market.\n"
                         "- **Beta < 1**: swings less than the market.\n\n"
                         "When the whole market falls, almost every stock falls with it. Spreading across stocks cannot remove this risk."},
          "tip": {"lo": "ພອດທີ່ມີ Beta ສູງ ຈະຂຶ້ນໄວ ແລະ ລົງໄວເຊັ່ນກັນ.", "en": "A high-beta portfolio rises fast and falls just as fast."}},
         {"title": {"lo": "VaR ແລະ ການຂາດທຶນສູງສຸດ", "en": "VaR and max drawdown"},
          "body": {"lo": "- **VaR 95%**: ການຂາດທຶນຕໍ່ມື້ ທີ່ຈຸດ 5% ຮ້າຍທີ່ສຸດ. ຖ້າ VaR = 2% ແປວ່າ ໃນ 20 ມື້ ຈະມີປະມານ 1 ມື້ທີ່ຂາດທຶນຫຼາຍກວ່າ 2%.\n"
                         "- **ການຂາດທຶນສູງສຸດ** (Max Drawdown): ການຕົກຈາກຈຸດສູງສຸດຫາຈຸດຕ່ຳສຸດທີ່ເລິກທີ່ສຸດໃນອະດີດ.\n\n"
                         "ສອງຕົວເລກນີ້ຊ່ວຍຕອບຄຳຖາມວ່າ \"ຖ້າໂຊກບໍ່ດີ ຂ້ອຍຈະເສຍເທົ່າໃດ?\"",
                   "en": "- **VaR 95%**: the daily loss at the worst 5% point. A VaR of 2% means that on about 1 day in 20 you lose more than 2%.\n"
                         "- **Max drawdown**: the deepest fall from a peak to the following low in the past.\n\n"
                         "Both numbers help answer the question: \"If I am unlucky, how much do I lose?\""},
          "tip": {"lo": "ກ່ອນຊື້ ຖາມຕົນເອງວ່າ ຖ້າຮຸ້ນນີ້ຕົກເທົ່າກັບການຂາດທຶນສູງສຸດ ທ່ານຈະຍັງຖືຢູ່ບໍ່?", "en": "Before buying, ask yourself: if this stock fell by its max drawdown again, would you still hold it?"}},
     ]},
    {"key": "port", "icon": ":material/pie_chart:", "link": "page_portfolio",
     "title": {"lo": "ການຈັດພອດ", "en": "Portfolio"},
     "lessons": [
         {"title": {"lo": "ການກະຈາຍຄວາມສ່ຽງ", "en": "Diversification"},
          "body": {"lo": "\"ຢ່າເອົາໄຂ່ທັງໝົດໃສ່ກະຕ່າໃບດຽວ.\" ການຖືຫຼາຍຮຸ້ນ ຫຼາຍອຸດສາຫະກຳ ຊ່ວຍຫຼຸດຜົນກະທົບເມື່ອຕົວໃດຕົວໜຶ່ງຕົກ.\n\n"
                         "- ຮຸ້ນທີ່ເໜັງຕີງບໍ່ຄືກັນ ຊ່ວຍໃຫ້ພອດນິ້ງຂຶ້ນ.\n"
                         "- ຖືຮຸ້ນ 10 ຕົວໃນອຸດສາຫະກຳດຽວ ຍັງບໍ່ຖືວ່າກະຈາຍ.",
                   "en": "\"Don't put all your eggs in one basket.\" Holding several stocks across industries softens the blow when one of them falls.\n\n"
                         "- Stocks that do not move together make the portfolio calmer.\n"
                         "- Ten stocks in one industry is still not diversified."},
          "tip": {"lo": "ການກະຈາຍຄວາມສ່ຽງ ຫຼຸດຄວາມສ່ຽງໄດ້ ໂດຍບໍ່ຈຳເປັນຕ້ອງຫຼຸດຜົນຕອບແທນ.", "en": "Diversifying can cut risk without having to cut return."}},
         {"title": {"lo": "ການຈັດສັນຊັບສິນ", "en": "Asset allocation"},
          "body": {"lo": "ການຈັດສັນຊັບສິນຄືການແບ່ງເງິນລະຫວ່າງ ເງິນຝາກ, ພັນທະບັດ, ຮຸ້ນ ແລະ ຊັບສິນທາງເລືອກ.\n\n"
                         "- ສັດສ່ວນນີ້ມີຜົນຕໍ່ຜົນຕອບແທນ ແລະ ຄວາມສ່ຽງ ຫຼາຍກວ່າການເລືອກຮຸ້ນລາຍຕົວ.\n"
                         "- ຄົນທີ່ຮັບຄວາມສ່ຽງໄດ້ໜ້ອຍ ຄວນຖືຮຸ້ນໜ້ອຍລົງ ແລະ ເງິນຝາກ/ພັນທະບັດຫຼາຍຂຶ້ນ.\n\n"
                         "ເຮັດແບບປະເມີນຜູ້ລົງທຶນເພື່ອຮູ້ສັດສ່ວນທີ່ເໝາະກັບທ່ານ.",
                   "en": "Asset allocation is how you split money between deposits, bonds, stocks and alternatives.\n\n"
                         "- This split affects your return and risk more than which individual stocks you pick.\n"
                         "- Someone who can take little risk should hold fewer stocks and more deposits and bonds.\n\n"
                         "Take the investor assessment to find the split that fits you."},
          "tip": {"lo": "ຮູ້ຈັກຕົນເອງກ່ອນ ແລ້ວຈຶ່ງເລືອກຊັບສິນ.", "en": "Know yourself first, then choose the assets."}},
         {"title": {"lo": "ລົງທຶນສະໝ່ຳສະເໝີ ແລະ ປັບພອດ", "en": "Regular investing and rebalancing"},
          "body": {"lo": "- **DCA** (ລົງທຶນແບບສະເລ່ຍຕົ້ນທຶນ): ລົງທຶນຈຳນວນເທົ່າກັນທຸກເດືອນ ບໍ່ວ່າລາຄາຈະຂຶ້ນຫຼືລົງ. ຊ່ວຍຫຼຸດຄວາມສ່ຽງຈາກການຊື້ຜິດຈັງຫວະ.\n"
                         "- **ການປັບພອດ** (Rebalancing): ປີລະ 1–2 ຄັ້ງ ປັບສັດສ່ວນກັບຄືນສູ່ເປົ້າໝາຍ ໂດຍຂາຍສ່ວນທີ່ຂຶ້ນຫຼາຍ ແລະ ຊື້ສ່ວນທີ່ຫຼຸດ.",
                   "en": "- **DCA** (dollar-cost averaging): invest the same amount every month whether prices are up or down. It reduces the risk of buying at the wrong moment.\n"
                         "- **Rebalancing**: once or twice a year, bring the split back to your target by selling what has grown most and buying what has fallen."},
          "tip": {"lo": "ວິໄນສຳຄັນກວ່າການຄາດເດົາຕະຫຼາດ.", "en": "Discipline beats trying to guess the market."}},
     ]},
    {"key": "scam", "icon": ":material/gpp_maybe:", "link": None,
     "title": {"lo": "ລະວັງການຫຼອກລວງ", "en": "Scams"},
     "lessons": [
         {"title": {"lo": "ຮູບແບບການຫຼອກລວງທີ່ພົບເລື້ອຍ", "en": "Common investment scams"},
          "body": {"lo": "- **ແຊຣ໌ລູກໂສ້ / Ponzi**: ເອົາເງິນຂອງຄົນໃໝ່ມາຈ່າຍໃຫ້ຄົນເກົ່າ. ພັງເມື່ອບໍ່ມີຄົນໃໝ່ເຂົ້າມາ.\n"
                         "- **ໂບຣກເກີ ຫຼື ແອັບປອມ**: ໜ້າຈໍສະແດງກຳໄລ ແຕ່ຖອນເງິນບໍ່ໄດ້.\n"
                         "- **ກຸ່ມປັ່ນລາຄາ**: ຊວນຊື້ຮຸ້ນ ຫຼື ຫຼຽນ ຕົວໃດໜຶ່ງພ້ອມກັນ ແລ້ວຜູ້ຊວນຂາຍໃສ່ທ່ານ.\n"
                         "- **Forex / ຄຣິບໂຕ ຮັບປະກັນກຳໄລ**: ອ້າງວ່າມີລະບົບ ຫຼື ຜູ້ຊ່ຽວຊານເທຣດແທນ.",
                   "en": "- **Ponzi and pyramid schemes**: new members' money pays the earlier ones. It collapses when new money stops.\n"
                         "- **Fake brokers and apps**: the screen shows profit, but you cannot withdraw.\n"
                         "- **Pump-and-dump groups**: everyone is urged to buy one stock or coin together, then the promoters sell to you.\n"
                         "- **\"Guaranteed\" forex or crypto**: claims of a system or an expert who trades for you."},
          "tip": {"lo": "ຖ້າຟັງແລ້ວດີເກີນຈິງ ມັນມັກຈະບໍ່ຈິງ.", "en": "If it sounds too good to be true, it usually is."}},
         {"title": {"lo": "ກວດສອບກ່ອນໂອນເງິນ", "en": "Check before you send money"},
          "body": {"lo": "1. ກວດວ່າບໍລິສັດ ຫຼື ບຸກຄົນນັ້ນ **ມີໃບອະນຸຍາດ** ຈາກໜ່ວຍງານຄຸ້ມຄອງຫຼັກຊັບຂອງປະເທດ (ໃນ ສປປ ລາວ: ສຳນັກງານຄະນະກຳມະການຄຸ້ມຄອງຫຼັກຊັບ).\n"
                         "2. ຖາມວ່າ **ກຳໄລມາຈາກໃສ**. ຖ້າອະທິບາຍບໍ່ໄດ້ ຢ່າລົງທຶນ.\n"
                         "3. **ຢ່າໂອນເງິນເຂົ້າບັນຊີສ່ວນຕົວ** ຂອງບຸກຄົນ.\n"
                         "4. ທົດລອງ **ຖອນເງິນຈຳນວນໜ້ອຍ** ກ່ອນເພີ່ມເງິນ.\n"
                         "5. ປຶກສາຄົນທີ່ໄວ້ໃຈໄດ້ ແລະ ຢ່າຟ້າວຕັດສິນໃຈ.",
                   "en": "1. Check that the company or person is **licensed** by your country's securities regulator (in Laos, the Lao Securities Commission Office).\n"
                         "2. Ask **where the profit comes from**. If they cannot explain it, do not invest.\n"
                         "3. **Never transfer to an individual's personal account.**\n"
                         "4. Try **withdrawing a small amount** before adding more.\n"
                         "5. Talk to someone you trust, and do not rush."},
          "tip": {"lo": "ການລົງທຶນທີ່ແທ້ຈິງ ບໍ່ເຄີຍບັງຄັບໃຫ້ທ່ານຕັດສິນໃຈພາຍໃນມື້ນີ້.", "en": "A real investment never forces you to decide today."}},
         {"title": {"lo": "ຖ້າຖືກຫຼອກແລ້ວ ຄວນເຮັດແນວໃດ?", "en": "What to do if you were scammed"},
          "body": {"lo": "1. **ຢຸດໂອນເງິນທັນທີ** — ຢ່າຈ່າຍ \"ຄ່າທຳນຽມ\" ເພື່ອຖອນເງິນຄືນ.\n"
                         "2. **ເກັບຫຼັກຖານ**: ຂໍ້ຄວາມ, ໃບໂອນເງິນ, ຊື່ບັນຊີ, ລິ້ງເວັບໄຊ.\n"
                         "3. **ແຈ້ງທະນາຄານ** ຂອງທ່ານໃຫ້ໄວທີ່ສຸດ ເພື່ອຂໍອາຍັດການໂອນ.\n"
                         "4. **ແຈ້ງຄວາມກັບເຈົ້າໜ້າທີ່ຕຳຫຼວດ**.\n"
                         "5. ລະວັງຜູ້ທີ່ອ້າງວ່າ \"ຊ່ວຍເອົາເງິນຄືນໄດ້\" — ມັກເປັນການຫຼອກຊ້ຳສອງ.",
                   "en": "1. **Stop sending money at once** — do not pay a \"fee\" to get your money back.\n"
                         "2. **Keep the evidence**: messages, transfer slips, account names, website links.\n"
                         "3. **Tell your bank** as fast as you can and ask them to freeze the transfer.\n"
                         "4. **Report it to the police.**\n"
                         "5. Beware of anyone who says they can \"recover your money\" — that is often a second scam."},
          "tip": {"lo": "ການແຈ້ງໄວ ເພີ່ມໂອກາດໄດ້ເງິນຄືນ ແລະ ຊ່ວຍປ້ອງກັນຄົນອື່ນ.", "en": "Reporting quickly raises the chance of recovery and protects other people."}},
     ]},
]

# สัญญาณเตือนการหลอกลวง — ติ๊กยิ่งมาก ยิ่งเสี่ยง
RED_FLAGS = [
    {"lo": "ຮັບປະກັນຜົນຕອບແທນ ຫຼື ສັນຍາກຳໄລສູງຜິດປົກກະຕິ (ເຊັ່ນ ຫຼາຍ % ຕໍ່ເດືອນ)", "en": "Guaranteed returns, or unusually high profit (such as several % a month)"},
    {"lo": "ເລັ່ງໃຫ້ຕັດສິນໃຈໄວ ຫຼື ອ້າງວ່າ \"ເຫຼືອບ່ອນຈຳກັດ\"", "en": "Pressure to decide fast, or \"only a few places left\""},
    {"lo": "ໄດ້ຄ່າຕອບແທນເມື່ອຊວນຄົນອື່ນມາຮ່ວມ", "en": "You are paid for recruiting other people"},
    {"lo": "ອະທິບາຍບໍ່ໄດ້ຊັດເຈນວ່າກຳໄລມາຈາກໃສ", "en": "They cannot clearly explain where the profit comes from"},
    {"lo": "ບໍ່ມີໃບອະນຸຍາດຈາກໜ່ວຍງານຄຸ້ມຄອງ ຫຼື ກວດສອບບໍ່ໄດ້", "en": "No licence from a regulator, or none you can verify"},
    {"lo": "ໃຫ້ໂອນເງິນເຂົ້າບັນຊີສ່ວນຕົວ ຫຼື ຜ່ານຄຣິບໂຕເທົ່ານັ້ນ", "en": "Money goes to a personal account, or by crypto only"},
    {"lo": "ຄົນແປກໜ້າຕິດຕໍ່ມາກ່ອນ ຜ່ານສື່ສັງຄົມ ຫຼື ແຊັດ", "en": "A stranger contacted you first on social media or chat"},
    {"lo": "ຖອນເງິນຍາກ ຫຼື ຕ້ອງຈ່າຍ \"ຄ່າທຳນຽມ\" ເພີ່ມກ່ອນຖອນ", "en": "Withdrawals are difficult, or need an extra \"fee\" first"},
]

GLOSSARY = [
    ("Stock", {"lo": "ຮຸ້ນ — ສ່ວນແບ່ງຄວາມເປັນເຈົ້າຂອງໃນບໍລິສັດ.", "en": "A share of ownership in a company."}),
    ("Bond", {"lo": "ພັນທະບັດ — ການໃຫ້ລັດຖະບານ ຫຼື ບໍລິສັດກູ້ຢືມເງິນ ເພື່ອຮັບດອກເບ້ຍ.", "en": "A loan to a government or company that pays you interest."}),
    ("Dividend", {"lo": "ເງິນປັນຜົນ — ກຳໄລທີ່ບໍລິສັດແບ່ງຈ່າຍໃຫ້ຜູ້ຖືຮຸ້ນ.", "en": "Profit a company pays out to its shareholders."}),
    ("Market cap", {"lo": "ມູນຄ່າຕະຫຼາດ — ລາຄາຮຸ້ນ × ຈຳນວນຮຸ້ນທັງໝົດ.", "en": "Share price × total number of shares."}),
    ("EPS", {"lo": "ກຳໄລຕໍ່ຮຸ້ນ — ກຳໄລສຸດທິ ÷ ຈຳນວນຮຸ້ນ.", "en": "Earnings per share: net profit ÷ number of shares."}),
    ("P/E", {"lo": "ລາຄາຕໍ່ກຳໄລ — ລາຄາຮຸ້ນ ÷ EPS.", "en": "Price-to-earnings: share price ÷ EPS."}),
    ("P/BV", {"lo": "ລາຄາຕໍ່ມູນຄ່າທາງບັນຊີ — ລາຄາຮຸ້ນ ÷ ມູນຄ່າທາງບັນຊີຕໍ່ຮຸ້ນ.", "en": "Price-to-book: share price ÷ book value per share."}),
    ("ROE", {"lo": "ຜົນຕອບແທນຕໍ່ສ່ວນຂອງຜູ້ຖືຮຸ້ນ — ກຳໄລສຸດທິ ÷ ສ່ວນຂອງຜູ້ຖືຮຸ້ນ.", "en": "Return on equity: net profit ÷ shareholders' equity."}),
    ("D/E", {"lo": "ໜີ້ສິນຕໍ່ທຶນ — ໜີ້ສິນລວມ ÷ ສ່ວນຂອງຜູ້ຖືຮຸ້ນ.", "en": "Debt-to-equity: total debt ÷ shareholders' equity."}),
    ("Free cash flow", {"lo": "ກະແສເງິນສົດອິດສະຫຼະ — ເງິນສົດຈາກການດຳເນີນງານ ຫັກລາຍຈ່າຍລົງທຶນ.", "en": "Cash from operations minus capital spending."}),
    ("Fair value", {"lo": "ມູນຄ່າທີ່ເໝາະສົມ — ຄ່າປະເມີນວ່າຮຸ້ນຄວນມີລາຄາເທົ່າໃດ.", "en": "An estimate of what a share should be worth."}),
    ("Margin of safety", {"lo": "ສ່ວນເຜື່ອຄວາມປອດໄພ — ສ່ວນຕ່າງເມື່ອຊື້ໃນລາຄາຕ່ຳກວ່າມູນຄ່າ.", "en": "The cushion you get by buying below fair value."}),
    ("Volatility", {"lo": "ຄວາມຜັນຜວນ — ລະດັບການແກວ່ງຂຶ້ນລົງຂອງລາຄາ.", "en": "How much the price swings up and down."}),
    ("Beta", {"lo": "ຄ່າທີ່ບອກວ່າຮຸ້ນເໜັງຕີງຈັກເທົ່າຂອງຕະຫຼາດ.", "en": "How many times the market's move a stock tends to make."}),
    ("VaR", {"lo": "Value at Risk — ການຂາດທຶນທີ່ອາດເກີດ ໃນລະດັບຄວາມເຊື່ອໝັ້ນທີ່ກຳນົດ.", "en": "Value at Risk: the loss you might see at a chosen confidence level."}),
    ("Max drawdown", {"lo": "ການຂາດທຶນສູງສຸດ — ການຕົກຈາກຈຸດສູງສຸດຫາຈຸດຕ່ຳສຸດທີ່ເລິກທີ່ສຸດ.", "en": "The deepest fall from a peak to the following low."}),
    ("Sharpe ratio", {"lo": "ຜົນຕອບແທນສ່ວນເກີນ ຕໍ່ຄວາມສ່ຽງ 1 ໜ່ວຍ.", "en": "Extra return earned per unit of risk."}),
    ("Diversification", {"lo": "ການກະຈາຍຄວາມສ່ຽງ — ຖືຊັບສິນຫຼາຍຢ່າງເພື່ອຫຼຸດຄວາມສ່ຽງ.", "en": "Holding many assets to reduce risk."}),
    ("Asset allocation", {"lo": "ການຈັດສັນຊັບສິນ — ການແບ່ງເງິນລະຫວ່າງປະເພດຊັບສິນ.", "en": "How money is split between types of assets."}),
    ("DCA", {"lo": "ລົງທຶນແບບສະເລ່ຍຕົ້ນທຶນ — ລົງທຶນຈຳນວນເທົ່າກັນເປັນປະຈຳ.", "en": "Dollar-cost averaging: investing the same amount at regular intervals."}),
]


def compound(initial: float, monthly: float, years: int, rate: float) -> list:
    """ดอกเบี้ยทบต้นรายเดือน: ยอดเงิน = ยอดเดิม × (1 + อัตราต่อปี ÷ 12) + เงินที่ใส่เพิ่มรายเดือน
    คืนค่ารายปี: [(ปีที่, เงินที่ใส่สะสม, ยอดเงินรวม)]  เริ่มที่ปี 0"""
    balance, paid, out = float(initial), float(initial), [(0, float(initial), float(initial))]
    for month in range(1, years * 12 + 1):
        balance = balance * (1 + rate / 12) + monthly
        paid += monthly
        if month % 12 == 0:
            out.append((month // 12, paid, balance))
    return out
