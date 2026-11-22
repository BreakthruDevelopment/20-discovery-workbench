# Controller interview
Client: Acme
Subject: procure-to-pay
Interview date: 2026-10-16
Interviewee: Ellis Ward, controller
Interviewer: Analyst
Location: Mill Road office

Analyst: The brief says spend on procure-to-pay is too high. I want the work as it is
done this week.

Ellis Ward: I am the controller. Gwen Adler keys the daily summary journal into
Ledgerline. About 220 invoices a week is the volume I use for the close. The January
payment rule is still in force. I have not reissued it.

Analyst: How do you measure the invoice cycle?

Ellis Ward: Cycle days run from the mailbox timestamp, stored as the received date, to
the moment Paywindow shows proposed. They stop before release and before the bank pays.
They are calendar days, so a weekend counts. An invoice that never reaches proposed is
outside the average, which means the oldest problems are missing from it.

Analyst: What was the average invoice cycle last quarter?

Ellis Ward: The average invoice cycle last quarter was 9 days.

Ellis Ward: The sample has 300 invoices. The mean of cycle_days is 9.00. Weekly means
are not the same number.

Ellis Ward: The sample is not the whole quarter. I will stand behind the quarter mean of
that sample, not a single week.

Analyst: What do you make of duplicate payments?

Ellis Ward: Helpline shows them. I do not treat a buyer's confidence as a count. I want
the clerk's block on a repeated invoice number. Gwen sees the payments once they have
reached the ledger, which is late.

Analyst: And the match itself?

Ellis Ward: The January rule says a clerk compares the purchase order, the goods receipt
and the invoice outside Paywindow and writes the match log. Paywindow does not do that
comparison. There is still no shared list of held invoices. I have asked for one. When
the holder is away, the other clerks cannot see the hold without the invoice number.

Analyst: The night file.

Ellis Ward: Gwen still keys the summary. A second file arrives at night with invoice
lines she did not key. We do not reconcile the two. If that night step stops, the detail
lines stop and her summary still has to be keyed. I have asked IT to name the owner. The
inventory still has no row for it. On 2026-07-09 the night file was rejected and her
summary still posted.

Analyst: The portal pilot.

Ellis Ward: I agreed in March that the pilot was not saving clerk time, because a clerk
still re-keyed every invoice. I did not put new money on it. Dana's closure note is the
record. The date is 2026-03-14.

Analyst: Fridays.

Ellis Ward: Tess Harp has set released while the clerks were in the month-end meeting.
The rule says only Gwen may do that. Some of those invoices have already reached the
ledger. Gwen has been told to send them back. The system does not enforce the rule.

Analyst: Will you put a number on how mature this process is, or on the money it would
save?

Ellis Ward: No. I will not put a number on how mature the process is. There is no scored
model I would sign. I also will not quote a savings figure in this interview. I do not
have a basis I would sign.

## Cycle sample

Columns are received, proposed, cycle_days, invoice, supplier code, supplier slug, and
amount. cycle_days counts calendar days from the mailbox received date to the payment
proposal, and a weekend counts. Received dates are weekdays from 2026-07-01 through
2026-09-30. Invoices that never reached proposed are not in this sample. The sample has
300 invoices. The mean of cycle_days is 9.00. Weekly means are not the same number.

2026-07-01 2026-07-12 11 INV-Q3-0001 S-1044 bramble-tin 200.00
2026-07-01 2026-07-09 8 INV-Q3-0002 S-2210 lowlamp-paper 215.00
2026-07-01 2026-07-11 10 INV-Q3-0003 S-0881 kite-and-coil 230.00
2026-07-01 2026-07-08 7 INV-Q3-0004 S-3301 yellow-dock 245.00
2026-07-01 2026-07-10 9 INV-Q3-0005 S-0770 pell-and-murmur 260.00
2026-07-02 2026-07-14 12 INV-Q3-0006 S-4419 glassbarley 275.00
2026-07-02 2026-07-08 6 INV-Q3-0007 S-6155 two-river 290.00
2026-07-02 2026-07-11 9 INV-Q3-0008 S-7022 moss-freight 305.00
2026-07-02 2026-07-10 8 INV-Q3-0009 S-1044 bramble-tin 320.00
2026-07-02 2026-07-13 11 INV-Q3-0010 S-2210 lowlamp-paper 335.00
2026-07-03 2026-07-10 7 INV-Q3-0011 S-0881 kite-and-coil 350.00
2026-07-03 2026-07-13 10 INV-Q3-0012 S-3301 yellow-dock 365.00
2026-07-03 2026-07-14 11 INV-Q3-0013 S-0770 pell-and-murmur 380.00
2026-07-03 2026-07-11 8 INV-Q3-0014 S-4419 glassbarley 395.00
2026-07-03 2026-07-13 10 INV-Q3-0015 S-6155 two-river 410.00
2026-07-06 2026-07-13 7 INV-Q3-0016 S-7022 moss-freight 425.00
2026-07-06 2026-07-15 9 INV-Q3-0017 S-1044 bramble-tin 440.00
2026-07-06 2026-07-18 12 INV-Q3-0018 S-2210 lowlamp-paper 455.00
2026-07-06 2026-07-12 6 INV-Q3-0019 S-0881 kite-and-coil 470.00
2026-07-06 2026-07-15 9 INV-Q3-0020 S-3301 yellow-dock 485.00
2026-07-07 2026-07-15 8 INV-Q3-0021 S-0770 pell-and-murmur 500.00
2026-07-07 2026-07-18 11 INV-Q3-0022 S-4419 glassbarley 515.00
2026-07-07 2026-07-14 7 INV-Q3-0023 S-6155 two-river 530.00
2026-07-07 2026-07-17 10 INV-Q3-0024 S-7022 moss-freight 545.00
2026-07-07 2026-07-18 11 INV-Q3-0025 S-1044 bramble-tin 560.00
2026-07-08 2026-07-16 8 INV-Q3-0026 S-2210 lowlamp-paper 575.00
2026-07-08 2026-07-18 10 INV-Q3-0027 S-0881 kite-and-coil 590.00
2026-07-08 2026-07-15 7 INV-Q3-0028 S-3301 yellow-dock 605.00
2026-07-08 2026-07-17 9 INV-Q3-0029 S-0770 pell-and-murmur 620.00
2026-07-08 2026-07-20 12 INV-Q3-0030 S-4419 glassbarley 635.00
2026-07-09 2026-07-15 6 INV-Q3-0031 S-6155 two-river 650.00
2026-07-09 2026-07-18 9 INV-Q3-0032 S-7022 moss-freight 665.00
2026-07-09 2026-07-17 8 INV-Q3-0033 S-1044 bramble-tin 680.00
2026-07-09 2026-07-20 11 INV-Q3-0034 S-2210 lowlamp-paper 695.00
2026-07-09 2026-07-16 7 INV-Q3-0035 S-0881 kite-and-coil 710.00
2026-07-10 2026-07-20 10 INV-Q3-0036 S-3301 yellow-dock 725.00
2026-07-10 2026-07-21 11 INV-Q3-0037 S-0770 pell-and-murmur 740.00
2026-07-10 2026-07-18 8 INV-Q3-0038 S-4419 glassbarley 755.00
2026-07-10 2026-07-20 10 INV-Q3-0039 S-6155 two-river 770.00
2026-07-10 2026-07-17 7 INV-Q3-0040 S-7022 moss-freight 785.00
2026-07-13 2026-07-22 9 INV-Q3-0041 S-1044 bramble-tin 800.00
2026-07-13 2026-07-25 12 INV-Q3-0042 S-2210 lowlamp-paper 815.00
2026-07-13 2026-07-19 6 INV-Q3-0043 S-0881 kite-and-coil 830.00
2026-07-13 2026-07-22 9 INV-Q3-0044 S-3301 yellow-dock 845.00
2026-07-13 2026-07-21 8 INV-Q3-0045 S-0770 pell-and-murmur 860.00
2026-07-14 2026-07-25 11 INV-Q3-0046 S-4419 glassbarley 875.00
2026-07-14 2026-07-21 7 INV-Q3-0047 S-6155 two-river 890.00
2026-07-14 2026-07-24 10 INV-Q3-0048 S-7022 moss-freight 905.00
2026-07-14 2026-07-25 11 INV-Q3-0049 S-1044 bramble-tin 920.00
2026-07-14 2026-07-22 8 INV-Q3-0050 S-2210 lowlamp-paper 935.00
2026-07-15 2026-07-25 10 INV-Q3-0051 S-0881 kite-and-coil 950.00
2026-07-15 2026-07-22 7 INV-Q3-0052 S-3301 yellow-dock 965.00
2026-07-15 2026-07-24 9 INV-Q3-0053 S-0770 pell-and-murmur 980.00
2026-07-15 2026-07-27 12 INV-Q3-0054 S-4419 glassbarley 995.00
2026-07-15 2026-07-21 6 INV-Q3-0055 S-6155 two-river 1010.00
2026-07-16 2026-07-25 9 INV-Q3-0056 S-7022 moss-freight 1025.00
2026-07-16 2026-07-24 8 INV-Q3-0057 S-1044 bramble-tin 1040.00
2026-07-16 2026-07-27 11 INV-Q3-0058 S-2210 lowlamp-paper 1055.00
2026-07-16 2026-07-23 7 INV-Q3-0059 S-0881 kite-and-coil 1070.00
2026-07-16 2026-07-26 10 INV-Q3-0060 S-3301 yellow-dock 1085.00
2026-07-17 2026-07-28 11 INV-Q3-0061 S-0770 pell-and-murmur 1100.00
2026-07-17 2026-07-25 8 INV-Q3-0062 S-4419 glassbarley 1115.00
2026-07-17 2026-07-27 10 INV-Q3-0063 S-6155 two-river 1130.00
2026-07-17 2026-07-24 7 INV-Q3-0064 S-7022 moss-freight 1145.00
2026-07-17 2026-07-26 9 INV-Q3-0065 S-1044 bramble-tin 1160.00
2026-07-20 2026-08-01 12 INV-Q3-0066 S-2210 lowlamp-paper 1175.00
2026-07-20 2026-07-26 6 INV-Q3-0067 S-0881 kite-and-coil 1190.00
2026-07-20 2026-07-29 9 INV-Q3-0068 S-3301 yellow-dock 1205.00
2026-07-20 2026-07-28 8 INV-Q3-0069 S-0770 pell-and-murmur 1220.00
2026-07-20 2026-07-31 11 INV-Q3-0070 S-4419 glassbarley 1235.00
2026-07-21 2026-07-28 7 INV-Q3-0071 S-6155 two-river 1250.00
2026-07-21 2026-07-31 10 INV-Q3-0072 S-7022 moss-freight 1265.00
2026-07-21 2026-08-01 11 INV-Q3-0073 S-1044 bramble-tin 1280.00
2026-07-21 2026-07-29 8 INV-Q3-0074 S-2210 lowlamp-paper 1295.00
2026-07-21 2026-07-31 10 INV-Q3-0075 S-0881 kite-and-coil 1310.00
2026-07-22 2026-07-29 7 INV-Q3-0076 S-3301 yellow-dock 1325.00
2026-07-22 2026-07-31 9 INV-Q3-0077 S-0770 pell-and-murmur 1340.00
2026-07-22 2026-08-03 12 INV-Q3-0078 S-4419 glassbarley 1355.00
2026-07-22 2026-07-28 6 INV-Q3-0079 S-6155 two-river 1370.00
2026-07-22 2026-07-31 9 INV-Q3-0080 S-7022 moss-freight 1385.00
2026-07-23 2026-07-31 8 INV-Q3-0081 S-1044 bramble-tin 1400.00
2026-07-23 2026-08-03 11 INV-Q3-0082 S-2210 lowlamp-paper 1415.00
2026-07-23 2026-07-30 7 INV-Q3-0083 S-0881 kite-and-coil 1430.00
2026-07-23 2026-08-02 10 INV-Q3-0084 S-3301 yellow-dock 1445.00
2026-07-23 2026-08-03 11 INV-Q3-0085 S-0770 pell-and-murmur 1460.00
2026-07-24 2026-08-01 8 INV-Q3-0086 S-4419 glassbarley 1475.00
2026-07-24 2026-08-03 10 INV-Q3-0087 S-6155 two-river 1490.00
2026-07-24 2026-07-31 7 INV-Q3-0088 S-7022 moss-freight 1505.00
2026-07-24 2026-08-02 9 INV-Q3-0089 S-1044 bramble-tin 1520.00
2026-07-24 2026-08-05 12 INV-Q3-0090 S-2210 lowlamp-paper 1535.00
2026-07-27 2026-08-02 6 INV-Q3-0091 S-0881 kite-and-coil 1550.00
2026-07-27 2026-08-05 9 INV-Q3-0092 S-3301 yellow-dock 1565.00
2026-07-27 2026-08-04 8 INV-Q3-0093 S-0770 pell-and-murmur 1580.00
2026-07-27 2026-08-07 11 INV-Q3-0094 S-4419 glassbarley 1595.00
2026-07-27 2026-08-03 7 INV-Q3-0095 S-6155 two-river 1610.00
2026-07-28 2026-08-07 10 INV-Q3-0096 S-7022 moss-freight 1625.00
2026-07-28 2026-08-08 11 INV-Q3-0097 S-1044 bramble-tin 1640.00
2026-07-28 2026-08-05 8 INV-Q3-0098 S-2210 lowlamp-paper 1655.00
2026-07-28 2026-08-07 10 INV-Q3-0099 S-0881 kite-and-coil 1670.00
2026-07-28 2026-08-04 7 INV-Q3-0100 S-3301 yellow-dock 1685.00
2026-07-29 2026-08-07 9 INV-Q3-0101 S-0770 pell-and-murmur 1700.00
2026-07-29 2026-08-10 12 INV-Q3-0102 S-4419 glassbarley 1715.00
2026-07-29 2026-08-04 6 INV-Q3-0103 S-6155 two-river 1730.00
2026-07-29 2026-08-07 9 INV-Q3-0104 S-7022 moss-freight 1745.00
2026-07-29 2026-08-06 8 INV-Q3-0105 S-1044 bramble-tin 1760.00
2026-07-30 2026-08-10 11 INV-Q3-0106 S-2210 lowlamp-paper 1775.00
2026-07-30 2026-08-06 7 INV-Q3-0107 S-0881 kite-and-coil 1790.00
2026-07-30 2026-08-09 10 INV-Q3-0108 S-3301 yellow-dock 1805.00
2026-07-30 2026-08-10 11 INV-Q3-0109 S-0770 pell-and-murmur 1820.00
2026-07-30 2026-08-07 8 INV-Q3-0110 S-4419 glassbarley 1835.00
2026-07-31 2026-08-10 10 INV-Q3-0111 S-6155 two-river 1850.00
2026-07-31 2026-08-07 7 INV-Q3-0112 S-7022 moss-freight 1865.00
2026-07-31 2026-08-09 9 INV-Q3-0113 S-1044 bramble-tin 1880.00
2026-07-31 2026-08-12 12 INV-Q3-0114 S-2210 lowlamp-paper 1895.00
2026-07-31 2026-08-06 6 INV-Q3-0115 S-0881 kite-and-coil 1910.00
2026-08-03 2026-08-12 9 INV-Q3-0116 S-3301 yellow-dock 1925.00
2026-08-03 2026-08-11 8 INV-Q3-0117 S-0770 pell-and-murmur 1940.00
2026-08-03 2026-08-14 11 INV-Q3-0118 S-4419 glassbarley 1955.00
2026-08-03 2026-08-10 7 INV-Q3-0119 S-6155 two-river 1970.00
2026-08-03 2026-08-13 10 INV-Q3-0120 S-7022 moss-freight 1985.00
2026-08-04 2026-08-15 11 INV-Q3-0121 S-1044 bramble-tin 2000.00
2026-08-04 2026-08-12 8 INV-Q3-0122 S-2210 lowlamp-paper 2015.00
2026-08-04 2026-08-14 10 INV-Q3-0123 S-0881 kite-and-coil 2030.00
2026-08-04 2026-08-11 7 INV-Q3-0124 S-3301 yellow-dock 2045.00
2026-08-04 2026-08-13 9 INV-Q3-0125 S-0770 pell-and-murmur 2060.00
2026-08-05 2026-08-17 12 INV-Q3-0126 S-4419 glassbarley 2075.00
2026-08-05 2026-08-11 6 INV-Q3-0127 S-6155 two-river 2090.00
2026-08-05 2026-08-14 9 INV-Q3-0128 S-7022 moss-freight 2105.00
2026-08-05 2026-08-13 8 INV-Q3-0129 S-1044 bramble-tin 2120.00
2026-08-05 2026-08-16 11 INV-Q3-0130 S-2210 lowlamp-paper 2135.00
2026-08-06 2026-08-13 7 INV-Q3-0131 S-0881 kite-and-coil 2150.00
2026-08-06 2026-08-16 10 INV-Q3-0132 S-3301 yellow-dock 2165.00
2026-08-06 2026-08-17 11 INV-Q3-0133 S-0770 pell-and-murmur 2180.00
2026-08-06 2026-08-14 8 INV-Q3-0134 S-4419 glassbarley 2195.00
2026-08-06 2026-08-16 10 INV-Q3-0135 S-6155 two-river 2210.00
2026-08-07 2026-08-14 7 INV-Q3-0136 S-7022 moss-freight 2225.00
2026-08-07 2026-08-16 9 INV-Q3-0137 S-1044 bramble-tin 2240.00
2026-08-07 2026-08-19 12 INV-Q3-0138 S-2210 lowlamp-paper 2255.00
2026-08-07 2026-08-13 6 INV-Q3-0139 S-0881 kite-and-coil 2270.00
2026-08-07 2026-08-16 9 INV-Q3-0140 S-3301 yellow-dock 2285.00
2026-08-10 2026-08-18 8 INV-Q3-0141 S-0770 pell-and-murmur 2300.00
2026-08-10 2026-08-21 11 INV-Q3-0142 S-4419 glassbarley 2315.00
2026-08-10 2026-08-17 7 INV-Q3-0143 S-6155 two-river 2330.00
2026-08-10 2026-08-20 10 INV-Q3-0144 S-7022 moss-freight 2345.00
2026-08-10 2026-08-21 11 INV-Q3-0145 S-1044 bramble-tin 2360.00
2026-08-11 2026-08-19 8 INV-Q3-0146 S-2210 lowlamp-paper 2375.00
2026-08-11 2026-08-21 10 INV-Q3-0147 S-0881 kite-and-coil 2390.00
2026-08-11 2026-08-18 7 INV-Q3-0148 S-3301 yellow-dock 2405.00
2026-08-11 2026-08-20 9 INV-Q3-0149 S-0770 pell-and-murmur 2420.00
2026-08-11 2026-08-23 12 INV-Q3-0150 S-4419 glassbarley 2435.00
2026-08-12 2026-08-18 6 INV-Q3-0151 S-6155 two-river 2450.00
2026-08-12 2026-08-21 9 INV-Q3-0152 S-7022 moss-freight 2465.00
2026-08-12 2026-08-20 8 INV-Q3-0153 S-1044 bramble-tin 2480.00
2026-08-12 2026-08-23 11 INV-Q3-0154 S-2210 lowlamp-paper 2495.00
2026-08-12 2026-08-19 7 INV-Q3-0155 S-0881 kite-and-coil 2510.00
2026-08-13 2026-08-23 10 INV-Q3-0156 S-3301 yellow-dock 2525.00
2026-08-13 2026-08-24 11 INV-Q3-0157 S-0770 pell-and-murmur 2540.00
2026-08-13 2026-08-21 8 INV-Q3-0158 S-4419 glassbarley 2555.00
2026-08-13 2026-08-23 10 INV-Q3-0159 S-6155 two-river 2570.00
2026-08-13 2026-08-20 7 INV-Q3-0160 S-7022 moss-freight 2585.00
2026-08-14 2026-08-23 9 INV-Q3-0161 S-1044 bramble-tin 2600.00
2026-08-14 2026-08-26 12 INV-Q3-0162 S-2210 lowlamp-paper 2615.00
2026-08-14 2026-08-20 6 INV-Q3-0163 S-0881 kite-and-coil 2630.00
2026-08-14 2026-08-23 9 INV-Q3-0164 S-3301 yellow-dock 2645.00
2026-08-14 2026-08-22 8 INV-Q3-0165 S-0770 pell-and-murmur 2660.00
2026-08-17 2026-08-28 11 INV-Q3-0166 S-4419 glassbarley 2675.00
2026-08-17 2026-08-24 7 INV-Q3-0167 S-6155 two-river 2690.00
2026-08-17 2026-08-27 10 INV-Q3-0168 S-7022 moss-freight 2705.00
2026-08-17 2026-08-28 11 INV-Q3-0169 S-1044 bramble-tin 2720.00
2026-08-17 2026-08-25 8 INV-Q3-0170 S-2210 lowlamp-paper 2735.00
2026-08-18 2026-08-28 10 INV-Q3-0171 S-0881 kite-and-coil 2750.00
2026-08-18 2026-08-25 7 INV-Q3-0172 S-3301 yellow-dock 2765.00
2026-08-18 2026-08-27 9 INV-Q3-0173 S-0770 pell-and-murmur 2780.00
2026-08-18 2026-08-30 12 INV-Q3-0174 S-4419 glassbarley 2795.00
2026-08-18 2026-08-24 6 INV-Q3-0175 S-6155 two-river 2810.00
2026-08-19 2026-08-28 9 INV-Q3-0176 S-7022 moss-freight 2825.00
2026-08-19 2026-08-27 8 INV-Q3-0177 S-1044 bramble-tin 2840.00
2026-08-19 2026-08-30 11 INV-Q3-0178 S-2210 lowlamp-paper 2855.00
2026-08-19 2026-08-26 7 INV-Q3-0179 S-0881 kite-and-coil 2870.00
2026-08-19 2026-08-29 10 INV-Q3-0180 S-3301 yellow-dock 2885.00
2026-08-20 2026-08-31 11 INV-Q3-0181 S-0770 pell-and-murmur 2900.00
2026-08-20 2026-08-28 8 INV-Q3-0182 S-4419 glassbarley 2915.00
2026-08-20 2026-08-30 10 INV-Q3-0183 S-6155 two-river 2930.00
2026-08-20 2026-08-27 7 INV-Q3-0184 S-7022 moss-freight 2945.00
2026-08-21 2026-08-30 9 INV-Q3-0185 S-1044 bramble-tin 2960.00
2026-08-21 2026-09-02 12 INV-Q3-0186 S-2210 lowlamp-paper 2975.00
2026-08-21 2026-08-27 6 INV-Q3-0187 S-0881 kite-and-coil 2990.00
2026-08-21 2026-08-30 9 INV-Q3-0188 S-3301 yellow-dock 3005.00
2026-08-24 2026-09-01 8 INV-Q3-0189 S-0770 pell-and-murmur 3020.00
2026-08-24 2026-09-04 11 INV-Q3-0190 S-4419 glassbarley 3035.00
2026-08-24 2026-08-31 7 INV-Q3-0191 S-6155 two-river 3050.00
2026-08-24 2026-09-03 10 INV-Q3-0192 S-7022 moss-freight 3065.00
2026-08-25 2026-09-05 11 INV-Q3-0193 S-1044 bramble-tin 3080.00
2026-08-25 2026-09-02 8 INV-Q3-0194 S-2210 lowlamp-paper 3095.00
2026-08-25 2026-09-04 10 INV-Q3-0195 S-0881 kite-and-coil 3110.00
2026-08-25 2026-09-01 7 INV-Q3-0196 S-3301 yellow-dock 3125.00
2026-08-26 2026-09-04 9 INV-Q3-0197 S-0770 pell-and-murmur 3140.00
2026-08-26 2026-09-07 12 INV-Q3-0198 S-4419 glassbarley 3155.00
2026-08-26 2026-09-01 6 INV-Q3-0199 S-6155 two-river 3170.00
2026-08-26 2026-09-04 9 INV-Q3-0200 S-7022 moss-freight 3185.00
2026-08-27 2026-09-04 8 INV-Q3-0201 S-1044 bramble-tin 3200.00
2026-08-27 2026-09-07 11 INV-Q3-0202 S-2210 lowlamp-paper 3215.00
2026-08-27 2026-09-03 7 INV-Q3-0203 S-0881 kite-and-coil 3230.00
2026-08-27 2026-09-06 10 INV-Q3-0204 S-3301 yellow-dock 3245.00
2026-08-28 2026-09-08 11 INV-Q3-0205 S-0770 pell-and-murmur 3260.00
2026-08-28 2026-09-05 8 INV-Q3-0206 S-4419 glassbarley 3275.00
2026-08-28 2026-09-07 10 INV-Q3-0207 S-6155 two-river 3290.00
2026-08-28 2026-09-04 7 INV-Q3-0208 S-7022 moss-freight 3305.00
2026-08-31 2026-09-09 9 INV-Q3-0209 S-1044 bramble-tin 3320.00
2026-08-31 2026-09-12 12 INV-Q3-0210 S-2210 lowlamp-paper 3335.00
2026-08-31 2026-09-06 6 INV-Q3-0211 S-0881 kite-and-coil 3350.00
2026-08-31 2026-09-09 9 INV-Q3-0212 S-3301 yellow-dock 3365.00
2026-09-01 2026-09-09 8 INV-Q3-0213 S-0770 pell-and-murmur 3380.00
2026-09-01 2026-09-12 11 INV-Q3-0214 S-4419 glassbarley 3395.00
2026-09-01 2026-09-08 7 INV-Q3-0215 S-6155 two-river 3410.00
2026-09-01 2026-09-11 10 INV-Q3-0216 S-7022 moss-freight 3425.00
2026-09-02 2026-09-13 11 INV-Q3-0217 S-1044 bramble-tin 3440.00
2026-09-02 2026-09-10 8 INV-Q3-0218 S-2210 lowlamp-paper 3455.00
2026-09-02 2026-09-12 10 INV-Q3-0219 S-0881 kite-and-coil 3470.00
2026-09-02 2026-09-09 7 INV-Q3-0220 S-3301 yellow-dock 3485.00
2026-09-03 2026-09-12 9 INV-Q3-0221 S-0770 pell-and-murmur 3500.00
2026-09-03 2026-09-15 12 INV-Q3-0222 S-4419 glassbarley 3515.00
2026-09-03 2026-09-09 6 INV-Q3-0223 S-6155 two-river 3530.00
2026-09-03 2026-09-12 9 INV-Q3-0224 S-7022 moss-freight 3545.00
2026-09-04 2026-09-12 8 INV-Q3-0225 S-1044 bramble-tin 3560.00
2026-09-04 2026-09-15 11 INV-Q3-0226 S-2210 lowlamp-paper 3575.00
2026-09-04 2026-09-11 7 INV-Q3-0227 S-0881 kite-and-coil 3590.00
2026-09-04 2026-09-14 10 INV-Q3-0228 S-3301 yellow-dock 3605.00
2026-09-07 2026-09-18 11 INV-Q3-0229 S-0770 pell-and-murmur 3620.00
2026-09-07 2026-09-15 8 INV-Q3-0230 S-4419 glassbarley 3635.00
2026-09-07 2026-09-17 10 INV-Q3-0231 S-6155 two-river 3650.00
2026-09-07 2026-09-14 7 INV-Q3-0232 S-7022 moss-freight 3665.00
2026-09-08 2026-09-17 9 INV-Q3-0233 S-1044 bramble-tin 3680.00
2026-09-08 2026-09-20 12 INV-Q3-0234 S-2210 lowlamp-paper 3695.00
2026-09-08 2026-09-14 6 INV-Q3-0235 S-0881 kite-and-coil 3710.00
2026-09-08 2026-09-17 9 INV-Q3-0236 S-3301 yellow-dock 3725.00
2026-09-09 2026-09-17 8 INV-Q3-0237 S-0770 pell-and-murmur 3740.00
2026-09-09 2026-09-20 11 INV-Q3-0238 S-4419 glassbarley 3755.00
2026-09-09 2026-09-16 7 INV-Q3-0239 S-6155 two-river 3770.00
2026-09-09 2026-09-19 10 INV-Q3-0240 S-7022 moss-freight 3785.00
2026-09-10 2026-09-21 11 INV-Q3-0241 S-1044 bramble-tin 3800.00
2026-09-10 2026-09-18 8 INV-Q3-0242 S-2210 lowlamp-paper 3815.00
2026-09-10 2026-09-20 10 INV-Q3-0243 S-0881 kite-and-coil 3830.00
2026-09-10 2026-09-17 7 INV-Q3-0244 S-3301 yellow-dock 3845.00
2026-09-11 2026-09-20 9 INV-Q3-0245 S-0770 pell-and-murmur 3860.00
2026-09-11 2026-09-23 12 INV-Q3-0246 S-4419 glassbarley 3875.00
2026-09-11 2026-09-17 6 INV-Q3-0247 S-6155 two-river 3890.00
2026-09-11 2026-09-20 9 INV-Q3-0248 S-7022 moss-freight 3905.00
2026-09-14 2026-09-22 8 INV-Q3-0249 S-1044 bramble-tin 3920.00
2026-09-14 2026-09-25 11 INV-Q3-0250 S-2210 lowlamp-paper 3935.00
2026-09-14 2026-09-21 7 INV-Q3-0251 S-0881 kite-and-coil 3950.00
2026-09-14 2026-09-24 10 INV-Q3-0252 S-3301 yellow-dock 3965.00
2026-09-15 2026-09-26 11 INV-Q3-0253 S-0770 pell-and-murmur 3980.00
2026-09-15 2026-09-23 8 INV-Q3-0254 S-4419 glassbarley 3995.00
2026-09-15 2026-09-25 10 INV-Q3-0255 S-6155 two-river 4010.00
2026-09-15 2026-09-22 7 INV-Q3-0256 S-7022 moss-freight 4025.00
2026-09-16 2026-09-25 9 INV-Q3-0257 S-1044 bramble-tin 4040.00
2026-09-16 2026-09-28 12 INV-Q3-0258 S-2210 lowlamp-paper 4055.00
2026-09-16 2026-09-22 6 INV-Q3-0259 S-0881 kite-and-coil 4070.00
2026-09-16 2026-09-25 9 INV-Q3-0260 S-3301 yellow-dock 4085.00
2026-09-17 2026-09-25 8 INV-Q3-0261 S-0770 pell-and-murmur 4100.00
2026-09-17 2026-09-28 11 INV-Q3-0262 S-4419 glassbarley 4115.00
2026-09-17 2026-09-24 7 INV-Q3-0263 S-6155 two-river 4130.00
2026-09-17 2026-09-27 10 INV-Q3-0264 S-7022 moss-freight 4145.00
2026-09-18 2026-09-29 11 INV-Q3-0265 S-1044 bramble-tin 4160.00
2026-09-18 2026-09-26 8 INV-Q3-0266 S-2210 lowlamp-paper 4175.00
2026-09-18 2026-09-28 10 INV-Q3-0267 S-0881 kite-and-coil 4190.00
2026-09-18 2026-09-25 7 INV-Q3-0268 S-3301 yellow-dock 4205.00
2026-09-21 2026-09-30 9 INV-Q3-0269 S-0770 pell-and-murmur 4220.00
2026-09-21 2026-10-03 12 INV-Q3-0270 S-4419 glassbarley 4235.00
2026-09-21 2026-09-27 6 INV-Q3-0271 S-6155 two-river 4250.00
2026-09-21 2026-09-30 9 INV-Q3-0272 S-7022 moss-freight 4265.00
2026-09-22 2026-09-30 8 INV-Q3-0273 S-1044 bramble-tin 4280.00
2026-09-22 2026-10-03 11 INV-Q3-0274 S-2210 lowlamp-paper 4295.00
2026-09-22 2026-09-29 7 INV-Q3-0275 S-0881 kite-and-coil 4310.00
2026-09-22 2026-10-02 10 INV-Q3-0276 S-3301 yellow-dock 4325.00
2026-09-23 2026-10-04 11 INV-Q3-0277 S-0770 pell-and-murmur 4340.00
2026-09-23 2026-10-01 8 INV-Q3-0278 S-4419 glassbarley 4355.00
2026-09-23 2026-10-03 10 INV-Q3-0279 S-6155 two-river 4370.00
2026-09-23 2026-09-30 7 INV-Q3-0280 S-7022 moss-freight 4385.00
2026-09-24 2026-10-03 9 INV-Q3-0281 S-1044 bramble-tin 4400.00
2026-09-24 2026-10-06 12 INV-Q3-0282 S-2210 lowlamp-paper 4415.00
2026-09-24 2026-09-30 6 INV-Q3-0283 S-0881 kite-and-coil 4430.00
2026-09-24 2026-10-03 9 INV-Q3-0284 S-3301 yellow-dock 4445.00
2026-09-25 2026-10-03 8 INV-Q3-0285 S-0770 pell-and-murmur 4460.00
2026-09-25 2026-10-06 11 INV-Q3-0286 S-4419 glassbarley 4475.00
2026-09-25 2026-10-02 7 INV-Q3-0287 S-6155 two-river 4490.00
2026-09-25 2026-10-05 10 INV-Q3-0288 S-7022 moss-freight 4505.00
2026-09-28 2026-10-09 11 INV-Q3-0289 S-1044 bramble-tin 4520.00
2026-09-28 2026-10-06 8 INV-Q3-0290 S-2210 lowlamp-paper 4535.00
2026-09-28 2026-10-08 10 INV-Q3-0291 S-0881 kite-and-coil 4550.00
2026-09-28 2026-10-05 7 INV-Q3-0292 S-3301 yellow-dock 4565.00
2026-09-29 2026-10-08 9 INV-Q3-0293 S-0770 pell-and-murmur 4580.00
2026-09-29 2026-10-11 12 INV-Q3-0294 S-4419 glassbarley 4595.00
2026-09-29 2026-10-05 6 INV-Q3-0295 S-6155 two-river 4610.00
2026-09-29 2026-10-08 9 INV-Q3-0296 S-7022 moss-freight 4625.00
2026-09-30 2026-10-08 8 INV-Q3-0297 S-1044 bramble-tin 4640.00
2026-09-30 2026-10-11 11 INV-Q3-0298 S-2210 lowlamp-paper 4655.00
2026-09-30 2026-10-07 7 INV-Q3-0299 S-0881 kite-and-coil 4670.00
2026-09-30 2026-10-10 10 INV-Q3-0300 S-3301 yellow-dock 4685.00

## Weekly means

Columns are week_ending, invoices, and mean_cycle_days. The week ends on Friday of the
week the invoice was received. A week can end in October when the invoice was received
in the last days of September.

2026-07-03 15 9.13
2026-07-10 25 8.92
2026-07-17 25 9.00
2026-07-24 25 9.12
2026-07-31 25 8.88
2026-08-07 25 9.00
2026-08-14 25 8.96
2026-08-21 23 9.04
2026-08-28 20 9.00
2026-09-04 20 9.00
2026-09-11 20 9.00
2026-09-18 20 9.00
2026-09-25 20 9.00
2026-10-02 12 9.00
