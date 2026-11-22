# System inventory
Client: Acme
Subject: procure-to-pay systems
As of: 2026-10-01
Author: Jules Fen, IT analyst
Location: Mill Road office

A row is listed only when an IT owner names it and confirms it runs in production. The
owner for every system below is Jules Fen unless the row names someone else. This
inventory is a list of systems and interfaces. It is not a description of the payment
rule.

## Paywindow

Paywindow holds supplier invoices, payment proposals, supplier records and payment
history. Business users are Rowan Hale, Nia Pell, Owen Brice, Dana Okonkwo, Tess Harp,
Ivo Marsh and Gwen Adler. Gwen's use is to read the proposal list. The fields in use are
supplier code, invoice number, invoice date, received date, amount, status and proposal
date. Currency is dollars only. A document in another currency is turned away at the
desk and is not entered. Statuses are entered, held, proposed, released and paid.
Paywindow does not compare a purchase order, a receipt and an invoice, and it does not
read the match log. It does not block a second payment of an invoice number already
paid. A user can open an invoice by number. There is no screen that lists every invoice
in status held. Logins are named. There is no shared login. The system does not check
the rule about who may set a status. Any of the named logins can change one.

## Gatepass

Gatepass holds purchase orders. Business users are Dana Okonkwo, Tess Harp and Ivo
Marsh. Fields are supplier code, purchase order number, buyer, amount and raised date.
There is no received date. The screen does not know whether the goods have arrived. An
order can be raised with no prior request record in the system.

## Dockhand

Dockhand holds goods receipts. Business users are Samir Quill, Pilar Soto and the other
dock clerks. Fields are purchase order number, receipt number, quantity and receipt
date. A receipt cannot be saved without a purchase order number. Goods with no purchase
order wait in the cage and are not entered.

## Ledgerline

Ledgerline is the general ledger. For this process the business user is Gwen Adler. She
keys one summary journal a day from the Paywindow proposal list. The fields she uses are
journal date, amount and a narrative she types herself. Ledgerline does not read
Paywindow. There is no scheduled post from Paywindow to Ledgerline.

## Helpline

Helpline is the internal request log. It is not a payment system. Fields are request id,
opened date, closed date, system, category and summary. Category is whatever the person
who opened the request typed. Helpline does not pay a supplier and does not change a
Paywindow status.

## Interfaces

Interfaces IT runs, and the manual steps IT is willing to name, are these. Gatepass
writes po-nightly.csv to a folder Dockhand reads. The job is scheduled. Owner: Jules
Fen. Dockhand writes receipts.csv. A person starts the import into Paywindow. It is not
scheduled. Samir Quill owns the file. The accounts payable clerks own the import step.
Paywindow has no scheduled post to Ledgerline. Gwen Adler keys the daily summary
journal. Helpline has no interface to the other four systems.

## Out of scope

Personal machines on desks or in cupboards are not production interfaces and are not
listed. Mail, including the shared mailbox invoices@acme.example, is not a system in
this inventory. The match log spreadsheet on the office share is owned by the accounts
payable clerks and is not a system in this inventory. Retired work is not listed.
Production and a rehearsal copy are the only environments. Rehearsal is refreshed on the
first Monday of the month and is not used to pay a supplier. The servers sit in the Mill
Road building. No outside software house is named on a row.
