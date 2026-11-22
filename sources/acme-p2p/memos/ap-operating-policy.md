# Accounts payable operating rule
Client: Acme
Subject: procure-to-pay
Date: 2026-01-20
From: Ellis Ward, controller
To: accounts payable and procurement

## Purpose

This memo is the payment rule for Acme procure-to-pay. It replaces the 2025 note. It is
in force from 2026-01-20 until I withdraw it.

## Where an invoice goes

Suppliers send invoices to invoices@acme.example. Clerks work the oldest unread message
first. About 220 invoices arrive in a week. A document in a currency other than dollars
is turned away and is not entered.

## What must be compared

Before an invoice can move to proposed, a clerk compares the purchase order in Gatepass,
the goods receipt in Dockhand, and the supplier invoice. The fields are supplier,
quantity and unit price. The clerk records the result on the match log spreadsheet.
Paywindow does not compare the three documents and does not read the match log.

## Who may change a status

Statuses are entered, held, proposed, released and paid. A clerk may set entered, held
or proposed. Only Gwen Adler may set released. A buyer must not change a payment status.
Status paid is set when the bank run is confirmed. On Fridays Tess Harp has set released
while the clerks were in the month-end meeting. That is outside this rule. The system
does not stop it.

## Terms

Goods are due thirty days after the invoice is received. Freight is due fifteen days
after the invoice is received. The cycle measure, which the controller keeps, stops at
proposed and is not these terms.

## Repeated invoice numbers

The clerk searches Paywindow for the invoice number before proposing. Paywindow does not
block a second payment of an invoice number already paid. A repeated payment is a break
of this rule even when the search was skipped.

## Mismatches

The clerk emails the buyer who owns the purchase order and sets the invoice to held.
There is no shared list of held invoices. A colleague can see a held invoice only by
opening its number.

## Purchase orders raised after delivery

A purchase order is supposed to exist before the goods arrive. Raising one after
delivery is outside this rule and still happens.

## Who can change this memo

Ellis Ward can change this memo. Buyers and clerks cannot.
