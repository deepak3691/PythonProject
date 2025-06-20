import random
import uuid
from datetime import datetime, timedelta
from lxml import etree

def random_date(start_year=2000, end_year=2030):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + (end - start) * random.random()

def random_currency():
    return random.choice(["EUR", "USD", "GBP", "INR", "JPY", "CHF"])

def gen_decimal(min_val=0.01, max_val=10000.00):
    return round(random.uniform(min_val, max_val), 2)

def gen_string(length=10):
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

def gen_iban():
    return "DE" + ''.join(random.choices("0123456789", k=20))

def gen_bic():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))

NSMAP = {
    None: "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"
}

def create_statement():
    stmt_elem = etree.Element("Stmt")
    etree.SubElement(stmt_elem, "Id").text = str(random.randint(10000, 999999))
    etree.SubElement(stmt_elem, "ElctrncSeqNb").text = str(random.randint(1, 100))
    etree.SubElement(stmt_elem, "LglSeqNb").text = str(random.randint(1, 100))
    etree.SubElement(stmt_elem, "CreDtTm").text = datetime.utcnow().isoformat()

    fr_to_dt = etree.SubElement(stmt_elem, "FrToDt")
    fr_date = random_date()
    to_date = fr_date + timedelta(days=10)
    etree.SubElement(fr_to_dt, "FrDtTm").text = fr_date.isoformat()
    etree.SubElement(fr_to_dt, "ToDtTm").text = to_date.isoformat()

    acct = etree.SubElement(stmt_elem, "Acct")
    etree.SubElement(etree.SubElement(acct, "Id"), "IBAN").text = gen_iban()
    etree.SubElement(etree.SubElement(acct, "Tp"), "Prtry").text = "Current"
    etree.SubElement(acct, "Ccy").text = random_currency()
    etree.SubElement(acct, "Nm").text = "AccountHolder"
    fin_inst = etree.SubElement(etree.SubElement(acct, "Svcr"), "FinInstnId")
    etree.SubElement(fin_inst, "BICFI").text = gen_bic()
    etree.SubElement(fin_inst, "Nm").text = "BankName"

    # Balances
    for _ in range(2):
        bal = etree.SubElement(stmt_elem, "Bal")
        cd = etree.SubElement(etree.SubElement(bal, "Tp"), "CdOrPrtry")
        etree.SubElement(cd, "Cd").text = "CLBD"
        amt = etree.SubElement(bal, "Amt", Ccy=random_currency())
        amt.text = str(gen_decimal())
        etree.SubElement(bal, "CdtDbtInd").text = random.choice(["CRDT", "DBIT"])
        dt = etree.SubElement(bal, "Dt")
        etree.SubElement(dt, "DtTm").text = datetime.utcnow().isoformat()

    # TxsSummry
    txs = etree.SubElement(stmt_elem, "TxsSummry")
    total_entries = etree.SubElement(txs, "TtlNtries")
    etree.SubElement(total_entries, "NbOfNtries").text = "5"
    etree.SubElement(total_entries, "Sum").text = str(gen_decimal())
    net = etree.SubElement(total_entries, "TtlNetNtry")
    etree.SubElement(net, "Amt").text = str(gen_decimal())
    etree.SubElement(net, "CdtDbtInd").text = "CRDT"
    for tag in ["TtlCdtNtries", "TtlDbtNtries"]:
        t = etree.SubElement(txs, tag)
        etree.SubElement(t, "NbOfNtries").text = "3"
        etree.SubElement(t, "Sum").text = str(gen_decimal())

    # Ntry
    entry = etree.SubElement(stmt_elem, "Ntry")
    etree.SubElement(entry, "NtryRef").text = str(random.randint(100000, 999999))
    etree.SubElement(entry, "Amt", Ccy=random_currency()).text = str(gen_decimal())
    etree.SubElement(entry, "CdtDbtInd").text = random.choice(["CRDT", "DBIT"])
    etree.SubElement(entry, "RvslInd").text = "false"
    etree.SubElement(etree.SubElement(entry, "Sts"), "Cd").text = "BOOK"
    etree.SubElement(etree.SubElement(entry, "BookgDt"), "DtTm").text = datetime.utcnow().isoformat()
    etree.SubElement(etree.SubElement(entry, "ValDt"), "Dt").text = datetime.utcnow().date().isoformat()

    bk_tx_cd = etree.SubElement(entry, "BkTxCd")
    domn = etree.SubElement(bk_tx_cd, "Domn")
    etree.SubElement(domn, "Cd").text = "PMNT"
    fmly = etree.SubElement(domn, "Fmly")
    etree.SubElement(fmly, "Cd").text = "ICDT"
    etree.SubElement(fmly, "SubFmlyCd").text = "DMCT"
    prtry = etree.SubElement(bk_tx_cd, "Prtry")
    etree.SubElement(prtry, "Cd").text = "XYZ123"

    # Entry Details
    ntry_dtls = etree.SubElement(entry, "NtryDtls")
    tx_dtls = etree.SubElement(ntry_dtls, "TxDtls")
    refs = etree.SubElement(tx_dtls, "Refs")
    etree.SubElement(refs, "AcctSvcrRef").text = gen_string(12)
    etree.SubElement(refs, "PmtInfId").text = gen_string(12)
    etree.SubElement(refs, "EndToEndId").text = gen_string(12)
    etree.SubElement(refs, "TxId").text = gen_string(12)

    amt_dtls = etree.SubElement(tx_dtls, "AmtDtls")
    for tag in ["InstdAmt", "TxAmt"]:
        tag_elem = etree.SubElement(amt_dtls, tag)
        amt = etree.SubElement(tag_elem, "Amt", Ccy=random_currency())
        amt.text = str(gen_decimal())

    parties = etree.SubElement(tx_dtls, "RltdPties")
    etree.SubElement(etree.SubElement(etree.SubElement(parties, "Cdtr"), "Pty"), "Nm").text = "CreditorName"
    etree.SubElement(etree.SubElement(etree.SubElement(parties, "Dbtr"), "Pty"), "Nm").text = "DebtorName"
    dbtr_acct = etree.SubElement(parties, "DbtrAcct")
    etree.SubElement(etree.SubElement(dbtr_acct, "Id"), "IBAN").text = gen_iban()
    etree.SubElement(dbtr_acct, "Nm").text = "DebtorAccount"

    agts = etree.SubElement(tx_dtls, "RltdAgts")
    etree.SubElement(etree.SubElement(etree.SubElement(agts, "CdtrAgt"), "FinInstnId"), "BICFI").text = gen_bic()
    etree.SubElement(etree.SubElement(etree.SubElement(agts, "DbtrAgt"), "FinInstnId"), "BICFI").text = gen_bic()

    rmt_inf = etree.SubElement(tx_dtls, "RmtInf")
    etree.SubElement(rmt_inf, "Ustrd").text = "Invoice 12345"
    strd = etree.SubElement(rmt_inf, "Strd")
    ref_inf = etree.SubElement(strd, "CdtrRefInf")
    tp = etree.SubElement(ref_inf, "Tp")
    etree.SubElement(tp, "Issr").text = "ISO"
    etree.SubElement(ref_inf, "Ref").text = gen_string(10)

    etree.SubElement(etree.SubElement(tx_dtls, "RltdDts"), "IntrBkSttlmDt").text = datetime.utcnow().date().isoformat()
    etree.SubElement(tx_dtls, "AddtlTxInf").text = "Additional info goes here"

    return stmt_elem

def generate_xml_with_statements(num_statements=1):
    doc = etree.Element("Document", nsmap=NSMAP)
    bk_to_cust_stmt = etree.SubElement(doc, "BkToCstmrStmt")

    # Header
    grp_hdr = etree.SubElement(bk_to_cust_stmt, "GrpHdr")
    etree.SubElement(grp_hdr, "MsgId").text = str(random.randint(10000, 999999))
    etree.SubElement(grp_hdr, "CreDtTm").text = datetime.utcnow().isoformat()
    msg_rcpt = etree.SubElement(grp_hdr, "MsgRcpt")
    etree.SubElement(msg_rcpt, "Nm").text = "ReceiverName"
    etree.SubElement(etree.SubElement(etree.SubElement(etree.SubElement(msg_rcpt, "Id"), "OrgId"), "Othr"), "Id").text = str(uuid.uuid4())

    # Add multiple Stmt entries
    for _ in range(num_statements):
        bk_to_cust_stmt.append(create_statement())

    return etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding="UTF-8")

# ==== Entry Point ====
if __name__ == "__main__":
    num = 5  # 🔁 Set your number of statements here
    with open("camt053_multi_stmt.xml", "wb") as f:
        f.write(generate_xml_with_statements(3))
