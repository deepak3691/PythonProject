import random
import uuid
from datetime import datetime, timedelta
from lxml import etree

# ---------------------- Utility Functions ----------------------

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

NSMAP = {None: "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"}

# ---------------------- Element Generators ----------------------

def create_grp_hdr():
    grp_hdr = etree.Element("GrpHdr")
    etree.SubElement(grp_hdr, "MsgId").text = str(random.randint(10000, 999999))
    etree.SubElement(grp_hdr, "CreDtTm").text = datetime.utcnow().isoformat()
    msg_rcpt = etree.SubElement(grp_hdr, "MsgRcpt")
    etree.SubElement(msg_rcpt, "Nm").text = "ReceiverName"
    etree.SubElement(etree.SubElement(etree.SubElement(etree.SubElement(msg_rcpt, "Id"), "OrgId"), "Othr"), "Id").text = str(uuid.uuid4())
    return grp_hdr

def create_stmt():
    stmt = etree.Element("Stmt")
    etree.SubElement(stmt, "Id").text = str(random.randint(10000, 999999))
    etree.SubElement(stmt, "ElctrncSeqNb").text = str(random.randint(1, 100))
    etree.SubElement(stmt, "LglSeqNb").text = str(random.randint(1, 100))
    etree.SubElement(stmt, "CreDtTm").text = datetime.utcnow().isoformat()

    fr_to_dt = etree.SubElement(stmt, "FrToDt")
    fr_date = random_date()
    to_date = fr_date + timedelta(days=10)
    etree.SubElement(fr_to_dt, "FrDtTm").text = fr_date.isoformat()
    etree.SubElement(fr_to_dt, "ToDtTm").text = to_date.isoformat()

    acct = etree.SubElement(stmt, "Acct")
    etree.SubElement(etree.SubElement(acct, "Id"), "IBAN").text = gen_iban()
    etree.SubElement(etree.SubElement(acct, "Tp"), "Prtry").text = "Current"
    etree.SubElement(acct, "Ccy").text = random_currency()
    etree.SubElement(acct, "Nm").text = "AccountHolder"
    fin_inst = etree.SubElement(etree.SubElement(acct, "Svcr"), "FinInstnId")
    etree.SubElement(fin_inst, "BICFI").text = gen_bic()
    etree.SubElement(fin_inst, "Nm").text = "BankName"

    return stmt

def create_bal():
    bal = etree.Element("Bal")
    tp = etree.SubElement(bal, "Tp")
    cd = etree.SubElement(tp, "CdOrPrtry")
    etree.SubElement(cd, "Cd").text = "CLBD"
    amt = etree.SubElement(bal, "Amt", Ccy=random_currency())
    amt.text = str(gen_decimal())
    etree.SubElement(bal, "CdtDbtInd").text = random.choice(["CRDT", "DBIT"])
    dt = etree.SubElement(bal, "Dt")
    etree.SubElement(dt, "DtTm").text = datetime.utcnow().isoformat()
    return bal

def create_ntry():
    ntry = etree.Element("Ntry")
    etree.SubElement(ntry, "NtryRef").text = str(random.randint(100000, 999999))
    etree.SubElement(ntry, "Amt", Ccy=random_currency()).text = str(gen_decimal())
    etree.SubElement(ntry, "CdtDbtInd").text = random.choice(["CRDT", "DBIT"])
    etree.SubElement(ntry, "RvslInd").text = "false"
    etree.SubElement(etree.SubElement(ntry, "Sts"), "Cd").text = "BOOK"
    etree.SubElement(etree.SubElement(ntry, "BookgDt"), "DtTm").text = datetime.utcnow().isoformat()
    etree.SubElement(etree.SubElement(ntry, "ValDt"), "Dt").text = datetime.utcnow().date().isoformat()

    # BkTxCd
    bk_tx_cd = etree.SubElement(ntry, "BkTxCd")
    domn = etree.SubElement(bk_tx_cd, "Domn")
    etree.SubElement(domn, "Cd").text = "PMNT"
    fmly = etree.SubElement(domn, "Fmly")
    etree.SubElement(fmly, "Cd").text = "ICDT"
    etree.SubElement(fmly, "SubFmlyCd").text = "DMCT"
    prtry = etree.SubElement(bk_tx_cd, "Prtry")
    etree.SubElement(prtry, "Cd").text = "XYZ123"

    # NtryDtls
    ntry_dtls = etree.SubElement(ntry, "NtryDtls")
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
    etree.SubElement(tx_dtls, "AddtlTxInf").text = "Payment for invoice"

    return ntry

# ---------------------- Nested Structure Generator ----------------------

TAG_CREATORS = {
    "Stmt": create_stmt,
    "Bal": create_bal,
    "Ntry": create_ntry,
    # Add more tag generators if needed
}

def populate_structure(parent, structure):
    for tag_name, tag_info in structure.items():
        count = tag_info.get("count", 1)
        children = tag_info.get("children", {})

        for _ in range(count):
            if tag_name not in TAG_CREATORS:
                raise ValueError(f"Unsupported tag: {tag_name}")
            element = TAG_CREATORS[tag_name]()
            if children:
                populate_structure(element, children)
            parent.append(element)

def generate_nested_xml(structure):
    doc = etree.Element("Document", nsmap=NSMAP)
    bk_to_cust_stmt = etree.SubElement(doc, "BkToCstmrStmt")

    # Always add GrpHdr
    bk_to_cust_stmt.append(create_grp_hdr())

    # Add nested elements according to the structure
    populate_structure(bk_to_cust_stmt, structure)

    return etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding="UTF-8")

# ---------------------- Usage Example ----------------------

if __name__ == "__main__":
    structure = {
        "Stmt": {
            "count": 2,
            "children": {
                "Bal": {"count": 2},
                "Ntry": {"count": 3}
            }
        }
    }

    xml_output = generate_nested_xml(structure)

    with open("camt053_nested_final.xml", "wb") as f:
        f.write(xml_output)

    print("✅ XML generated successfully with nested tags.")
