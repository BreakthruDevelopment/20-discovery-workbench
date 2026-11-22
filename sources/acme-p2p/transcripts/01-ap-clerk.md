# Accounts payable clerk interview
Client: Acme
Subject: procure-to-pay
Interview date: 2026-10-13
Interviewee: Rowan Hale, accounts payable clerk
Interviewer: Analyst
Location: Mill Road office

Analyst: The brief says spend on procure-to-pay is too high. I want the work as it is
done this week.

Rowan Hale: I have been an accounts payable clerk for six years. Nia Pell and Owen Brice
are the other two. We sit at the Mill Road office. About 220 supplier invoices arrive in
a week, from about 80 suppliers.

Analyst: Walk me through an invoice from the moment it arrives.

Rowan Hale: It arrives at invoices@acme.example. I open the oldest unread message, save
the document, and look for a purchase order in Gatepass and a goods receipt in Dockhand.
I write the result on the match log. The match log is a spreadsheet on the office share.
It is not a Paywindow screen.

Analyst: How is a three-way match done?

Rowan Hale: We match the purchase order, the goods receipt and the invoice by hand.

Rowan Hale: The three documents are the purchase order in Gatepass, the goods receipt in
Dockhand, and the supplier invoice from the mailbox. I compare supplier, quantity and
unit price. Paywindow does not compare them. Its screens are Invoice entry, Payment
proposal, Supplier record and Payment history. It will propose whatever a clerk
releases. It does not read the match log.

Analyst: What are the statuses you set?

Rowan Hale: Entered, held, proposed, released and paid. A clerk may set entered, held or
proposed. Policy says only Gwen Adler may set released. The system does not stop a buyer
from doing it. Paid is set when the bank run is confirmed. I can open a held invoice if
I still have the number. The others cannot ask the system for a list of mine.

Analyst: Where does a mismatch go?

Rowan Hale: There is no exception queue.

Rowan Hale: I email the buyer who owns the purchase order and I set the invoice to held.
The row on the match log carries my name. When I am away, that row is not visible to Nia
or Owen unless they already know the invoice number.

Analyst: Tell me about invoice INV-1044-339.

Rowan Hale: Bramble Tin, supplier S-1044, purchase order PO-17330, 18420.00 dollars. I
entered it on 2026-02-10 and the match looked clean. On 2026-02-11 the same invoice was
entered again. Paywindow does not block a second payment of an invoice number already
paid. Helpline HLP-4410 is that second payment. The search I am supposed to do is a step
I can skip.

Analyst: And purchase order PO-18821?

Rowan Hale: Lowlamp Paper, invoice INV-2210-044, 9600.50 dollars. On 2026-03-02 the
buyer said the goods were on the dock. Dockhand had no receipt. The payment was released
anyway. Helpline HLP-4502. Samir Quill told me the same day that the dock had nothing on
file.

Analyst: The Lowlamp one in June, and the freight one in September.

Rowan Hale: Invoice INV-2210-118 on PO-18110 was paid on 2026-05-28 and again on
2026-06-02, 5320.75 dollars. Helpline HLP-4901. The mailbox had been read twice and Nia
keyed the second one. Invoice INV-7022-077 for Moss Freight, PO-18660, 890.25 dollars,
was keyed on 2026-09-17 and again on 2026-09-18. Helpline HLP-5440. Owen keyed the
second one after the mailbox was read again.

Analyst: What happened on 22 June?

Rowan Hale: I compared a batch of 40 Pell and Murmur invoices on the spreadsheet because
Paywindow has no match function. Helpline HLP-5012 records that day, 2026-06-22.
Supplier S-0770.

Analyst: The August hold.

Rowan Hale: I was away from the first of August. Invoice INV-4419-088 on PO-18440,
Glassbarley, 3100.00 dollars, stayed on hold with my name on it. Nia could not see it.
Helpline HLP-5244 opened on 2026-08-01 and closed on 2026-08-18, when I was back.

Analyst: The short payment in October.

Rowan Hale: Two River Packaging disputed invoice INV-6155-014 on PO-19110. The
difference was 415.40 dollars, a price the purchase order never carried. Helpline
HLP-5527 opened on 2026-10-02. Owen had the row.

Analyst: Who else touches the match log, and what happens on Fridays?

Rowan Hale: Nia, Owen and I write it. Gwen Adler can read it. Buyers are not supposed to
change a payment status. On Fridays Tess Harp has set released while we were in the
month-end meeting. Policy forbids that. The system allows it. Dana Okonkwo and Ivo Marsh
have logins too.

Analyst: Do you see lines in the ledger you did not enter?

Rowan Hale: Yes. Ledgerline shows lines I did not enter in Paywindow. I do not know the
program that sends them. Jules Fen says it is not an interface IT runs. Samir at the
dock knows more than I do.

Analyst: What would you change first?

Rowan Hale: A place the other clerks can see a held invoice without already knowing its
number, and a block on a second payment of an invoice number. I would not start with a
portal. The last one still left us re-keying the invoice into Paywindow.

## Match log extract

Columns are date, invoice, purchase order, supplier code, supplier slug, amount, result,
and holder. The first 11 rows are the ones the clerk pointed at. The next 700 rows are a
sample from 2026-01-05 through 2026-09-30, not the full population of about 220 invoices
a week. Result matched means the three documents agreed and the clerk set proposed.
Result price-diff, qty-diff or no-receipt means the clerk did not propose. Result
second-keying means the same invoice was entered again after a payment. Result
released-without-receipt means a payment was released with no goods receipt. Result
after-the-fact means the purchase order was raised after delivery and then matched. A
hyphen holder is the ordinary rotation. A named holder is the person the row sat with.

2026-02-10 INV-1044-339 PO-17330 S-1044 bramble-tin 18420.00 matched rowan-hale
2026-02-11 INV-1044-339 PO-17330 S-1044 bramble-tin 18420.00 second-keying rowan-hale
2026-03-02 INV-2210-044 PO-18821 S-2210 lowlamp-paper 9600.50 released-without-receipt rowan-hale
2026-03-19 INV-0881-212 PO-17660 S-0881 kite-and-coil 2400.00 price-diff nia-pell
2026-04-08 INV-3301-019 PO-19002 S-3301 yellow-dock 12750.00 after-the-fact rowan-hale
2026-05-28 INV-2210-118 PO-18110 S-2210 lowlamp-paper 5320.75 matched nia-pell
2026-06-02 INV-2210-118 PO-18110 S-2210 lowlamp-paper 5320.75 second-keying nia-pell
2026-08-01 INV-4419-088 PO-18440 S-4419 glassbarley 3100.00 no-receipt rowan-hale
2026-09-17 INV-7022-077 PO-18660 S-7022 moss-freight 890.25 matched owen-brice
2026-09-18 INV-7022-077 PO-18660 S-7022 moss-freight 890.25 second-keying owen-brice
2026-10-02 INV-6155-014 PO-19110 S-6155 two-river 415.40 price-diff owen-brice
2026-01-05 INV-M-0001 PO-30001 S-1044 bramble-tin 225.00 matched -
2026-01-05 INV-M-0002 PO-30002 S-2210 lowlamp-paper 250.00 matched -
2026-01-05 INV-M-0003 PO-30003 S-0881 kite-and-coil 275.00 matched -
2026-01-05 INV-M-0004 PO-30004 S-3301 yellow-dock 300.00 matched -
2026-01-06 INV-M-0005 PO-30005 S-0770 pell-and-murmur 325.00 price-diff nia-pell
2026-01-06 INV-M-0006 PO-30006 S-4419 glassbarley 350.00 qty-diff owen-brice
2026-01-06 INV-M-0007 PO-30007 S-6155 two-river 375.00 no-receipt rowan-hale
2026-01-06 INV-M-0008 PO-30008 S-7022 moss-freight 400.00 matched -
2026-01-07 INV-M-0009 PO-30009 S-1044 bramble-tin 425.00 matched -
2026-01-07 INV-M-0010 PO-30010 S-2210 lowlamp-paper 450.00 matched -
2026-01-07 INV-M-0011 PO-30011 S-0881 kite-and-coil 475.00 matched -
2026-01-07 INV-M-0012 PO-30012 S-3301 yellow-dock 500.00 price-diff owen-brice
2026-01-08 INV-M-0013 PO-30013 S-0770 pell-and-murmur 525.00 qty-diff rowan-hale
2026-01-08 INV-M-0014 PO-30014 S-4419 glassbarley 550.00 no-receipt nia-pell
2026-01-08 INV-M-0015 PO-30015 S-6155 two-river 575.00 matched -
2026-01-08 INV-M-0016 PO-30016 S-7022 moss-freight 600.00 matched -
2026-01-09 INV-M-0017 PO-30017 S-1044 bramble-tin 625.00 matched -
2026-01-09 INV-M-0018 PO-30018 S-2210 lowlamp-paper 650.00 matched -
2026-01-09 INV-M-0019 PO-30019 S-0881 kite-and-coil 675.00 price-diff rowan-hale
2026-01-09 INV-M-0020 PO-30020 S-3301 yellow-dock 700.00 qty-diff nia-pell
2026-01-12 INV-M-0021 PO-30021 S-0770 pell-and-murmur 725.00 no-receipt owen-brice
2026-01-12 INV-M-0022 PO-30022 S-4419 glassbarley 750.00 matched -
2026-01-12 INV-M-0023 PO-30023 S-6155 two-river 775.00 matched -
2026-01-12 INV-M-0024 PO-30024 S-7022 moss-freight 800.00 matched -
2026-01-13 INV-M-0025 PO-30025 S-1044 bramble-tin 825.00 matched -
2026-01-13 INV-M-0026 PO-30026 S-2210 lowlamp-paper 850.00 price-diff nia-pell
2026-01-13 INV-M-0027 PO-30027 S-0881 kite-and-coil 875.00 qty-diff owen-brice
2026-01-13 INV-M-0028 PO-30028 S-3301 yellow-dock 900.00 no-receipt rowan-hale
2026-01-14 INV-M-0029 PO-30029 S-0770 pell-and-murmur 925.00 matched -
2026-01-14 INV-M-0030 PO-30030 S-4419 glassbarley 950.00 matched -
2026-01-14 INV-M-0031 PO-30031 S-6155 two-river 975.00 matched -
2026-01-14 INV-M-0032 PO-30032 S-7022 moss-freight 1000.00 matched -
2026-01-15 INV-M-0033 PO-30033 S-1044 bramble-tin 1025.00 price-diff owen-brice
2026-01-15 INV-M-0034 PO-30034 S-2210 lowlamp-paper 1050.00 qty-diff rowan-hale
2026-01-15 INV-M-0035 PO-30035 S-0881 kite-and-coil 1075.00 no-receipt nia-pell
2026-01-15 INV-M-0036 PO-30036 S-3301 yellow-dock 1100.00 matched -
2026-01-16 INV-M-0037 PO-30037 S-0770 pell-and-murmur 1125.00 matched -
2026-01-16 INV-M-0038 PO-30038 S-4419 glassbarley 1150.00 matched -
2026-01-16 INV-M-0039 PO-30039 S-6155 two-river 1175.00 matched -
2026-01-16 INV-M-0040 PO-30040 S-7022 moss-freight 1200.00 price-diff rowan-hale
2026-01-19 INV-M-0041 PO-30041 S-1044 bramble-tin 1225.00 qty-diff nia-pell
2026-01-19 INV-M-0042 PO-30042 S-2210 lowlamp-paper 1250.00 no-receipt owen-brice
2026-01-19 INV-M-0043 PO-30043 S-0881 kite-and-coil 1275.00 matched -
2026-01-19 INV-M-0044 PO-30044 S-3301 yellow-dock 1300.00 matched -
2026-01-20 INV-M-0045 PO-30045 S-0770 pell-and-murmur 1325.00 matched -
2026-01-20 INV-M-0046 PO-30046 S-4419 glassbarley 1350.00 matched -
2026-01-20 INV-M-0047 PO-30047 S-6155 two-river 1375.00 price-diff nia-pell
2026-01-20 INV-M-0048 PO-30048 S-7022 moss-freight 1400.00 qty-diff owen-brice
2026-01-21 INV-M-0049 PO-30049 S-1044 bramble-tin 1425.00 no-receipt rowan-hale
2026-01-21 INV-M-0050 PO-30050 S-2210 lowlamp-paper 1450.00 matched -
2026-01-21 INV-M-0051 PO-30051 S-0881 kite-and-coil 1475.00 matched -
2026-01-21 INV-M-0052 PO-30052 S-3301 yellow-dock 1500.00 matched -
2026-01-22 INV-M-0053 PO-30053 S-0770 pell-and-murmur 1525.00 matched -
2026-01-22 INV-M-0054 PO-30054 S-4419 glassbarley 1550.00 price-diff owen-brice
2026-01-22 INV-M-0055 PO-30055 S-6155 two-river 1575.00 qty-diff rowan-hale
2026-01-22 INV-M-0056 PO-30056 S-7022 moss-freight 1600.00 no-receipt nia-pell
2026-01-23 INV-M-0057 PO-30057 S-1044 bramble-tin 1625.00 matched -
2026-01-23 INV-M-0058 PO-30058 S-2210 lowlamp-paper 1650.00 matched -
2026-01-23 INV-M-0059 PO-30059 S-0881 kite-and-coil 1675.00 matched -
2026-01-23 INV-M-0060 PO-30060 S-3301 yellow-dock 1700.00 matched -
2026-01-26 INV-M-0061 PO-30061 S-0770 pell-and-murmur 1725.00 price-diff rowan-hale
2026-01-26 INV-M-0062 PO-30062 S-4419 glassbarley 1750.00 qty-diff nia-pell
2026-01-26 INV-M-0063 PO-30063 S-6155 two-river 1775.00 no-receipt owen-brice
2026-01-26 INV-M-0064 PO-30064 S-7022 moss-freight 1800.00 matched -
2026-01-27 INV-M-0065 PO-30065 S-1044 bramble-tin 1825.00 matched -
2026-01-27 INV-M-0066 PO-30066 S-2210 lowlamp-paper 1850.00 matched -
2026-01-27 INV-M-0067 PO-30067 S-0881 kite-and-coil 1875.00 matched -
2026-01-27 INV-M-0068 PO-30068 S-3301 yellow-dock 1900.00 price-diff nia-pell
2026-01-28 INV-M-0069 PO-30069 S-0770 pell-and-murmur 1925.00 qty-diff owen-brice
2026-01-28 INV-M-0070 PO-30070 S-4419 glassbarley 1950.00 no-receipt rowan-hale
2026-01-28 INV-M-0071 PO-30071 S-6155 two-river 1975.00 matched -
2026-01-28 INV-M-0072 PO-30072 S-7022 moss-freight 2000.00 matched -
2026-01-29 INV-M-0073 PO-30073 S-1044 bramble-tin 2025.00 matched -
2026-01-29 INV-M-0074 PO-30074 S-2210 lowlamp-paper 2050.00 matched -
2026-01-29 INV-M-0075 PO-30075 S-0881 kite-and-coil 2075.00 price-diff owen-brice
2026-01-29 INV-M-0076 PO-30076 S-3301 yellow-dock 2100.00 qty-diff rowan-hale
2026-01-30 INV-M-0077 PO-30077 S-0770 pell-and-murmur 2125.00 no-receipt nia-pell
2026-01-30 INV-M-0078 PO-30078 S-4419 glassbarley 2150.00 matched -
2026-01-30 INV-M-0079 PO-30079 S-6155 two-river 2175.00 matched -
2026-01-30 INV-M-0080 PO-30080 S-7022 moss-freight 200.00 matched -
2026-02-02 INV-M-0081 PO-30081 S-1044 bramble-tin 225.00 matched -
2026-02-02 INV-M-0082 PO-30082 S-2210 lowlamp-paper 250.00 price-diff rowan-hale
2026-02-02 INV-M-0083 PO-30083 S-0881 kite-and-coil 275.00 qty-diff nia-pell
2026-02-02 INV-M-0084 PO-30084 S-3301 yellow-dock 300.00 no-receipt owen-brice
2026-02-03 INV-M-0085 PO-30085 S-0770 pell-and-murmur 325.00 matched -
2026-02-03 INV-M-0086 PO-30086 S-4419 glassbarley 350.00 matched -
2026-02-03 INV-M-0087 PO-30087 S-6155 two-river 375.00 matched -
2026-02-03 INV-M-0088 PO-30088 S-7022 moss-freight 400.00 matched -
2026-02-04 INV-M-0089 PO-30089 S-1044 bramble-tin 425.00 price-diff nia-pell
2026-02-04 INV-M-0090 PO-30090 S-2210 lowlamp-paper 450.00 qty-diff owen-brice
2026-02-04 INV-M-0091 PO-30091 S-0881 kite-and-coil 475.00 no-receipt rowan-hale
2026-02-04 INV-M-0092 PO-30092 S-3301 yellow-dock 500.00 matched -
2026-02-05 INV-M-0093 PO-30093 S-0770 pell-and-murmur 525.00 matched -
2026-02-05 INV-M-0094 PO-30094 S-4419 glassbarley 550.00 matched -
2026-02-05 INV-M-0095 PO-30095 S-6155 two-river 575.00 matched -
2026-02-05 INV-M-0096 PO-30096 S-7022 moss-freight 600.00 price-diff owen-brice
2026-02-06 INV-M-0097 PO-30097 S-1044 bramble-tin 625.00 qty-diff rowan-hale
2026-02-06 INV-M-0098 PO-30098 S-2210 lowlamp-paper 650.00 no-receipt nia-pell
2026-02-06 INV-M-0099 PO-30099 S-0881 kite-and-coil 675.00 matched -
2026-02-06 INV-M-0100 PO-30100 S-3301 yellow-dock 700.00 matched -
2026-02-09 INV-M-0101 PO-30101 S-0770 pell-and-murmur 725.00 matched -
2026-02-09 INV-M-0102 PO-30102 S-4419 glassbarley 750.00 matched -
2026-02-09 INV-M-0103 PO-30103 S-6155 two-river 775.00 price-diff rowan-hale
2026-02-09 INV-M-0104 PO-30104 S-7022 moss-freight 800.00 qty-diff nia-pell
2026-02-10 INV-M-0105 PO-30105 S-1044 bramble-tin 825.00 no-receipt owen-brice
2026-02-10 INV-M-0106 PO-30106 S-2210 lowlamp-paper 850.00 matched -
2026-02-10 INV-M-0107 PO-30107 S-0881 kite-and-coil 875.00 matched -
2026-02-10 INV-M-0108 PO-30108 S-3301 yellow-dock 900.00 matched -
2026-02-11 INV-M-0109 PO-30109 S-0770 pell-and-murmur 925.00 matched -
2026-02-11 INV-M-0110 PO-30110 S-4419 glassbarley 950.00 price-diff nia-pell
2026-02-11 INV-M-0111 PO-30111 S-6155 two-river 975.00 qty-diff owen-brice
2026-02-11 INV-M-0112 PO-30112 S-7022 moss-freight 1000.00 no-receipt rowan-hale
2026-02-12 INV-M-0113 PO-30113 S-1044 bramble-tin 1025.00 matched -
2026-02-12 INV-M-0114 PO-30114 S-2210 lowlamp-paper 1050.00 matched -
2026-02-12 INV-M-0115 PO-30115 S-0881 kite-and-coil 1075.00 matched -
2026-02-12 INV-M-0116 PO-30116 S-3301 yellow-dock 1100.00 matched -
2026-02-13 INV-M-0117 PO-30117 S-0770 pell-and-murmur 1125.00 price-diff owen-brice
2026-02-13 INV-M-0118 PO-30118 S-4419 glassbarley 1150.00 qty-diff rowan-hale
2026-02-13 INV-M-0119 PO-30119 S-6155 two-river 1175.00 no-receipt nia-pell
2026-02-13 INV-M-0120 PO-30120 S-7022 moss-freight 1200.00 matched -
2026-02-16 INV-M-0121 PO-30121 S-1044 bramble-tin 1225.00 matched -
2026-02-16 INV-M-0122 PO-30122 S-2210 lowlamp-paper 1250.00 matched -
2026-02-16 INV-M-0123 PO-30123 S-0881 kite-and-coil 1275.00 matched -
2026-02-16 INV-M-0124 PO-30124 S-3301 yellow-dock 1300.00 price-diff rowan-hale
2026-02-17 INV-M-0125 PO-30125 S-0770 pell-and-murmur 1325.00 qty-diff nia-pell
2026-02-17 INV-M-0126 PO-30126 S-4419 glassbarley 1350.00 no-receipt owen-brice
2026-02-17 INV-M-0127 PO-30127 S-6155 two-river 1375.00 matched -
2026-02-17 INV-M-0128 PO-30128 S-7022 moss-freight 1400.00 matched -
2026-02-18 INV-M-0129 PO-30129 S-1044 bramble-tin 1425.00 matched -
2026-02-18 INV-M-0130 PO-30130 S-2210 lowlamp-paper 1450.00 matched -
2026-02-18 INV-M-0131 PO-30131 S-0881 kite-and-coil 1475.00 price-diff nia-pell
2026-02-18 INV-M-0132 PO-30132 S-3301 yellow-dock 1500.00 qty-diff owen-brice
2026-02-19 INV-M-0133 PO-30133 S-0770 pell-and-murmur 1525.00 no-receipt rowan-hale
2026-02-19 INV-M-0134 PO-30134 S-4419 glassbarley 1550.00 matched -
2026-02-19 INV-M-0135 PO-30135 S-6155 two-river 1575.00 matched -
2026-02-19 INV-M-0136 PO-30136 S-7022 moss-freight 1600.00 matched -
2026-02-20 INV-M-0137 PO-30137 S-1044 bramble-tin 1625.00 matched -
2026-02-20 INV-M-0138 PO-30138 S-2210 lowlamp-paper 1650.00 price-diff owen-brice
2026-02-20 INV-M-0139 PO-30139 S-0881 kite-and-coil 1675.00 qty-diff rowan-hale
2026-02-20 INV-M-0140 PO-30140 S-3301 yellow-dock 1700.00 no-receipt nia-pell
2026-02-23 INV-M-0141 PO-30141 S-0770 pell-and-murmur 1725.00 matched -
2026-02-23 INV-M-0142 PO-30142 S-4419 glassbarley 1750.00 matched -
2026-02-23 INV-M-0143 PO-30143 S-6155 two-river 1775.00 matched -
2026-02-23 INV-M-0144 PO-30144 S-7022 moss-freight 1800.00 matched -
2026-02-24 INV-M-0145 PO-30145 S-1044 bramble-tin 1825.00 price-diff rowan-hale
2026-02-24 INV-M-0146 PO-30146 S-2210 lowlamp-paper 1850.00 qty-diff nia-pell
2026-02-24 INV-M-0147 PO-30147 S-0881 kite-and-coil 1875.00 no-receipt owen-brice
2026-02-24 INV-M-0148 PO-30148 S-3301 yellow-dock 1900.00 matched -
2026-02-25 INV-M-0149 PO-30149 S-0770 pell-and-murmur 1925.00 matched -
2026-02-25 INV-M-0150 PO-30150 S-4419 glassbarley 1950.00 matched -
2026-02-25 INV-M-0151 PO-30151 S-6155 two-river 1975.00 matched -
2026-02-25 INV-M-0152 PO-30152 S-7022 moss-freight 2000.00 price-diff nia-pell
2026-02-26 INV-M-0153 PO-30153 S-1044 bramble-tin 2025.00 qty-diff owen-brice
2026-02-26 INV-M-0154 PO-30154 S-2210 lowlamp-paper 2050.00 no-receipt rowan-hale
2026-02-26 INV-M-0155 PO-30155 S-0881 kite-and-coil 2075.00 matched -
2026-02-26 INV-M-0156 PO-30156 S-3301 yellow-dock 2100.00 matched -
2026-02-27 INV-M-0157 PO-30157 S-0770 pell-and-murmur 2125.00 matched -
2026-02-27 INV-M-0158 PO-30158 S-4419 glassbarley 2150.00 matched -
2026-02-27 INV-M-0159 PO-30159 S-6155 two-river 2175.00 price-diff owen-brice
2026-02-27 INV-M-0160 PO-30160 S-7022 moss-freight 200.00 qty-diff rowan-hale
2026-03-02 INV-M-0161 PO-30161 S-1044 bramble-tin 225.00 no-receipt nia-pell
2026-03-02 INV-M-0162 PO-30162 S-2210 lowlamp-paper 250.00 matched -
2026-03-02 INV-M-0163 PO-30163 S-0881 kite-and-coil 275.00 matched -
2026-03-02 INV-M-0164 PO-30164 S-3301 yellow-dock 300.00 matched -
2026-03-03 INV-M-0165 PO-30165 S-0770 pell-and-murmur 325.00 matched -
2026-03-03 INV-M-0166 PO-30166 S-4419 glassbarley 350.00 price-diff rowan-hale
2026-03-03 INV-M-0167 PO-30167 S-6155 two-river 375.00 qty-diff nia-pell
2026-03-03 INV-M-0168 PO-30168 S-7022 moss-freight 400.00 no-receipt owen-brice
2026-03-04 INV-M-0169 PO-30169 S-1044 bramble-tin 425.00 matched -
2026-03-04 INV-M-0170 PO-30170 S-2210 lowlamp-paper 450.00 matched -
2026-03-04 INV-M-0171 PO-30171 S-0881 kite-and-coil 475.00 matched -
2026-03-04 INV-M-0172 PO-30172 S-3301 yellow-dock 500.00 matched -
2026-03-05 INV-M-0173 PO-30173 S-0770 pell-and-murmur 525.00 price-diff nia-pell
2026-03-05 INV-M-0174 PO-30174 S-4419 glassbarley 550.00 qty-diff owen-brice
2026-03-05 INV-M-0175 PO-30175 S-6155 two-river 575.00 no-receipt rowan-hale
2026-03-05 INV-M-0176 PO-30176 S-7022 moss-freight 600.00 matched -
2026-03-06 INV-M-0177 PO-30177 S-1044 bramble-tin 625.00 matched -
2026-03-06 INV-M-0178 PO-30178 S-2210 lowlamp-paper 650.00 matched -
2026-03-06 INV-M-0179 PO-30179 S-0881 kite-and-coil 675.00 matched -
2026-03-06 INV-M-0180 PO-30180 S-3301 yellow-dock 700.00 price-diff owen-brice
2026-03-09 INV-M-0181 PO-30181 S-0770 pell-and-murmur 725.00 qty-diff rowan-hale
2026-03-09 INV-M-0182 PO-30182 S-4419 glassbarley 750.00 no-receipt nia-pell
2026-03-09 INV-M-0183 PO-30183 S-6155 two-river 775.00 matched -
2026-03-09 INV-M-0184 PO-30184 S-7022 moss-freight 800.00 matched -
2026-03-10 INV-M-0185 PO-30185 S-1044 bramble-tin 825.00 matched -
2026-03-10 INV-M-0186 PO-30186 S-2210 lowlamp-paper 850.00 matched -
2026-03-10 INV-M-0187 PO-30187 S-0881 kite-and-coil 875.00 price-diff rowan-hale
2026-03-10 INV-M-0188 PO-30188 S-3301 yellow-dock 900.00 qty-diff nia-pell
2026-03-11 INV-M-0189 PO-30189 S-0770 pell-and-murmur 925.00 no-receipt owen-brice
2026-03-11 INV-M-0190 PO-30190 S-4419 glassbarley 950.00 matched -
2026-03-11 INV-M-0191 PO-30191 S-6155 two-river 975.00 matched -
2026-03-11 INV-M-0192 PO-30192 S-7022 moss-freight 1000.00 matched -
2026-03-12 INV-M-0193 PO-30193 S-1044 bramble-tin 1025.00 matched -
2026-03-12 INV-M-0194 PO-30194 S-2210 lowlamp-paper 1050.00 price-diff nia-pell
2026-03-12 INV-M-0195 PO-30195 S-0881 kite-and-coil 1075.00 qty-diff owen-brice
2026-03-12 INV-M-0196 PO-30196 S-3301 yellow-dock 1100.00 no-receipt rowan-hale
2026-03-13 INV-M-0197 PO-30197 S-0770 pell-and-murmur 1125.00 matched -
2026-03-13 INV-M-0198 PO-30198 S-4419 glassbarley 1150.00 matched -
2026-03-13 INV-M-0199 PO-30199 S-6155 two-river 1175.00 matched -
2026-03-13 INV-M-0200 PO-30200 S-7022 moss-freight 1200.00 matched -
2026-03-16 INV-M-0201 PO-30201 S-1044 bramble-tin 1225.00 price-diff owen-brice
2026-03-16 INV-M-0202 PO-30202 S-2210 lowlamp-paper 1250.00 qty-diff rowan-hale
2026-03-16 INV-M-0203 PO-30203 S-0881 kite-and-coil 1275.00 no-receipt nia-pell
2026-03-16 INV-M-0204 PO-30204 S-3301 yellow-dock 1300.00 matched -
2026-03-17 INV-M-0205 PO-30205 S-0770 pell-and-murmur 1325.00 matched -
2026-03-17 INV-M-0206 PO-30206 S-4419 glassbarley 1350.00 matched -
2026-03-17 INV-M-0207 PO-30207 S-6155 two-river 1375.00 matched -
2026-03-17 INV-M-0208 PO-30208 S-7022 moss-freight 1400.00 price-diff rowan-hale
2026-03-18 INV-M-0209 PO-30209 S-1044 bramble-tin 1425.00 qty-diff nia-pell
2026-03-18 INV-M-0210 PO-30210 S-2210 lowlamp-paper 1450.00 no-receipt owen-brice
2026-03-18 INV-M-0211 PO-30211 S-0881 kite-and-coil 1475.00 matched -
2026-03-18 INV-M-0212 PO-30212 S-3301 yellow-dock 1500.00 matched -
2026-03-19 INV-M-0213 PO-30213 S-0770 pell-and-murmur 1525.00 matched -
2026-03-19 INV-M-0214 PO-30214 S-4419 glassbarley 1550.00 matched -
2026-03-19 INV-M-0215 PO-30215 S-6155 two-river 1575.00 price-diff nia-pell
2026-03-19 INV-M-0216 PO-30216 S-7022 moss-freight 1600.00 qty-diff owen-brice
2026-03-20 INV-M-0217 PO-30217 S-1044 bramble-tin 1625.00 no-receipt rowan-hale
2026-03-20 INV-M-0218 PO-30218 S-2210 lowlamp-paper 1650.00 matched -
2026-03-20 INV-M-0219 PO-30219 S-0881 kite-and-coil 1675.00 matched -
2026-03-20 INV-M-0220 PO-30220 S-3301 yellow-dock 1700.00 matched -
2026-03-23 INV-M-0221 PO-30221 S-0770 pell-and-murmur 1725.00 matched -
2026-03-23 INV-M-0222 PO-30222 S-4419 glassbarley 1750.00 price-diff owen-brice
2026-03-23 INV-M-0223 PO-30223 S-6155 two-river 1775.00 qty-diff rowan-hale
2026-03-23 INV-M-0224 PO-30224 S-7022 moss-freight 1800.00 no-receipt nia-pell
2026-03-24 INV-M-0225 PO-30225 S-1044 bramble-tin 1825.00 matched -
2026-03-24 INV-M-0226 PO-30226 S-2210 lowlamp-paper 1850.00 matched -
2026-03-24 INV-M-0227 PO-30227 S-0881 kite-and-coil 1875.00 matched -
2026-03-24 INV-M-0228 PO-30228 S-3301 yellow-dock 1900.00 matched -
2026-03-25 INV-M-0229 PO-30229 S-0770 pell-and-murmur 1925.00 price-diff rowan-hale
2026-03-25 INV-M-0230 PO-30230 S-4419 glassbarley 1950.00 qty-diff nia-pell
2026-03-25 INV-M-0231 PO-30231 S-6155 two-river 1975.00 no-receipt owen-brice
2026-03-25 INV-M-0232 PO-30232 S-7022 moss-freight 2000.00 matched -
2026-03-26 INV-M-0233 PO-30233 S-1044 bramble-tin 2025.00 matched -
2026-03-26 INV-M-0234 PO-30234 S-2210 lowlamp-paper 2050.00 matched -
2026-03-26 INV-M-0235 PO-30235 S-0881 kite-and-coil 2075.00 matched -
2026-03-26 INV-M-0236 PO-30236 S-3301 yellow-dock 2100.00 price-diff nia-pell
2026-03-27 INV-M-0237 PO-30237 S-0770 pell-and-murmur 2125.00 qty-diff owen-brice
2026-03-27 INV-M-0238 PO-30238 S-4419 glassbarley 2150.00 no-receipt rowan-hale
2026-03-27 INV-M-0239 PO-30239 S-6155 two-river 2175.00 matched -
2026-03-27 INV-M-0240 PO-30240 S-7022 moss-freight 200.00 matched -
2026-03-30 INV-M-0241 PO-30241 S-1044 bramble-tin 225.00 matched -
2026-03-30 INV-M-0242 PO-30242 S-2210 lowlamp-paper 250.00 matched -
2026-03-30 INV-M-0243 PO-30243 S-0881 kite-and-coil 275.00 price-diff owen-brice
2026-03-30 INV-M-0244 PO-30244 S-3301 yellow-dock 300.00 qty-diff rowan-hale
2026-03-31 INV-M-0245 PO-30245 S-0770 pell-and-murmur 325.00 no-receipt nia-pell
2026-03-31 INV-M-0246 PO-30246 S-4419 glassbarley 350.00 matched -
2026-03-31 INV-M-0247 PO-30247 S-6155 two-river 375.00 matched -
2026-03-31 INV-M-0248 PO-30248 S-7022 moss-freight 400.00 matched -
2026-04-01 INV-M-0249 PO-30249 S-1044 bramble-tin 425.00 matched -
2026-04-01 INV-M-0250 PO-30250 S-2210 lowlamp-paper 450.00 price-diff rowan-hale
2026-04-01 INV-M-0251 PO-30251 S-0881 kite-and-coil 475.00 qty-diff nia-pell
2026-04-01 INV-M-0252 PO-30252 S-3301 yellow-dock 500.00 no-receipt owen-brice
2026-04-02 INV-M-0253 PO-30253 S-0770 pell-and-murmur 525.00 matched -
2026-04-02 INV-M-0254 PO-30254 S-4419 glassbarley 550.00 matched -
2026-04-02 INV-M-0255 PO-30255 S-6155 two-river 575.00 matched -
2026-04-02 INV-M-0256 PO-30256 S-7022 moss-freight 600.00 matched -
2026-04-03 INV-M-0257 PO-30257 S-1044 bramble-tin 625.00 price-diff nia-pell
2026-04-03 INV-M-0258 PO-30258 S-2210 lowlamp-paper 650.00 qty-diff owen-brice
2026-04-03 INV-M-0259 PO-30259 S-0881 kite-and-coil 675.00 no-receipt rowan-hale
2026-04-03 INV-M-0260 PO-30260 S-3301 yellow-dock 700.00 matched -
2026-04-06 INV-M-0261 PO-30261 S-0770 pell-and-murmur 725.00 matched -
2026-04-06 INV-M-0262 PO-30262 S-4419 glassbarley 750.00 matched -
2026-04-06 INV-M-0263 PO-30263 S-6155 two-river 775.00 matched -
2026-04-06 INV-M-0264 PO-30264 S-7022 moss-freight 800.00 price-diff owen-brice
2026-04-07 INV-M-0265 PO-30265 S-1044 bramble-tin 825.00 qty-diff rowan-hale
2026-04-07 INV-M-0266 PO-30266 S-2210 lowlamp-paper 850.00 no-receipt nia-pell
2026-04-07 INV-M-0267 PO-30267 S-0881 kite-and-coil 875.00 matched -
2026-04-07 INV-M-0268 PO-30268 S-3301 yellow-dock 900.00 matched -
2026-04-08 INV-M-0269 PO-30269 S-0770 pell-and-murmur 925.00 matched -
2026-04-08 INV-M-0270 PO-30270 S-4419 glassbarley 950.00 matched -
2026-04-08 INV-M-0271 PO-30271 S-6155 two-river 975.00 price-diff rowan-hale
2026-04-08 INV-M-0272 PO-30272 S-7022 moss-freight 1000.00 qty-diff nia-pell
2026-04-09 INV-M-0273 PO-30273 S-1044 bramble-tin 1025.00 no-receipt owen-brice
2026-04-09 INV-M-0274 PO-30274 S-2210 lowlamp-paper 1050.00 matched -
2026-04-09 INV-M-0275 PO-30275 S-0881 kite-and-coil 1075.00 matched -
2026-04-09 INV-M-0276 PO-30276 S-3301 yellow-dock 1100.00 matched -
2026-04-10 INV-M-0277 PO-30277 S-0770 pell-and-murmur 1125.00 matched -
2026-04-10 INV-M-0278 PO-30278 S-4419 glassbarley 1150.00 price-diff nia-pell
2026-04-10 INV-M-0279 PO-30279 S-6155 two-river 1175.00 qty-diff owen-brice
2026-04-10 INV-M-0280 PO-30280 S-7022 moss-freight 1200.00 no-receipt rowan-hale
2026-04-13 INV-M-0281 PO-30281 S-1044 bramble-tin 1225.00 matched -
2026-04-13 INV-M-0282 PO-30282 S-2210 lowlamp-paper 1250.00 matched -
2026-04-13 INV-M-0283 PO-30283 S-0881 kite-and-coil 1275.00 matched -
2026-04-13 INV-M-0284 PO-30284 S-3301 yellow-dock 1300.00 matched -
2026-04-14 INV-M-0285 PO-30285 S-0770 pell-and-murmur 1325.00 price-diff owen-brice
2026-04-14 INV-M-0286 PO-30286 S-4419 glassbarley 1350.00 qty-diff rowan-hale
2026-04-14 INV-M-0287 PO-30287 S-6155 two-river 1375.00 no-receipt nia-pell
2026-04-14 INV-M-0288 PO-30288 S-7022 moss-freight 1400.00 matched -
2026-04-15 INV-M-0289 PO-30289 S-1044 bramble-tin 1425.00 matched -
2026-04-15 INV-M-0290 PO-30290 S-2210 lowlamp-paper 1450.00 matched -
2026-04-15 INV-M-0291 PO-30291 S-0881 kite-and-coil 1475.00 matched -
2026-04-15 INV-M-0292 PO-30292 S-3301 yellow-dock 1500.00 price-diff rowan-hale
2026-04-16 INV-M-0293 PO-30293 S-0770 pell-and-murmur 1525.00 qty-diff nia-pell
2026-04-16 INV-M-0294 PO-30294 S-4419 glassbarley 1550.00 no-receipt owen-brice
2026-04-16 INV-M-0295 PO-30295 S-6155 two-river 1575.00 matched -
2026-04-16 INV-M-0296 PO-30296 S-7022 moss-freight 1600.00 matched -
2026-04-17 INV-M-0297 PO-30297 S-1044 bramble-tin 1625.00 matched -
2026-04-17 INV-M-0298 PO-30298 S-2210 lowlamp-paper 1650.00 matched -
2026-04-17 INV-M-0299 PO-30299 S-0881 kite-and-coil 1675.00 price-diff nia-pell
2026-04-17 INV-M-0300 PO-30300 S-3301 yellow-dock 1700.00 qty-diff owen-brice
2026-04-20 INV-M-0301 PO-30301 S-0770 pell-and-murmur 1725.00 no-receipt rowan-hale
2026-04-20 INV-M-0302 PO-30302 S-4419 glassbarley 1750.00 matched -
2026-04-20 INV-M-0303 PO-30303 S-6155 two-river 1775.00 matched -
2026-04-20 INV-M-0304 PO-30304 S-7022 moss-freight 1800.00 matched -
2026-04-21 INV-M-0305 PO-30305 S-1044 bramble-tin 1825.00 matched -
2026-04-21 INV-M-0306 PO-30306 S-2210 lowlamp-paper 1850.00 price-diff owen-brice
2026-04-21 INV-M-0307 PO-30307 S-0881 kite-and-coil 1875.00 qty-diff rowan-hale
2026-04-21 INV-M-0308 PO-30308 S-3301 yellow-dock 1900.00 no-receipt nia-pell
2026-04-22 INV-M-0309 PO-30309 S-0770 pell-and-murmur 1925.00 matched -
2026-04-22 INV-M-0310 PO-30310 S-4419 glassbarley 1950.00 matched -
2026-04-22 INV-M-0311 PO-30311 S-6155 two-river 1975.00 matched -
2026-04-22 INV-M-0312 PO-30312 S-7022 moss-freight 2000.00 matched -
2026-04-23 INV-M-0313 PO-30313 S-1044 bramble-tin 2025.00 price-diff rowan-hale
2026-04-23 INV-M-0314 PO-30314 S-2210 lowlamp-paper 2050.00 qty-diff nia-pell
2026-04-23 INV-M-0315 PO-30315 S-0881 kite-and-coil 2075.00 no-receipt owen-brice
2026-04-23 INV-M-0316 PO-30316 S-3301 yellow-dock 2100.00 matched -
2026-04-24 INV-M-0317 PO-30317 S-0770 pell-and-murmur 2125.00 matched -
2026-04-24 INV-M-0318 PO-30318 S-4419 glassbarley 2150.00 matched -
2026-04-24 INV-M-0319 PO-30319 S-6155 two-river 2175.00 matched -
2026-04-24 INV-M-0320 PO-30320 S-7022 moss-freight 200.00 price-diff nia-pell
2026-04-27 INV-M-0321 PO-30321 S-1044 bramble-tin 225.00 qty-diff owen-brice
2026-04-27 INV-M-0322 PO-30322 S-2210 lowlamp-paper 250.00 no-receipt rowan-hale
2026-04-27 INV-M-0323 PO-30323 S-0881 kite-and-coil 275.00 matched -
2026-04-27 INV-M-0324 PO-30324 S-3301 yellow-dock 300.00 matched -
2026-04-28 INV-M-0325 PO-30325 S-0770 pell-and-murmur 325.00 matched -
2026-04-28 INV-M-0326 PO-30326 S-4419 glassbarley 350.00 matched -
2026-04-28 INV-M-0327 PO-30327 S-6155 two-river 375.00 price-diff owen-brice
2026-04-28 INV-M-0328 PO-30328 S-7022 moss-freight 400.00 qty-diff rowan-hale
2026-04-29 INV-M-0329 PO-30329 S-1044 bramble-tin 425.00 no-receipt nia-pell
2026-04-29 INV-M-0330 PO-30330 S-2210 lowlamp-paper 450.00 matched -
2026-04-29 INV-M-0331 PO-30331 S-0881 kite-and-coil 475.00 matched -
2026-04-29 INV-M-0332 PO-30332 S-3301 yellow-dock 500.00 matched -
2026-04-30 INV-M-0333 PO-30333 S-0770 pell-and-murmur 525.00 matched -
2026-04-30 INV-M-0334 PO-30334 S-4419 glassbarley 550.00 price-diff rowan-hale
2026-04-30 INV-M-0335 PO-30335 S-6155 two-river 575.00 qty-diff nia-pell
2026-04-30 INV-M-0336 PO-30336 S-7022 moss-freight 600.00 no-receipt owen-brice
2026-05-01 INV-M-0337 PO-30337 S-1044 bramble-tin 625.00 matched -
2026-05-01 INV-M-0338 PO-30338 S-2210 lowlamp-paper 650.00 matched -
2026-05-01 INV-M-0339 PO-30339 S-0881 kite-and-coil 675.00 matched -
2026-05-01 INV-M-0340 PO-30340 S-3301 yellow-dock 700.00 matched -
2026-05-04 INV-M-0341 PO-30341 S-0770 pell-and-murmur 725.00 price-diff nia-pell
2026-05-04 INV-M-0342 PO-30342 S-4419 glassbarley 750.00 qty-diff owen-brice
2026-05-04 INV-M-0343 PO-30343 S-6155 two-river 775.00 no-receipt rowan-hale
2026-05-04 INV-M-0344 PO-30344 S-7022 moss-freight 800.00 matched -
2026-05-05 INV-M-0345 PO-30345 S-1044 bramble-tin 825.00 matched -
2026-05-05 INV-M-0346 PO-30346 S-2210 lowlamp-paper 850.00 matched -
2026-05-05 INV-M-0347 PO-30347 S-0881 kite-and-coil 875.00 matched -
2026-05-05 INV-M-0348 PO-30348 S-3301 yellow-dock 900.00 price-diff owen-brice
2026-05-06 INV-M-0349 PO-30349 S-0770 pell-and-murmur 925.00 qty-diff rowan-hale
2026-05-06 INV-M-0350 PO-30350 S-4419 glassbarley 950.00 no-receipt nia-pell
2026-05-06 INV-M-0351 PO-30351 S-6155 two-river 975.00 matched -
2026-05-06 INV-M-0352 PO-30352 S-7022 moss-freight 1000.00 matched -
2026-05-07 INV-M-0353 PO-30353 S-1044 bramble-tin 1025.00 matched -
2026-05-07 INV-M-0354 PO-30354 S-2210 lowlamp-paper 1050.00 matched -
2026-05-07 INV-M-0355 PO-30355 S-0881 kite-and-coil 1075.00 price-diff rowan-hale
2026-05-07 INV-M-0356 PO-30356 S-3301 yellow-dock 1100.00 qty-diff nia-pell
2026-05-08 INV-M-0357 PO-30357 S-0770 pell-and-murmur 1125.00 no-receipt owen-brice
2026-05-08 INV-M-0358 PO-30358 S-4419 glassbarley 1150.00 matched -
2026-05-08 INV-M-0359 PO-30359 S-6155 two-river 1175.00 matched -
2026-05-08 INV-M-0360 PO-30360 S-7022 moss-freight 1200.00 matched -
2026-05-11 INV-M-0361 PO-30361 S-1044 bramble-tin 1225.00 matched -
2026-05-11 INV-M-0362 PO-30362 S-2210 lowlamp-paper 1250.00 price-diff nia-pell
2026-05-11 INV-M-0363 PO-30363 S-0881 kite-and-coil 1275.00 qty-diff owen-brice
2026-05-11 INV-M-0364 PO-30364 S-3301 yellow-dock 1300.00 no-receipt rowan-hale
2026-05-12 INV-M-0365 PO-30365 S-0770 pell-and-murmur 1325.00 matched -
2026-05-12 INV-M-0366 PO-30366 S-4419 glassbarley 1350.00 matched -
2026-05-12 INV-M-0367 PO-30367 S-6155 two-river 1375.00 matched -
2026-05-12 INV-M-0368 PO-30368 S-7022 moss-freight 1400.00 matched -
2026-05-13 INV-M-0369 PO-30369 S-1044 bramble-tin 1425.00 price-diff owen-brice
2026-05-13 INV-M-0370 PO-30370 S-2210 lowlamp-paper 1450.00 qty-diff rowan-hale
2026-05-13 INV-M-0371 PO-30371 S-0881 kite-and-coil 1475.00 no-receipt nia-pell
2026-05-13 INV-M-0372 PO-30372 S-3301 yellow-dock 1500.00 matched -
2026-05-14 INV-M-0373 PO-30373 S-0770 pell-and-murmur 1525.00 matched -
2026-05-14 INV-M-0374 PO-30374 S-4419 glassbarley 1550.00 matched -
2026-05-14 INV-M-0375 PO-30375 S-6155 two-river 1575.00 matched -
2026-05-14 INV-M-0376 PO-30376 S-7022 moss-freight 1600.00 price-diff rowan-hale
2026-05-15 INV-M-0377 PO-30377 S-1044 bramble-tin 1625.00 qty-diff nia-pell
2026-05-15 INV-M-0378 PO-30378 S-2210 lowlamp-paper 1650.00 no-receipt owen-brice
2026-05-15 INV-M-0379 PO-30379 S-0881 kite-and-coil 1675.00 matched -
2026-05-15 INV-M-0380 PO-30380 S-3301 yellow-dock 1700.00 matched -
2026-05-18 INV-M-0381 PO-30381 S-0770 pell-and-murmur 1725.00 matched -
2026-05-18 INV-M-0382 PO-30382 S-4419 glassbarley 1750.00 matched -
2026-05-18 INV-M-0383 PO-30383 S-6155 two-river 1775.00 price-diff nia-pell
2026-05-18 INV-M-0384 PO-30384 S-7022 moss-freight 1800.00 qty-diff owen-brice
2026-05-19 INV-M-0385 PO-30385 S-1044 bramble-tin 1825.00 no-receipt rowan-hale
2026-05-19 INV-M-0386 PO-30386 S-2210 lowlamp-paper 1850.00 matched -
2026-05-19 INV-M-0387 PO-30387 S-0881 kite-and-coil 1875.00 matched -
2026-05-19 INV-M-0388 PO-30388 S-3301 yellow-dock 1900.00 matched -
2026-05-20 INV-M-0389 PO-30389 S-0770 pell-and-murmur 1925.00 matched -
2026-05-20 INV-M-0390 PO-30390 S-4419 glassbarley 1950.00 price-diff owen-brice
2026-05-20 INV-M-0391 PO-30391 S-6155 two-river 1975.00 qty-diff rowan-hale
2026-05-20 INV-M-0392 PO-30392 S-7022 moss-freight 2000.00 no-receipt nia-pell
2026-05-21 INV-M-0393 PO-30393 S-1044 bramble-tin 2025.00 matched -
2026-05-21 INV-M-0394 PO-30394 S-2210 lowlamp-paper 2050.00 matched -
2026-05-21 INV-M-0395 PO-30395 S-0881 kite-and-coil 2075.00 matched -
2026-05-21 INV-M-0396 PO-30396 S-3301 yellow-dock 2100.00 matched -
2026-05-22 INV-M-0397 PO-30397 S-0770 pell-and-murmur 2125.00 price-diff rowan-hale
2026-05-22 INV-M-0398 PO-30398 S-4419 glassbarley 2150.00 qty-diff nia-pell
2026-05-22 INV-M-0399 PO-30399 S-6155 two-river 2175.00 no-receipt owen-brice
2026-05-22 INV-M-0400 PO-30400 S-7022 moss-freight 200.00 matched -
2026-05-25 INV-M-0401 PO-30401 S-1044 bramble-tin 225.00 matched -
2026-05-25 INV-M-0402 PO-30402 S-2210 lowlamp-paper 250.00 matched -
2026-05-25 INV-M-0403 PO-30403 S-0881 kite-and-coil 275.00 matched -
2026-05-25 INV-M-0404 PO-30404 S-3301 yellow-dock 300.00 price-diff nia-pell
2026-05-26 INV-M-0405 PO-30405 S-0770 pell-and-murmur 325.00 qty-diff owen-brice
2026-05-26 INV-M-0406 PO-30406 S-4419 glassbarley 350.00 no-receipt rowan-hale
2026-05-26 INV-M-0407 PO-30407 S-6155 two-river 375.00 matched -
2026-05-26 INV-M-0408 PO-30408 S-7022 moss-freight 400.00 matched -
2026-05-27 INV-M-0409 PO-30409 S-1044 bramble-tin 425.00 matched -
2026-05-27 INV-M-0410 PO-30410 S-2210 lowlamp-paper 450.00 matched -
2026-05-27 INV-M-0411 PO-30411 S-0881 kite-and-coil 475.00 price-diff owen-brice
2026-05-27 INV-M-0412 PO-30412 S-3301 yellow-dock 500.00 qty-diff rowan-hale
2026-05-28 INV-M-0413 PO-30413 S-0770 pell-and-murmur 525.00 no-receipt nia-pell
2026-05-28 INV-M-0414 PO-30414 S-4419 glassbarley 550.00 matched -
2026-05-28 INV-M-0415 PO-30415 S-6155 two-river 575.00 matched -
2026-05-28 INV-M-0416 PO-30416 S-7022 moss-freight 600.00 matched -
2026-05-29 INV-M-0417 PO-30417 S-1044 bramble-tin 625.00 matched -
2026-05-29 INV-M-0418 PO-30418 S-2210 lowlamp-paper 650.00 price-diff rowan-hale
2026-05-29 INV-M-0419 PO-30419 S-0881 kite-and-coil 675.00 qty-diff nia-pell
2026-05-29 INV-M-0420 PO-30420 S-3301 yellow-dock 700.00 no-receipt owen-brice
2026-06-01 INV-M-0421 PO-30421 S-0770 pell-and-murmur 725.00 matched -
2026-06-01 INV-M-0422 PO-30422 S-4419 glassbarley 750.00 matched -
2026-06-01 INV-M-0423 PO-30423 S-6155 two-river 775.00 matched -
2026-06-01 INV-M-0424 PO-30424 S-7022 moss-freight 800.00 matched -
2026-06-02 INV-M-0425 PO-30425 S-1044 bramble-tin 825.00 price-diff nia-pell
2026-06-02 INV-M-0426 PO-30426 S-2210 lowlamp-paper 850.00 qty-diff owen-brice
2026-06-02 INV-M-0427 PO-30427 S-0881 kite-and-coil 875.00 no-receipt rowan-hale
2026-06-02 INV-M-0428 PO-30428 S-3301 yellow-dock 900.00 matched -
2026-06-03 INV-M-0429 PO-30429 S-0770 pell-and-murmur 925.00 matched -
2026-06-03 INV-M-0430 PO-30430 S-4419 glassbarley 950.00 matched -
2026-06-03 INV-M-0431 PO-30431 S-6155 two-river 975.00 matched -
2026-06-03 INV-M-0432 PO-30432 S-7022 moss-freight 1000.00 price-diff owen-brice
2026-06-04 INV-M-0433 PO-30433 S-1044 bramble-tin 1025.00 qty-diff rowan-hale
2026-06-04 INV-M-0434 PO-30434 S-2210 lowlamp-paper 1050.00 no-receipt nia-pell
2026-06-04 INV-M-0435 PO-30435 S-0881 kite-and-coil 1075.00 matched -
2026-06-04 INV-M-0436 PO-30436 S-3301 yellow-dock 1100.00 matched -
2026-06-05 INV-M-0437 PO-30437 S-0770 pell-and-murmur 1125.00 matched -
2026-06-05 INV-M-0438 PO-30438 S-4419 glassbarley 1150.00 matched -
2026-06-05 INV-M-0439 PO-30439 S-6155 two-river 1175.00 price-diff rowan-hale
2026-06-05 INV-M-0440 PO-30440 S-7022 moss-freight 1200.00 qty-diff nia-pell
2026-06-08 INV-M-0441 PO-30441 S-1044 bramble-tin 1225.00 no-receipt owen-brice
2026-06-08 INV-M-0442 PO-30442 S-2210 lowlamp-paper 1250.00 matched -
2026-06-08 INV-M-0443 PO-30443 S-0881 kite-and-coil 1275.00 matched -
2026-06-08 INV-M-0444 PO-30444 S-3301 yellow-dock 1300.00 matched -
2026-06-09 INV-M-0445 PO-30445 S-0770 pell-and-murmur 1325.00 matched -
2026-06-09 INV-M-0446 PO-30446 S-4419 glassbarley 1350.00 price-diff nia-pell
2026-06-09 INV-M-0447 PO-30447 S-6155 two-river 1375.00 qty-diff owen-brice
2026-06-09 INV-M-0448 PO-30448 S-7022 moss-freight 1400.00 no-receipt rowan-hale
2026-06-10 INV-M-0449 PO-30449 S-1044 bramble-tin 1425.00 matched -
2026-06-10 INV-M-0450 PO-30450 S-2210 lowlamp-paper 1450.00 matched -
2026-06-10 INV-M-0451 PO-30451 S-0881 kite-and-coil 1475.00 matched -
2026-06-10 INV-M-0452 PO-30452 S-3301 yellow-dock 1500.00 matched -
2026-06-11 INV-M-0453 PO-30453 S-0770 pell-and-murmur 1525.00 price-diff owen-brice
2026-06-11 INV-M-0454 PO-30454 S-4419 glassbarley 1550.00 qty-diff rowan-hale
2026-06-11 INV-M-0455 PO-30455 S-6155 two-river 1575.00 no-receipt nia-pell
2026-06-11 INV-M-0456 PO-30456 S-7022 moss-freight 1600.00 matched -
2026-06-12 INV-M-0457 PO-30457 S-1044 bramble-tin 1625.00 matched -
2026-06-12 INV-M-0458 PO-30458 S-2210 lowlamp-paper 1650.00 matched -
2026-06-12 INV-M-0459 PO-30459 S-0881 kite-and-coil 1675.00 matched -
2026-06-12 INV-M-0460 PO-30460 S-3301 yellow-dock 1700.00 price-diff rowan-hale
2026-06-15 INV-M-0461 PO-30461 S-0770 pell-and-murmur 1725.00 qty-diff nia-pell
2026-06-15 INV-M-0462 PO-30462 S-4419 glassbarley 1750.00 no-receipt owen-brice
2026-06-15 INV-M-0463 PO-30463 S-6155 two-river 1775.00 matched -
2026-06-15 INV-M-0464 PO-30464 S-7022 moss-freight 1800.00 matched -
2026-06-16 INV-M-0465 PO-30465 S-1044 bramble-tin 1825.00 matched -
2026-06-16 INV-M-0466 PO-30466 S-2210 lowlamp-paper 1850.00 matched -
2026-06-16 INV-M-0467 PO-30467 S-0881 kite-and-coil 1875.00 price-diff nia-pell
2026-06-16 INV-M-0468 PO-30468 S-3301 yellow-dock 1900.00 qty-diff owen-brice
2026-06-17 INV-M-0469 PO-30469 S-0770 pell-and-murmur 1925.00 no-receipt rowan-hale
2026-06-17 INV-M-0470 PO-30470 S-4419 glassbarley 1950.00 matched -
2026-06-17 INV-M-0471 PO-30471 S-6155 two-river 1975.00 matched -
2026-06-17 INV-M-0472 PO-30472 S-7022 moss-freight 2000.00 matched -
2026-06-18 INV-M-0473 PO-30473 S-1044 bramble-tin 2025.00 matched -
2026-06-18 INV-M-0474 PO-30474 S-2210 lowlamp-paper 2050.00 price-diff owen-brice
2026-06-18 INV-M-0475 PO-30475 S-0881 kite-and-coil 2075.00 qty-diff rowan-hale
2026-06-18 INV-M-0476 PO-30476 S-3301 yellow-dock 2100.00 no-receipt nia-pell
2026-06-19 INV-M-0477 PO-30477 S-0770 pell-and-murmur 2125.00 matched -
2026-06-19 INV-M-0478 PO-30478 S-4419 glassbarley 2150.00 matched -
2026-06-19 INV-M-0479 PO-30479 S-6155 two-river 2175.00 matched -
2026-06-19 INV-M-0480 PO-30480 S-7022 moss-freight 200.00 matched -
2026-06-22 INV-M-0481 PO-30481 S-1044 bramble-tin 225.00 price-diff rowan-hale
2026-06-22 INV-M-0482 PO-30482 S-2210 lowlamp-paper 250.00 qty-diff nia-pell
2026-06-22 INV-M-0483 PO-30483 S-0881 kite-and-coil 275.00 no-receipt owen-brice
2026-06-22 INV-M-0484 PO-30484 S-3301 yellow-dock 300.00 matched -
2026-06-23 INV-M-0485 PO-30485 S-0770 pell-and-murmur 325.00 matched -
2026-06-23 INV-M-0486 PO-30486 S-4419 glassbarley 350.00 matched -
2026-06-23 INV-M-0487 PO-30487 S-6155 two-river 375.00 matched -
2026-06-24 INV-M-0488 PO-30488 S-7022 moss-freight 400.00 price-diff nia-pell
2026-06-24 INV-M-0489 PO-30489 S-1044 bramble-tin 425.00 qty-diff owen-brice
2026-06-24 INV-M-0490 PO-30490 S-2210 lowlamp-paper 450.00 no-receipt rowan-hale
2026-06-25 INV-M-0491 PO-30491 S-0881 kite-and-coil 475.00 matched -
2026-06-25 INV-M-0492 PO-30492 S-3301 yellow-dock 500.00 matched -
2026-06-25 INV-M-0493 PO-30493 S-0770 pell-and-murmur 525.00 matched -
2026-06-26 INV-M-0494 PO-30494 S-4419 glassbarley 550.00 matched -
2026-06-26 INV-M-0495 PO-30495 S-6155 two-river 575.00 price-diff owen-brice
2026-06-26 INV-M-0496 PO-30496 S-7022 moss-freight 600.00 qty-diff rowan-hale
2026-06-29 INV-M-0497 PO-30497 S-1044 bramble-tin 625.00 no-receipt nia-pell
2026-06-29 INV-M-0498 PO-30498 S-2210 lowlamp-paper 650.00 matched -
2026-06-29 INV-M-0499 PO-30499 S-0881 kite-and-coil 675.00 matched -
2026-06-30 INV-M-0500 PO-30500 S-3301 yellow-dock 700.00 matched -
2026-06-30 INV-M-0501 PO-30501 S-0770 pell-and-murmur 725.00 matched -
2026-06-30 INV-M-0502 PO-30502 S-4419 glassbarley 750.00 price-diff rowan-hale
2026-07-01 INV-M-0503 PO-30503 S-6155 two-river 775.00 qty-diff nia-pell
2026-07-01 INV-M-0504 PO-30504 S-7022 moss-freight 800.00 no-receipt owen-brice
2026-07-01 INV-M-0505 PO-30505 S-1044 bramble-tin 825.00 matched -
2026-07-02 INV-M-0506 PO-30506 S-2210 lowlamp-paper 850.00 matched -
2026-07-02 INV-M-0507 PO-30507 S-0881 kite-and-coil 875.00 matched -
2026-07-02 INV-M-0508 PO-30508 S-3301 yellow-dock 900.00 matched -
2026-07-03 INV-M-0509 PO-30509 S-0770 pell-and-murmur 925.00 price-diff nia-pell
2026-07-03 INV-M-0510 PO-30510 S-4419 glassbarley 950.00 qty-diff owen-brice
2026-07-03 INV-M-0511 PO-30511 S-6155 two-river 975.00 no-receipt rowan-hale
2026-07-06 INV-M-0512 PO-30512 S-7022 moss-freight 1000.00 matched -
2026-07-06 INV-M-0513 PO-30513 S-1044 bramble-tin 1025.00 matched -
2026-07-06 INV-M-0514 PO-30514 S-2210 lowlamp-paper 1050.00 matched -
2026-07-07 INV-M-0515 PO-30515 S-0881 kite-and-coil 1075.00 matched -
2026-07-07 INV-M-0516 PO-30516 S-3301 yellow-dock 1100.00 price-diff owen-brice
2026-07-07 INV-M-0517 PO-30517 S-0770 pell-and-murmur 1125.00 qty-diff rowan-hale
2026-07-08 INV-M-0518 PO-30518 S-4419 glassbarley 1150.00 no-receipt nia-pell
2026-07-08 INV-M-0519 PO-30519 S-6155 two-river 1175.00 matched -
2026-07-08 INV-M-0520 PO-30520 S-7022 moss-freight 1200.00 matched -
2026-07-09 INV-M-0521 PO-30521 S-1044 bramble-tin 1225.00 matched -
2026-07-09 INV-M-0522 PO-30522 S-2210 lowlamp-paper 1250.00 matched -
2026-07-09 INV-M-0523 PO-30523 S-0881 kite-and-coil 1275.00 price-diff rowan-hale
2026-07-10 INV-M-0524 PO-30524 S-3301 yellow-dock 1300.00 qty-diff nia-pell
2026-07-10 INV-M-0525 PO-30525 S-0770 pell-and-murmur 1325.00 no-receipt owen-brice
2026-07-10 INV-M-0526 PO-30526 S-4419 glassbarley 1350.00 matched -
2026-07-13 INV-M-0527 PO-30527 S-6155 two-river 1375.00 matched -
2026-07-13 INV-M-0528 PO-30528 S-7022 moss-freight 1400.00 matched -
2026-07-13 INV-M-0529 PO-30529 S-1044 bramble-tin 1425.00 matched -
2026-07-14 INV-M-0530 PO-30530 S-2210 lowlamp-paper 1450.00 price-diff nia-pell
2026-07-14 INV-M-0531 PO-30531 S-0881 kite-and-coil 1475.00 qty-diff owen-brice
2026-07-14 INV-M-0532 PO-30532 S-3301 yellow-dock 1500.00 no-receipt rowan-hale
2026-07-15 INV-M-0533 PO-30533 S-0770 pell-and-murmur 1525.00 matched -
2026-07-15 INV-M-0534 PO-30534 S-4419 glassbarley 1550.00 matched -
2026-07-15 INV-M-0535 PO-30535 S-6155 two-river 1575.00 matched -
2026-07-16 INV-M-0536 PO-30536 S-7022 moss-freight 1600.00 matched -
2026-07-16 INV-M-0537 PO-30537 S-1044 bramble-tin 1625.00 price-diff owen-brice
2026-07-16 INV-M-0538 PO-30538 S-2210 lowlamp-paper 1650.00 qty-diff rowan-hale
2026-07-17 INV-M-0539 PO-30539 S-0881 kite-and-coil 1675.00 no-receipt nia-pell
2026-07-17 INV-M-0540 PO-30540 S-3301 yellow-dock 1700.00 matched -
2026-07-17 INV-M-0541 PO-30541 S-0770 pell-and-murmur 1725.00 matched -
2026-07-20 INV-M-0542 PO-30542 S-4419 glassbarley 1750.00 matched -
2026-07-20 INV-M-0543 PO-30543 S-6155 two-river 1775.00 matched -
2026-07-20 INV-M-0544 PO-30544 S-7022 moss-freight 1800.00 price-diff rowan-hale
2026-07-21 INV-M-0545 PO-30545 S-1044 bramble-tin 1825.00 qty-diff nia-pell
2026-07-21 INV-M-0546 PO-30546 S-2210 lowlamp-paper 1850.00 no-receipt owen-brice
2026-07-21 INV-M-0547 PO-30547 S-0881 kite-and-coil 1875.00 matched -
2026-07-22 INV-M-0548 PO-30548 S-3301 yellow-dock 1900.00 matched -
2026-07-22 INV-M-0549 PO-30549 S-0770 pell-and-murmur 1925.00 matched -
2026-07-22 INV-M-0550 PO-30550 S-4419 glassbarley 1950.00 matched -
2026-07-23 INV-M-0551 PO-30551 S-6155 two-river 1975.00 price-diff nia-pell
2026-07-23 INV-M-0552 PO-30552 S-7022 moss-freight 2000.00 qty-diff owen-brice
2026-07-23 INV-M-0553 PO-30553 S-1044 bramble-tin 2025.00 no-receipt rowan-hale
2026-07-24 INV-M-0554 PO-30554 S-2210 lowlamp-paper 2050.00 matched -
2026-07-24 INV-M-0555 PO-30555 S-0881 kite-and-coil 2075.00 matched -
2026-07-24 INV-M-0556 PO-30556 S-3301 yellow-dock 2100.00 matched -
2026-07-27 INV-M-0557 PO-30557 S-0770 pell-and-murmur 2125.00 matched -
2026-07-27 INV-M-0558 PO-30558 S-4419 glassbarley 2150.00 price-diff owen-brice
2026-07-27 INV-M-0559 PO-30559 S-6155 two-river 2175.00 qty-diff rowan-hale
2026-07-28 INV-M-0560 PO-30560 S-7022 moss-freight 200.00 no-receipt nia-pell
2026-07-28 INV-M-0561 PO-30561 S-1044 bramble-tin 225.00 matched -
2026-07-28 INV-M-0562 PO-30562 S-2210 lowlamp-paper 250.00 matched -
2026-07-29 INV-M-0563 PO-30563 S-0881 kite-and-coil 275.00 matched -
2026-07-29 INV-M-0564 PO-30564 S-3301 yellow-dock 300.00 matched -
2026-07-29 INV-M-0565 PO-30565 S-0770 pell-and-murmur 325.00 price-diff rowan-hale
2026-07-30 INV-M-0566 PO-30566 S-4419 glassbarley 350.00 qty-diff nia-pell
2026-07-30 INV-M-0567 PO-30567 S-6155 two-river 375.00 no-receipt owen-brice
2026-07-30 INV-M-0568 PO-30568 S-7022 moss-freight 400.00 matched -
2026-07-31 INV-M-0569 PO-30569 S-1044 bramble-tin 425.00 matched -
2026-07-31 INV-M-0570 PO-30570 S-2210 lowlamp-paper 450.00 matched -
2026-07-31 INV-M-0571 PO-30571 S-0881 kite-and-coil 475.00 matched -
2026-08-03 INV-M-0572 PO-30572 S-3301 yellow-dock 500.00 price-diff nia-pell
2026-08-03 INV-M-0573 PO-30573 S-0770 pell-and-murmur 525.00 qty-diff owen-brice
2026-08-03 INV-M-0574 PO-30574 S-4419 glassbarley 550.00 no-receipt rowan-hale
2026-08-04 INV-M-0575 PO-30575 S-6155 two-river 575.00 matched -
2026-08-04 INV-M-0576 PO-30576 S-7022 moss-freight 600.00 matched -
2026-08-04 INV-M-0577 PO-30577 S-1044 bramble-tin 625.00 matched -
2026-08-05 INV-M-0578 PO-30578 S-2210 lowlamp-paper 650.00 matched -
2026-08-05 INV-M-0579 PO-30579 S-0881 kite-and-coil 675.00 price-diff owen-brice
2026-08-05 INV-M-0580 PO-30580 S-3301 yellow-dock 700.00 qty-diff rowan-hale
2026-08-06 INV-M-0581 PO-30581 S-0770 pell-and-murmur 725.00 no-receipt nia-pell
2026-08-06 INV-M-0582 PO-30582 S-4419 glassbarley 750.00 matched -
2026-08-06 INV-M-0583 PO-30583 S-6155 two-river 775.00 matched -
2026-08-07 INV-M-0584 PO-30584 S-7022 moss-freight 800.00 matched -
2026-08-07 INV-M-0585 PO-30585 S-1044 bramble-tin 825.00 matched -
2026-08-07 INV-M-0586 PO-30586 S-2210 lowlamp-paper 850.00 price-diff rowan-hale
2026-08-10 INV-M-0587 PO-30587 S-0881 kite-and-coil 875.00 qty-diff nia-pell
2026-08-10 INV-M-0588 PO-30588 S-3301 yellow-dock 900.00 no-receipt owen-brice
2026-08-10 INV-M-0589 PO-30589 S-0770 pell-and-murmur 925.00 matched -
2026-08-11 INV-M-0590 PO-30590 S-4419 glassbarley 950.00 matched -
2026-08-11 INV-M-0591 PO-30591 S-6155 two-river 975.00 matched -
2026-08-11 INV-M-0592 PO-30592 S-7022 moss-freight 1000.00 matched -
2026-08-12 INV-M-0593 PO-30593 S-1044 bramble-tin 1025.00 price-diff nia-pell
2026-08-12 INV-M-0594 PO-30594 S-2210 lowlamp-paper 1050.00 qty-diff owen-brice
2026-08-12 INV-M-0595 PO-30595 S-0881 kite-and-coil 1075.00 no-receipt rowan-hale
2026-08-13 INV-M-0596 PO-30596 S-3301 yellow-dock 1100.00 matched -
2026-08-13 INV-M-0597 PO-30597 S-0770 pell-and-murmur 1125.00 matched -
2026-08-13 INV-M-0598 PO-30598 S-4419 glassbarley 1150.00 matched -
2026-08-14 INV-M-0599 PO-30599 S-6155 two-river 1175.00 matched -
2026-08-14 INV-M-0600 PO-30600 S-7022 moss-freight 1200.00 price-diff owen-brice
2026-08-14 INV-M-0601 PO-30601 S-1044 bramble-tin 1225.00 qty-diff rowan-hale
2026-08-17 INV-M-0602 PO-30602 S-2210 lowlamp-paper 1250.00 no-receipt nia-pell
2026-08-17 INV-M-0603 PO-30603 S-0881 kite-and-coil 1275.00 matched -
2026-08-17 INV-M-0604 PO-30604 S-3301 yellow-dock 1300.00 matched -
2026-08-18 INV-M-0605 PO-30605 S-0770 pell-and-murmur 1325.00 matched -
2026-08-18 INV-M-0606 PO-30606 S-4419 glassbarley 1350.00 matched -
2026-08-18 INV-M-0607 PO-30607 S-6155 two-river 1375.00 price-diff rowan-hale
2026-08-19 INV-M-0608 PO-30608 S-7022 moss-freight 1400.00 qty-diff nia-pell
2026-08-19 INV-M-0609 PO-30609 S-1044 bramble-tin 1425.00 no-receipt owen-brice
2026-08-19 INV-M-0610 PO-30610 S-2210 lowlamp-paper 1450.00 matched -
2026-08-20 INV-M-0611 PO-30611 S-0881 kite-and-coil 1475.00 matched -
2026-08-20 INV-M-0612 PO-30612 S-3301 yellow-dock 1500.00 matched -
2026-08-20 INV-M-0613 PO-30613 S-0770 pell-and-murmur 1525.00 matched -
2026-08-21 INV-M-0614 PO-30614 S-4419 glassbarley 1550.00 price-diff nia-pell
2026-08-21 INV-M-0615 PO-30615 S-6155 two-river 1575.00 qty-diff owen-brice
2026-08-21 INV-M-0616 PO-30616 S-7022 moss-freight 1600.00 no-receipt rowan-hale
2026-08-24 INV-M-0617 PO-30617 S-1044 bramble-tin 1625.00 matched -
2026-08-24 INV-M-0618 PO-30618 S-2210 lowlamp-paper 1650.00 matched -
2026-08-24 INV-M-0619 PO-30619 S-0881 kite-and-coil 1675.00 matched -
2026-08-25 INV-M-0620 PO-30620 S-3301 yellow-dock 1700.00 matched -
2026-08-25 INV-M-0621 PO-30621 S-0770 pell-and-murmur 1725.00 price-diff owen-brice
2026-08-25 INV-M-0622 PO-30622 S-4419 glassbarley 1750.00 qty-diff rowan-hale
2026-08-26 INV-M-0623 PO-30623 S-6155 two-river 1775.00 no-receipt nia-pell
2026-08-26 INV-M-0624 PO-30624 S-7022 moss-freight 1800.00 matched -
2026-08-26 INV-M-0625 PO-30625 S-1044 bramble-tin 1825.00 matched -
2026-08-27 INV-M-0626 PO-30626 S-2210 lowlamp-paper 1850.00 matched -
2026-08-27 INV-M-0627 PO-30627 S-0881 kite-and-coil 1875.00 matched -
2026-08-27 INV-M-0628 PO-30628 S-3301 yellow-dock 1900.00 price-diff rowan-hale
2026-08-28 INV-M-0629 PO-30629 S-0770 pell-and-murmur 1925.00 qty-diff nia-pell
2026-08-28 INV-M-0630 PO-30630 S-4419 glassbarley 1950.00 no-receipt owen-brice
2026-08-28 INV-M-0631 PO-30631 S-6155 two-river 1975.00 matched -
2026-08-31 INV-M-0632 PO-30632 S-7022 moss-freight 2000.00 matched -
2026-08-31 INV-M-0633 PO-30633 S-1044 bramble-tin 2025.00 matched -
2026-08-31 INV-M-0634 PO-30634 S-2210 lowlamp-paper 2050.00 matched -
2026-09-01 INV-M-0635 PO-30635 S-0881 kite-and-coil 2075.00 price-diff nia-pell
2026-09-01 INV-M-0636 PO-30636 S-3301 yellow-dock 2100.00 qty-diff owen-brice
2026-09-01 INV-M-0637 PO-30637 S-0770 pell-and-murmur 2125.00 no-receipt rowan-hale
2026-09-02 INV-M-0638 PO-30638 S-4419 glassbarley 2150.00 matched -
2026-09-02 INV-M-0639 PO-30639 S-6155 two-river 2175.00 matched -
2026-09-02 INV-M-0640 PO-30640 S-7022 moss-freight 200.00 matched -
2026-09-03 INV-M-0641 PO-30641 S-1044 bramble-tin 225.00 matched -
2026-09-03 INV-M-0642 PO-30642 S-2210 lowlamp-paper 250.00 price-diff owen-brice
2026-09-03 INV-M-0643 PO-30643 S-0881 kite-and-coil 275.00 qty-diff rowan-hale
2026-09-04 INV-M-0644 PO-30644 S-3301 yellow-dock 300.00 no-receipt nia-pell
2026-09-04 INV-M-0645 PO-30645 S-0770 pell-and-murmur 325.00 matched -
2026-09-04 INV-M-0646 PO-30646 S-4419 glassbarley 350.00 matched -
2026-09-07 INV-M-0647 PO-30647 S-6155 two-river 375.00 matched -
2026-09-07 INV-M-0648 PO-30648 S-7022 moss-freight 400.00 matched -
2026-09-07 INV-M-0649 PO-30649 S-1044 bramble-tin 425.00 price-diff rowan-hale
2026-09-08 INV-M-0650 PO-30650 S-2210 lowlamp-paper 450.00 qty-diff nia-pell
2026-09-08 INV-M-0651 PO-30651 S-0881 kite-and-coil 475.00 no-receipt owen-brice
2026-09-08 INV-M-0652 PO-30652 S-3301 yellow-dock 500.00 matched -
2026-09-09 INV-M-0653 PO-30653 S-0770 pell-and-murmur 525.00 matched -
2026-09-09 INV-M-0654 PO-30654 S-4419 glassbarley 550.00 matched -
2026-09-09 INV-M-0655 PO-30655 S-6155 two-river 575.00 matched -
2026-09-10 INV-M-0656 PO-30656 S-7022 moss-freight 600.00 price-diff nia-pell
2026-09-10 INV-M-0657 PO-30657 S-1044 bramble-tin 625.00 qty-diff owen-brice
2026-09-10 INV-M-0658 PO-30658 S-2210 lowlamp-paper 650.00 no-receipt rowan-hale
2026-09-11 INV-M-0659 PO-30659 S-0881 kite-and-coil 675.00 matched -
2026-09-11 INV-M-0660 PO-30660 S-3301 yellow-dock 700.00 matched -
2026-09-11 INV-M-0661 PO-30661 S-0770 pell-and-murmur 725.00 matched -
2026-09-14 INV-M-0662 PO-30662 S-4419 glassbarley 750.00 matched -
2026-09-14 INV-M-0663 PO-30663 S-6155 two-river 775.00 price-diff owen-brice
2026-09-14 INV-M-0664 PO-30664 S-7022 moss-freight 800.00 qty-diff rowan-hale
2026-09-15 INV-M-0665 PO-30665 S-1044 bramble-tin 825.00 no-receipt nia-pell
2026-09-15 INV-M-0666 PO-30666 S-2210 lowlamp-paper 850.00 matched -
2026-09-15 INV-M-0667 PO-30667 S-0881 kite-and-coil 875.00 matched -
2026-09-16 INV-M-0668 PO-30668 S-3301 yellow-dock 900.00 matched -
2026-09-16 INV-M-0669 PO-30669 S-0770 pell-and-murmur 925.00 matched -
2026-09-16 INV-M-0670 PO-30670 S-4419 glassbarley 950.00 price-diff rowan-hale
2026-09-17 INV-M-0671 PO-30671 S-6155 two-river 975.00 qty-diff nia-pell
2026-09-17 INV-M-0672 PO-30672 S-7022 moss-freight 1000.00 no-receipt owen-brice
2026-09-17 INV-M-0673 PO-30673 S-1044 bramble-tin 1025.00 matched -
2026-09-18 INV-M-0674 PO-30674 S-2210 lowlamp-paper 1050.00 matched -
2026-09-18 INV-M-0675 PO-30675 S-0881 kite-and-coil 1075.00 matched -
2026-09-18 INV-M-0676 PO-30676 S-3301 yellow-dock 1100.00 matched -
2026-09-21 INV-M-0677 PO-30677 S-0770 pell-and-murmur 1125.00 price-diff nia-pell
2026-09-21 INV-M-0678 PO-30678 S-4419 glassbarley 1150.00 qty-diff owen-brice
2026-09-21 INV-M-0679 PO-30679 S-6155 two-river 1175.00 no-receipt rowan-hale
2026-09-22 INV-M-0680 PO-30680 S-7022 moss-freight 1200.00 matched -
2026-09-22 INV-M-0681 PO-30681 S-1044 bramble-tin 1225.00 matched -
2026-09-22 INV-M-0682 PO-30682 S-2210 lowlamp-paper 1250.00 matched -
2026-09-23 INV-M-0683 PO-30683 S-0881 kite-and-coil 1275.00 matched -
2026-09-23 INV-M-0684 PO-30684 S-3301 yellow-dock 1300.00 price-diff owen-brice
2026-09-23 INV-M-0685 PO-30685 S-0770 pell-and-murmur 1325.00 qty-diff rowan-hale
2026-09-24 INV-M-0686 PO-30686 S-4419 glassbarley 1350.00 no-receipt nia-pell
2026-09-24 INV-M-0687 PO-30687 S-6155 two-river 1375.00 matched -
2026-09-24 INV-M-0688 PO-30688 S-7022 moss-freight 1400.00 matched -
2026-09-25 INV-M-0689 PO-30689 S-1044 bramble-tin 1425.00 matched -
2026-09-25 INV-M-0690 PO-30690 S-2210 lowlamp-paper 1450.00 matched -
2026-09-25 INV-M-0691 PO-30691 S-0881 kite-and-coil 1475.00 price-diff rowan-hale
2026-09-28 INV-M-0692 PO-30692 S-3301 yellow-dock 1500.00 qty-diff nia-pell
2026-09-28 INV-M-0693 PO-30693 S-0770 pell-and-murmur 1525.00 no-receipt owen-brice
2026-09-28 INV-M-0694 PO-30694 S-4419 glassbarley 1550.00 matched -
2026-09-29 INV-M-0695 PO-30695 S-6155 two-river 1575.00 matched -
2026-09-29 INV-M-0696 PO-30696 S-7022 moss-freight 1600.00 matched -
2026-09-29 INV-M-0697 PO-30697 S-1044 bramble-tin 1625.00 matched -
2026-09-30 INV-M-0698 PO-30698 S-2210 lowlamp-paper 1650.00 price-diff nia-pell
2026-09-30 INV-M-0699 PO-30699 S-0881 kite-and-coil 1675.00 qty-diff owen-brice
2026-09-30 INV-M-0700 PO-30700 S-3301 yellow-dock 1700.00 no-receipt rowan-hale
