# Procurement lead interview
Client: Acme
Subject: procure-to-pay
Interview date: 2026-10-14
Interviewee: Dana Okonkwo, procurement lead
Interviewer: Analyst
Location: Mill Road office

Analyst: The brief says spend on procure-to-pay is too high. I want the work as it is
done this week.

Dana Okonkwo: I lead procurement. Tess Harp and Ivo Marsh are the buyers. About 80
suppliers are active. About 220 invoices a week is the volume the clerks quote, and it
matches what I see leaving Gatepass.

Analyst: How does a purchase order start?

Dana Okonkwo: A buyer types it in Gatepass after a request by mail. There is no
requisition screen. The screen does not know whether the goods have already arrived.
Sometimes they have.

Analyst: Tell me about PO-19002.

Dana Okonkwo: Yellow Dock Components, supplier S-3301, had already delivered. Tess
raised PO-19002 on 2026-04-07 for 12750.00 dollars. Invoice INV-3301-019 was matched the
next day. Helpline HLP-4704. Raising the order after delivery is outside the rule, and
it still happens.

Analyst: The Bramble Tin supplier record.

Dana Okonkwo: Two codes are active for one legal entity, S-1044 and S-1044B. Helpline
HLP-4820 opened on 2026-05-14. A buyer can pick the wrong code. I have not closed
S-1044B.

Analyst: Have duplicate payments stopped?

Dana Okonkwo: We have had zero duplicate payments in the last twelve months.

Analyst: Which report shows that?

Dana Okonkwo: I am not looking at a report. The buyers would have told me. I do not read
Helpline. The clerks are supposed to search for an invoice number before they propose
payment.

Analyst: How does a supplier send an invoice?

Dana Okonkwo: They email invoices@acme.example. There is no portal. In August a supplier
asked where to submit one online. Tess answered. She told them the project was cancelled
and to keep using the mailbox. Helpline HLP-5309 is that request, opened on 2026-08-26.
I do not remember the project name. The closure note has the name and the date. It was a
pilot with two suppliers. A clerk still re-keyed every invoice into Paywindow, so I did
not defend it when the budget stopped.

Analyst: The Kite and Coil price difference.

Dana Okonkwo: Invoice INV-0881-212 on PO-17660 sat above the order, 2400.00 dollars. It
stayed in one clerk's mailbox for eleven days. Helpline HLP-4611 opened on 2026-03-19.
Tess was the buyer. She heard about it late because nothing brought it to her except
that mail.

Analyst: What are the payment terms, and who measures the cycle?

Dana Okonkwo: Goods are due thirty days after the invoice arrives. Freight is due
fifteen days after. I do not measure the cycle. Ellis Ward does.

Analyst: What do you see of the match?

Dana Okonkwo: The clerks compare the purchase order, the receipt and the invoice before
they pay. I see the purchase order. I do not see the match log unless a buyer is mailed
about a price.

Analyst: What would you change first?

Dana Okonkwo: Block a repeated invoice number, and stop raising purchase orders after
the goods are in. I would not buy another portal until the re-keying is gone.

## Purchase order extract

Columns are date, purchase order, supplier code, supplier slug, amount, and flag. Flag
before-delivery means the order was raised before the goods arrived. Flag
raised-after-delivery means the goods were already in. The first row is the one the
buyer pointed at. The next 380 rows are a sample, not every order.

2026-04-07 PO-19002 S-3301 yellow-dock 12750.00 raised-after-delivery
2026-01-05 PO-50001 S-1044 bramble-tin 315.00 before-delivery
2026-01-05 PO-50002 S-2210 lowlamp-paper 330.00 before-delivery
2026-01-06 PO-50003 S-0881 kite-and-coil 345.00 before-delivery
2026-01-06 PO-50004 S-3301 yellow-dock 360.00 before-delivery
2026-01-07 PO-50005 S-0770 pell-and-murmur 375.00 before-delivery
2026-01-07 PO-50006 S-4419 glassbarley 390.00 before-delivery
2026-01-08 PO-50007 S-6155 two-river 405.00 before-delivery
2026-01-08 PO-50008 S-7022 moss-freight 420.00 before-delivery
2026-01-09 PO-50009 S-1044 bramble-tin 435.00 before-delivery
2026-01-09 PO-50010 S-2210 lowlamp-paper 450.00 before-delivery
2026-01-12 PO-50011 S-0881 kite-and-coil 465.00 before-delivery
2026-01-12 PO-50012 S-3301 yellow-dock 480.00 before-delivery
2026-01-13 PO-50013 S-0770 pell-and-murmur 495.00 before-delivery
2026-01-13 PO-50014 S-4419 glassbarley 510.00 before-delivery
2026-01-14 PO-50015 S-6155 two-river 525.00 before-delivery
2026-01-14 PO-50016 S-7022 moss-freight 540.00 before-delivery
2026-01-15 PO-50017 S-1044 bramble-tin 555.00 raised-after-delivery
2026-01-15 PO-50018 S-2210 lowlamp-paper 570.00 before-delivery
2026-01-16 PO-50019 S-0881 kite-and-coil 585.00 before-delivery
2026-01-16 PO-50020 S-3301 yellow-dock 600.00 before-delivery
2026-01-19 PO-50021 S-0770 pell-and-murmur 615.00 before-delivery
2026-01-19 PO-50022 S-4419 glassbarley 630.00 before-delivery
2026-01-20 PO-50023 S-6155 two-river 645.00 before-delivery
2026-01-20 PO-50024 S-7022 moss-freight 660.00 before-delivery
2026-01-21 PO-50025 S-1044 bramble-tin 675.00 before-delivery
2026-01-21 PO-50026 S-2210 lowlamp-paper 690.00 before-delivery
2026-01-22 PO-50027 S-0881 kite-and-coil 705.00 before-delivery
2026-01-22 PO-50028 S-3301 yellow-dock 720.00 before-delivery
2026-01-23 PO-50029 S-0770 pell-and-murmur 735.00 before-delivery
2026-01-23 PO-50030 S-4419 glassbarley 750.00 before-delivery
2026-01-26 PO-50031 S-6155 two-river 765.00 before-delivery
2026-01-26 PO-50032 S-7022 moss-freight 780.00 before-delivery
2026-01-27 PO-50033 S-1044 bramble-tin 795.00 before-delivery
2026-01-27 PO-50034 S-2210 lowlamp-paper 810.00 raised-after-delivery
2026-01-28 PO-50035 S-0881 kite-and-coil 825.00 before-delivery
2026-01-28 PO-50036 S-3301 yellow-dock 840.00 before-delivery
2026-01-29 PO-50037 S-0770 pell-and-murmur 855.00 before-delivery
2026-01-29 PO-50038 S-4419 glassbarley 870.00 before-delivery
2026-01-30 PO-50039 S-6155 two-river 885.00 before-delivery
2026-01-30 PO-50040 S-7022 moss-freight 900.00 before-delivery
2026-02-02 PO-50041 S-1044 bramble-tin 915.00 before-delivery
2026-02-02 PO-50042 S-2210 lowlamp-paper 930.00 before-delivery
2026-02-03 PO-50043 S-0881 kite-and-coil 945.00 before-delivery
2026-02-03 PO-50044 S-3301 yellow-dock 960.00 before-delivery
2026-02-04 PO-50045 S-0770 pell-and-murmur 975.00 before-delivery
2026-02-04 PO-50046 S-4419 glassbarley 990.00 before-delivery
2026-02-05 PO-50047 S-6155 two-river 1005.00 before-delivery
2026-02-05 PO-50048 S-7022 moss-freight 1020.00 before-delivery
2026-02-06 PO-50049 S-1044 bramble-tin 1035.00 before-delivery
2026-02-06 PO-50050 S-2210 lowlamp-paper 1050.00 before-delivery
2026-02-09 PO-50051 S-0881 kite-and-coil 1065.00 raised-after-delivery
2026-02-09 PO-50052 S-3301 yellow-dock 1080.00 before-delivery
2026-02-10 PO-50053 S-0770 pell-and-murmur 1095.00 before-delivery
2026-02-10 PO-50054 S-4419 glassbarley 1110.00 before-delivery
2026-02-11 PO-50055 S-6155 two-river 1125.00 before-delivery
2026-02-11 PO-50056 S-7022 moss-freight 1140.00 before-delivery
2026-02-12 PO-50057 S-1044 bramble-tin 1155.00 before-delivery
2026-02-12 PO-50058 S-2210 lowlamp-paper 1170.00 before-delivery
2026-02-13 PO-50059 S-0881 kite-and-coil 1185.00 before-delivery
2026-02-13 PO-50060 S-3301 yellow-dock 1200.00 before-delivery
2026-02-16 PO-50061 S-0770 pell-and-murmur 1215.00 before-delivery
2026-02-16 PO-50062 S-4419 glassbarley 1230.00 before-delivery
2026-02-17 PO-50063 S-6155 two-river 1245.00 before-delivery
2026-02-17 PO-50064 S-7022 moss-freight 1260.00 before-delivery
2026-02-18 PO-50065 S-1044 bramble-tin 1275.00 before-delivery
2026-02-18 PO-50066 S-2210 lowlamp-paper 1290.00 before-delivery
2026-02-19 PO-50067 S-0881 kite-and-coil 1305.00 before-delivery
2026-02-19 PO-50068 S-3301 yellow-dock 1320.00 raised-after-delivery
2026-02-20 PO-50069 S-0770 pell-and-murmur 1335.00 before-delivery
2026-02-20 PO-50070 S-4419 glassbarley 1350.00 before-delivery
2026-02-23 PO-50071 S-6155 two-river 1365.00 before-delivery
2026-02-23 PO-50072 S-7022 moss-freight 1380.00 before-delivery
2026-02-24 PO-50073 S-1044 bramble-tin 1395.00 before-delivery
2026-02-24 PO-50074 S-2210 lowlamp-paper 1410.00 before-delivery
2026-02-25 PO-50075 S-0881 kite-and-coil 1425.00 before-delivery
2026-02-25 PO-50076 S-3301 yellow-dock 1440.00 before-delivery
2026-02-26 PO-50077 S-0770 pell-and-murmur 1455.00 before-delivery
2026-02-26 PO-50078 S-4419 glassbarley 1470.00 before-delivery
2026-02-27 PO-50079 S-6155 two-river 1485.00 before-delivery
2026-02-27 PO-50080 S-7022 moss-freight 1500.00 before-delivery
2026-03-02 PO-50081 S-1044 bramble-tin 1515.00 before-delivery
2026-03-02 PO-50082 S-2210 lowlamp-paper 1530.00 before-delivery
2026-03-03 PO-50083 S-0881 kite-and-coil 1545.00 before-delivery
2026-03-03 PO-50084 S-3301 yellow-dock 1560.00 before-delivery
2026-03-04 PO-50085 S-0770 pell-and-murmur 1575.00 raised-after-delivery
2026-03-04 PO-50086 S-4419 glassbarley 1590.00 before-delivery
2026-03-05 PO-50087 S-6155 two-river 1605.00 before-delivery
2026-03-05 PO-50088 S-7022 moss-freight 1620.00 before-delivery
2026-03-06 PO-50089 S-1044 bramble-tin 1635.00 before-delivery
2026-03-06 PO-50090 S-2210 lowlamp-paper 1650.00 before-delivery
2026-03-09 PO-50091 S-0881 kite-and-coil 1665.00 before-delivery
2026-03-09 PO-50092 S-3301 yellow-dock 1680.00 before-delivery
2026-03-10 PO-50093 S-0770 pell-and-murmur 1695.00 before-delivery
2026-03-10 PO-50094 S-4419 glassbarley 1710.00 before-delivery
2026-03-11 PO-50095 S-6155 two-river 1725.00 before-delivery
2026-03-11 PO-50096 S-7022 moss-freight 1740.00 before-delivery
2026-03-12 PO-50097 S-1044 bramble-tin 1755.00 before-delivery
2026-03-12 PO-50098 S-2210 lowlamp-paper 1770.00 before-delivery
2026-03-13 PO-50099 S-0881 kite-and-coil 1785.00 before-delivery
2026-03-13 PO-50100 S-3301 yellow-dock 1800.00 before-delivery
2026-03-16 PO-50101 S-0770 pell-and-murmur 1815.00 before-delivery
2026-03-16 PO-50102 S-4419 glassbarley 1830.00 raised-after-delivery
2026-03-17 PO-50103 S-6155 two-river 1845.00 before-delivery
2026-03-17 PO-50104 S-7022 moss-freight 1860.00 before-delivery
2026-03-18 PO-50105 S-1044 bramble-tin 1875.00 before-delivery
2026-03-18 PO-50106 S-2210 lowlamp-paper 1890.00 before-delivery
2026-03-19 PO-50107 S-0881 kite-and-coil 1905.00 before-delivery
2026-03-19 PO-50108 S-3301 yellow-dock 1920.00 before-delivery
2026-03-20 PO-50109 S-0770 pell-and-murmur 1935.00 before-delivery
2026-03-20 PO-50110 S-4419 glassbarley 1950.00 before-delivery
2026-03-23 PO-50111 S-6155 two-river 1965.00 before-delivery
2026-03-23 PO-50112 S-7022 moss-freight 1980.00 before-delivery
2026-03-24 PO-50113 S-1044 bramble-tin 1995.00 before-delivery
2026-03-24 PO-50114 S-2210 lowlamp-paper 2010.00 before-delivery
2026-03-25 PO-50115 S-0881 kite-and-coil 2025.00 before-delivery
2026-03-25 PO-50116 S-3301 yellow-dock 2040.00 before-delivery
2026-03-26 PO-50117 S-0770 pell-and-murmur 2055.00 before-delivery
2026-03-26 PO-50118 S-4419 glassbarley 2070.00 before-delivery
2026-03-27 PO-50119 S-6155 two-river 2085.00 raised-after-delivery
2026-03-27 PO-50120 S-7022 moss-freight 2100.00 before-delivery
2026-03-30 PO-50121 S-1044 bramble-tin 2115.00 before-delivery
2026-03-30 PO-50122 S-2210 lowlamp-paper 2130.00 before-delivery
2026-03-31 PO-50123 S-0881 kite-and-coil 2145.00 before-delivery
2026-03-31 PO-50124 S-3301 yellow-dock 2160.00 before-delivery
2026-04-01 PO-50125 S-0770 pell-and-murmur 2175.00 before-delivery
2026-04-01 PO-50126 S-4419 glassbarley 2190.00 before-delivery
2026-04-02 PO-50127 S-6155 two-river 2205.00 before-delivery
2026-04-02 PO-50128 S-7022 moss-freight 2220.00 before-delivery
2026-04-03 PO-50129 S-1044 bramble-tin 2235.00 before-delivery
2026-04-03 PO-50130 S-2210 lowlamp-paper 2250.00 before-delivery
2026-04-06 PO-50131 S-0881 kite-and-coil 2265.00 before-delivery
2026-04-06 PO-50132 S-3301 yellow-dock 2280.00 before-delivery
2026-04-07 PO-50133 S-0770 pell-and-murmur 2295.00 before-delivery
2026-04-07 PO-50134 S-4419 glassbarley 2310.00 before-delivery
2026-04-08 PO-50135 S-6155 two-river 2325.00 before-delivery
2026-04-08 PO-50136 S-7022 moss-freight 2340.00 raised-after-delivery
2026-04-09 PO-50137 S-1044 bramble-tin 2355.00 before-delivery
2026-04-09 PO-50138 S-2210 lowlamp-paper 2370.00 before-delivery
2026-04-10 PO-50139 S-0881 kite-and-coil 2385.00 before-delivery
2026-04-10 PO-50140 S-3301 yellow-dock 2400.00 before-delivery
2026-04-13 PO-50141 S-0770 pell-and-murmur 2415.00 before-delivery
2026-04-13 PO-50142 S-4419 glassbarley 2430.00 before-delivery
2026-04-14 PO-50143 S-6155 two-river 2445.00 before-delivery
2026-04-14 PO-50144 S-7022 moss-freight 2460.00 before-delivery
2026-04-15 PO-50145 S-1044 bramble-tin 2475.00 before-delivery
2026-04-15 PO-50146 S-2210 lowlamp-paper 2490.00 before-delivery
2026-04-16 PO-50147 S-0881 kite-and-coil 2505.00 before-delivery
2026-04-16 PO-50148 S-3301 yellow-dock 2520.00 before-delivery
2026-04-17 PO-50149 S-0770 pell-and-murmur 2535.00 before-delivery
2026-04-17 PO-50150 S-4419 glassbarley 2550.00 before-delivery
2026-04-20 PO-50151 S-6155 two-river 2565.00 before-delivery
2026-04-20 PO-50152 S-7022 moss-freight 2580.00 before-delivery
2026-04-21 PO-50153 S-1044 bramble-tin 2595.00 raised-after-delivery
2026-04-21 PO-50154 S-2210 lowlamp-paper 2610.00 before-delivery
2026-04-22 PO-50155 S-0881 kite-and-coil 2625.00 before-delivery
2026-04-22 PO-50156 S-3301 yellow-dock 2640.00 before-delivery
2026-04-23 PO-50157 S-0770 pell-and-murmur 2655.00 before-delivery
2026-04-23 PO-50158 S-4419 glassbarley 2670.00 before-delivery
2026-04-24 PO-50159 S-6155 two-river 2685.00 before-delivery
2026-04-24 PO-50160 S-7022 moss-freight 2700.00 before-delivery
2026-04-27 PO-50161 S-1044 bramble-tin 2715.00 before-delivery
2026-04-27 PO-50162 S-2210 lowlamp-paper 2730.00 before-delivery
2026-04-28 PO-50163 S-0881 kite-and-coil 2745.00 before-delivery
2026-04-28 PO-50164 S-3301 yellow-dock 2760.00 before-delivery
2026-04-29 PO-50165 S-0770 pell-and-murmur 2775.00 before-delivery
2026-04-29 PO-50166 S-4419 glassbarley 2790.00 before-delivery
2026-04-30 PO-50167 S-6155 two-river 2805.00 before-delivery
2026-04-30 PO-50168 S-7022 moss-freight 2820.00 before-delivery
2026-05-01 PO-50169 S-1044 bramble-tin 2835.00 before-delivery
2026-05-01 PO-50170 S-2210 lowlamp-paper 2850.00 raised-after-delivery
2026-05-04 PO-50171 S-0881 kite-and-coil 2865.00 before-delivery
2026-05-04 PO-50172 S-3301 yellow-dock 2880.00 before-delivery
2026-05-05 PO-50173 S-0770 pell-and-murmur 2895.00 before-delivery
2026-05-05 PO-50174 S-4419 glassbarley 2910.00 before-delivery
2026-05-06 PO-50175 S-6155 two-river 2925.00 before-delivery
2026-05-06 PO-50176 S-7022 moss-freight 2940.00 before-delivery
2026-05-07 PO-50177 S-1044 bramble-tin 2955.00 before-delivery
2026-05-07 PO-50178 S-2210 lowlamp-paper 2970.00 before-delivery
2026-05-08 PO-50179 S-0881 kite-and-coil 2985.00 before-delivery
2026-05-08 PO-50180 S-3301 yellow-dock 3000.00 before-delivery
2026-05-11 PO-50181 S-0770 pell-and-murmur 3015.00 before-delivery
2026-05-11 PO-50182 S-4419 glassbarley 3030.00 before-delivery
2026-05-12 PO-50183 S-6155 two-river 3045.00 before-delivery
2026-05-12 PO-50184 S-7022 moss-freight 3060.00 before-delivery
2026-05-13 PO-50185 S-1044 bramble-tin 3075.00 before-delivery
2026-05-13 PO-50186 S-2210 lowlamp-paper 3090.00 before-delivery
2026-05-14 PO-50187 S-0881 kite-and-coil 3105.00 raised-after-delivery
2026-05-14 PO-50188 S-3301 yellow-dock 3120.00 before-delivery
2026-05-15 PO-50189 S-0770 pell-and-murmur 3135.00 before-delivery
2026-05-15 PO-50190 S-4419 glassbarley 3150.00 before-delivery
2026-05-18 PO-50191 S-6155 two-river 3165.00 before-delivery
2026-05-18 PO-50192 S-7022 moss-freight 3180.00 before-delivery
2026-05-19 PO-50193 S-1044 bramble-tin 3195.00 before-delivery
2026-05-19 PO-50194 S-2210 lowlamp-paper 3210.00 before-delivery
2026-05-20 PO-50195 S-0881 kite-and-coil 3225.00 before-delivery
2026-05-20 PO-50196 S-3301 yellow-dock 3240.00 before-delivery
2026-05-21 PO-50197 S-0770 pell-and-murmur 3255.00 before-delivery
2026-05-21 PO-50198 S-4419 glassbarley 3270.00 before-delivery
2026-05-22 PO-50199 S-6155 two-river 3285.00 before-delivery
2026-05-22 PO-50200 S-7022 moss-freight 3300.00 before-delivery
2026-05-25 PO-50201 S-1044 bramble-tin 3315.00 before-delivery
2026-05-25 PO-50202 S-2210 lowlamp-paper 3330.00 before-delivery
2026-05-26 PO-50203 S-0881 kite-and-coil 3345.00 before-delivery
2026-05-26 PO-50204 S-3301 yellow-dock 3360.00 raised-after-delivery
2026-05-27 PO-50205 S-0770 pell-and-murmur 3375.00 before-delivery
2026-05-27 PO-50206 S-4419 glassbarley 3390.00 before-delivery
2026-05-28 PO-50207 S-6155 two-river 3405.00 before-delivery
2026-05-28 PO-50208 S-7022 moss-freight 3420.00 before-delivery
2026-05-29 PO-50209 S-1044 bramble-tin 3435.00 before-delivery
2026-05-29 PO-50210 S-2210 lowlamp-paper 3450.00 before-delivery
2026-06-01 PO-50211 S-0881 kite-and-coil 3465.00 before-delivery
2026-06-01 PO-50212 S-3301 yellow-dock 3480.00 before-delivery
2026-06-02 PO-50213 S-0770 pell-and-murmur 3495.00 before-delivery
2026-06-02 PO-50214 S-4419 glassbarley 3510.00 before-delivery
2026-06-03 PO-50215 S-6155 two-river 3525.00 before-delivery
2026-06-03 PO-50216 S-7022 moss-freight 3540.00 before-delivery
2026-06-04 PO-50217 S-1044 bramble-tin 3555.00 before-delivery
2026-06-04 PO-50218 S-2210 lowlamp-paper 3570.00 before-delivery
2026-06-05 PO-50219 S-0881 kite-and-coil 3585.00 before-delivery
2026-06-05 PO-50220 S-3301 yellow-dock 3600.00 before-delivery
2026-06-08 PO-50221 S-0770 pell-and-murmur 3615.00 raised-after-delivery
2026-06-08 PO-50222 S-4419 glassbarley 3630.00 before-delivery
2026-06-09 PO-50223 S-6155 two-river 3645.00 before-delivery
2026-06-09 PO-50224 S-7022 moss-freight 3660.00 before-delivery
2026-06-10 PO-50225 S-1044 bramble-tin 3675.00 before-delivery
2026-06-10 PO-50226 S-2210 lowlamp-paper 3690.00 before-delivery
2026-06-11 PO-50227 S-0881 kite-and-coil 3705.00 before-delivery
2026-06-11 PO-50228 S-3301 yellow-dock 3720.00 before-delivery
2026-06-12 PO-50229 S-0770 pell-and-murmur 3735.00 before-delivery
2026-06-12 PO-50230 S-4419 glassbarley 3750.00 before-delivery
2026-06-15 PO-50231 S-6155 two-river 3765.00 before-delivery
2026-06-15 PO-50232 S-7022 moss-freight 3780.00 before-delivery
2026-06-16 PO-50233 S-1044 bramble-tin 3795.00 before-delivery
2026-06-16 PO-50234 S-2210 lowlamp-paper 3810.00 before-delivery
2026-06-17 PO-50235 S-0881 kite-and-coil 3825.00 before-delivery
2026-06-17 PO-50236 S-3301 yellow-dock 3840.00 before-delivery
2026-06-18 PO-50237 S-0770 pell-and-murmur 3855.00 before-delivery
2026-06-18 PO-50238 S-4419 glassbarley 3870.00 raised-after-delivery
2026-06-19 PO-50239 S-6155 two-river 3885.00 before-delivery
2026-06-19 PO-50240 S-7022 moss-freight 3900.00 before-delivery
2026-06-22 PO-50241 S-1044 bramble-tin 3915.00 before-delivery
2026-06-22 PO-50242 S-2210 lowlamp-paper 3930.00 before-delivery
2026-06-23 PO-50243 S-0881 kite-and-coil 3945.00 before-delivery
2026-06-23 PO-50244 S-3301 yellow-dock 3960.00 before-delivery
2026-06-24 PO-50245 S-0770 pell-and-murmur 3975.00 before-delivery
2026-06-24 PO-50246 S-4419 glassbarley 3990.00 before-delivery
2026-06-25 PO-50247 S-6155 two-river 4005.00 before-delivery
2026-06-25 PO-50248 S-7022 moss-freight 4020.00 before-delivery
2026-06-26 PO-50249 S-1044 bramble-tin 4035.00 before-delivery
2026-06-26 PO-50250 S-2210 lowlamp-paper 4050.00 before-delivery
2026-06-29 PO-50251 S-0881 kite-and-coil 4065.00 before-delivery
2026-06-29 PO-50252 S-3301 yellow-dock 4080.00 before-delivery
2026-06-30 PO-50253 S-0770 pell-and-murmur 4095.00 before-delivery
2026-06-30 PO-50254 S-4419 glassbarley 4110.00 before-delivery
2026-07-01 PO-50255 S-6155 two-river 4125.00 raised-after-delivery
2026-07-01 PO-50256 S-7022 moss-freight 4140.00 before-delivery
2026-07-02 PO-50257 S-1044 bramble-tin 4155.00 before-delivery
2026-07-02 PO-50258 S-2210 lowlamp-paper 4170.00 before-delivery
2026-07-03 PO-50259 S-0881 kite-and-coil 4185.00 before-delivery
2026-07-03 PO-50260 S-3301 yellow-dock 4200.00 before-delivery
2026-07-06 PO-50261 S-0770 pell-and-murmur 4215.00 before-delivery
2026-07-06 PO-50262 S-4419 glassbarley 4230.00 before-delivery
2026-07-07 PO-50263 S-6155 two-river 4245.00 before-delivery
2026-07-07 PO-50264 S-7022 moss-freight 4260.00 before-delivery
2026-07-08 PO-50265 S-1044 bramble-tin 4275.00 before-delivery
2026-07-08 PO-50266 S-2210 lowlamp-paper 4290.00 before-delivery
2026-07-09 PO-50267 S-0881 kite-and-coil 4305.00 before-delivery
2026-07-09 PO-50268 S-3301 yellow-dock 4320.00 before-delivery
2026-07-10 PO-50269 S-0770 pell-and-murmur 4335.00 before-delivery
2026-07-10 PO-50270 S-4419 glassbarley 4350.00 before-delivery
2026-07-13 PO-50271 S-6155 two-river 4365.00 before-delivery
2026-07-13 PO-50272 S-7022 moss-freight 4380.00 raised-after-delivery
2026-07-14 PO-50273 S-1044 bramble-tin 4395.00 before-delivery
2026-07-14 PO-50274 S-2210 lowlamp-paper 4410.00 before-delivery
2026-07-15 PO-50275 S-0881 kite-and-coil 4425.00 before-delivery
2026-07-15 PO-50276 S-3301 yellow-dock 4440.00 before-delivery
2026-07-16 PO-50277 S-0770 pell-and-murmur 4455.00 before-delivery
2026-07-16 PO-50278 S-4419 glassbarley 4470.00 before-delivery
2026-07-17 PO-50279 S-6155 two-river 4485.00 before-delivery
2026-07-17 PO-50280 S-7022 moss-freight 4500.00 before-delivery
2026-07-20 PO-50281 S-1044 bramble-tin 4515.00 before-delivery
2026-07-20 PO-50282 S-2210 lowlamp-paper 4530.00 before-delivery
2026-07-21 PO-50283 S-0881 kite-and-coil 4545.00 before-delivery
2026-07-21 PO-50284 S-3301 yellow-dock 4560.00 before-delivery
2026-07-22 PO-50285 S-0770 pell-and-murmur 4575.00 before-delivery
2026-07-22 PO-50286 S-4419 glassbarley 4590.00 before-delivery
2026-07-23 PO-50287 S-6155 two-river 4605.00 before-delivery
2026-07-23 PO-50288 S-7022 moss-freight 4620.00 before-delivery
2026-07-24 PO-50289 S-1044 bramble-tin 4635.00 raised-after-delivery
2026-07-24 PO-50290 S-2210 lowlamp-paper 4650.00 before-delivery
2026-07-27 PO-50291 S-0881 kite-and-coil 4665.00 before-delivery
2026-07-27 PO-50292 S-3301 yellow-dock 4680.00 before-delivery
2026-07-28 PO-50293 S-0770 pell-and-murmur 4695.00 before-delivery
2026-07-28 PO-50294 S-4419 glassbarley 4710.00 before-delivery
2026-07-29 PO-50295 S-6155 two-river 4725.00 before-delivery
2026-07-29 PO-50296 S-7022 moss-freight 4740.00 before-delivery
2026-07-30 PO-50297 S-1044 bramble-tin 4755.00 before-delivery
2026-07-30 PO-50298 S-2210 lowlamp-paper 4770.00 before-delivery
2026-07-31 PO-50299 S-0881 kite-and-coil 4785.00 before-delivery
2026-07-31 PO-50300 S-3301 yellow-dock 4800.00 before-delivery
2026-08-03 PO-50301 S-0770 pell-and-murmur 4815.00 before-delivery
2026-08-03 PO-50302 S-4419 glassbarley 4830.00 before-delivery
2026-08-04 PO-50303 S-6155 two-river 4845.00 before-delivery
2026-08-04 PO-50304 S-7022 moss-freight 4860.00 before-delivery
2026-08-05 PO-50305 S-1044 bramble-tin 4875.00 before-delivery
2026-08-05 PO-50306 S-2210 lowlamp-paper 4890.00 raised-after-delivery
2026-08-06 PO-50307 S-0881 kite-and-coil 4905.00 before-delivery
2026-08-06 PO-50308 S-3301 yellow-dock 4920.00 before-delivery
2026-08-07 PO-50309 S-0770 pell-and-murmur 4935.00 before-delivery
2026-08-07 PO-50310 S-4419 glassbarley 4950.00 before-delivery
2026-08-10 PO-50311 S-6155 two-river 4965.00 before-delivery
2026-08-10 PO-50312 S-7022 moss-freight 4980.00 before-delivery
2026-08-11 PO-50313 S-1044 bramble-tin 4995.00 before-delivery
2026-08-11 PO-50314 S-2210 lowlamp-paper 5010.00 before-delivery
2026-08-12 PO-50315 S-0881 kite-and-coil 5025.00 before-delivery
2026-08-12 PO-50316 S-3301 yellow-dock 5040.00 before-delivery
2026-08-13 PO-50317 S-0770 pell-and-murmur 5055.00 before-delivery
2026-08-13 PO-50318 S-4419 glassbarley 5070.00 before-delivery
2026-08-14 PO-50319 S-6155 two-river 5085.00 before-delivery
2026-08-14 PO-50320 S-7022 moss-freight 5100.00 before-delivery
2026-08-17 PO-50321 S-1044 bramble-tin 5115.00 before-delivery
2026-08-17 PO-50322 S-2210 lowlamp-paper 5130.00 before-delivery
2026-08-18 PO-50323 S-0881 kite-and-coil 5145.00 raised-after-delivery
2026-08-18 PO-50324 S-3301 yellow-dock 5160.00 before-delivery
2026-08-19 PO-50325 S-0770 pell-and-murmur 5175.00 before-delivery
2026-08-19 PO-50326 S-4419 glassbarley 5190.00 before-delivery
2026-08-20 PO-50327 S-6155 two-river 5205.00 before-delivery
2026-08-20 PO-50328 S-7022 moss-freight 5220.00 before-delivery
2026-08-21 PO-50329 S-1044 bramble-tin 5235.00 before-delivery
2026-08-21 PO-50330 S-2210 lowlamp-paper 5250.00 before-delivery
2026-08-24 PO-50331 S-0881 kite-and-coil 5265.00 before-delivery
2026-08-24 PO-50332 S-3301 yellow-dock 5280.00 before-delivery
2026-08-25 PO-50333 S-0770 pell-and-murmur 5295.00 before-delivery
2026-08-25 PO-50334 S-4419 glassbarley 5310.00 before-delivery
2026-08-26 PO-50335 S-6155 two-river 5325.00 before-delivery
2026-08-26 PO-50336 S-7022 moss-freight 5340.00 before-delivery
2026-08-27 PO-50337 S-1044 bramble-tin 5355.00 before-delivery
2026-08-27 PO-50338 S-2210 lowlamp-paper 5370.00 before-delivery
2026-08-28 PO-50339 S-0881 kite-and-coil 5385.00 before-delivery
2026-08-28 PO-50340 S-3301 yellow-dock 5400.00 raised-after-delivery
2026-08-31 PO-50341 S-0770 pell-and-murmur 5415.00 before-delivery
2026-08-31 PO-50342 S-4419 glassbarley 5430.00 before-delivery
2026-09-01 PO-50343 S-6155 two-river 5445.00 before-delivery
2026-09-01 PO-50344 S-7022 moss-freight 5460.00 before-delivery
2026-09-02 PO-50345 S-1044 bramble-tin 5475.00 before-delivery
2026-09-02 PO-50346 S-2210 lowlamp-paper 5490.00 before-delivery
2026-09-03 PO-50347 S-0881 kite-and-coil 5505.00 before-delivery
2026-09-03 PO-50348 S-3301 yellow-dock 5520.00 before-delivery
2026-09-04 PO-50349 S-0770 pell-and-murmur 5535.00 before-delivery
2026-09-04 PO-50350 S-4419 glassbarley 5550.00 before-delivery
2026-09-07 PO-50351 S-6155 two-river 5565.00 before-delivery
2026-09-07 PO-50352 S-7022 moss-freight 5580.00 before-delivery
2026-09-08 PO-50353 S-1044 bramble-tin 5595.00 before-delivery
2026-09-08 PO-50354 S-2210 lowlamp-paper 5610.00 before-delivery
2026-09-09 PO-50355 S-0881 kite-and-coil 5625.00 before-delivery
2026-09-09 PO-50356 S-3301 yellow-dock 5640.00 before-delivery
2026-09-10 PO-50357 S-0770 pell-and-murmur 5655.00 raised-after-delivery
2026-09-10 PO-50358 S-4419 glassbarley 5670.00 before-delivery
2026-09-11 PO-50359 S-6155 two-river 5685.00 before-delivery
2026-09-11 PO-50360 S-7022 moss-freight 5700.00 before-delivery
2026-09-14 PO-50361 S-1044 bramble-tin 5715.00 before-delivery
2026-09-14 PO-50362 S-2210 lowlamp-paper 5730.00 before-delivery
2026-09-15 PO-50363 S-0881 kite-and-coil 5745.00 before-delivery
2026-09-15 PO-50364 S-3301 yellow-dock 5760.00 before-delivery
2026-09-16 PO-50365 S-0770 pell-and-murmur 5775.00 before-delivery
2026-09-16 PO-50366 S-4419 glassbarley 5790.00 before-delivery
2026-09-17 PO-50367 S-6155 two-river 5805.00 before-delivery
2026-09-17 PO-50368 S-7022 moss-freight 5820.00 before-delivery
2026-09-18 PO-50369 S-1044 bramble-tin 5835.00 before-delivery
2026-09-18 PO-50370 S-2210 lowlamp-paper 5850.00 before-delivery
2026-09-21 PO-50371 S-0881 kite-and-coil 5865.00 before-delivery
2026-09-21 PO-50372 S-3301 yellow-dock 5880.00 before-delivery
2026-09-22 PO-50373 S-0770 pell-and-murmur 5895.00 before-delivery
2026-09-22 PO-50374 S-4419 glassbarley 5910.00 raised-after-delivery
2026-09-23 PO-50375 S-6155 two-river 5925.00 before-delivery
2026-09-24 PO-50376 S-7022 moss-freight 5940.00 before-delivery
2026-09-25 PO-50377 S-1044 bramble-tin 5955.00 before-delivery
2026-09-28 PO-50378 S-2210 lowlamp-paper 5970.00 before-delivery
2026-09-29 PO-50379 S-0881 kite-and-coil 5985.00 before-delivery
2026-09-30 PO-50380 S-3301 yellow-dock 6000.00 before-delivery
