import os
import random
from faker import Faker
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd

# Initialize Faker
fake = Faker()

# Output directory
OUTPUT_DIR = 'generated_camt053_001_02'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper functions
def random_decimal(): return str(round(random.uniform(100, 10000), 2))
def random_currency(): return random.choice(['USD', 'EUR', 'INR', 'GBP', 'JPY'])
def random_date(): return (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
def random_datetime(): return (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%dT%H:%M:%S")
def random_boolean(): return random.choice(['true', 'false'])
def random_status(): return random.choice(['BOOK', 'PDNG', 'RCVD'])

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def get_value(row, key, generator):
    value = row.get(key)
    return value if pd.notna(value) and value != '' else generator()

def generate_full_from_excel(excel_path):
    df = pd.read_excel(excel_path)
    for index, row in df.iterrows():
        scenario = row['Scenario']
        Document = ET.Element('Document', xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02")
        BkToCstmrStmt = ET.SubElement(Document, 'BkToCstmrStmt')

        # GrpHdr
        GrpHdr = ET.SubElement(BkToCstmrStmt, 'GrpHdr')
        ET.SubElement(GrpHdr, 'MsgId').text = str(get_value(row, 'MsgId', fake.uuid4))
        ET.SubElement(GrpHdr, 'CreDtTm').text = str(get_value(row, 'CreDtTm', random_datetime))

        # MsgRcpt (optional)
        if 'MsgRcptNm' in row or 'MsgRcptId' in row:
            MsgRcpt = ET.SubElement(GrpHdr, 'MsgRcpt')
            ET.SubElement(MsgRcpt, 'Nm').text = str(get_value(row, 'MsgRcptNm', fake.name))
            Id = ET.SubElement(MsgRcpt, 'Id')
            OrgId = ET.SubElement(Id, 'OrgId')
            Othr = ET.SubElement(OrgId, 'Othr')
            ET.SubElement(Othr, 'Id').text = str(get_value(row, 'MsgRcptId', fake.uuid4))

        # Stmt
        Stmt = ET.SubElement(BkToCstmrStmt, 'Stmt')
        ET.SubElement(Stmt, 'Id').text = str(get_value(row, 'StmtId', fake.uuid4))
        ET.SubElement(Stmt, 'ElctrncSeqNb').text = str(get_value(row, 'ElctrncSeqNb', lambda: random.randint(1, 1000)))
        ET.SubElement(Stmt, 'LglSeqNb').text = str(get_value(row, 'LglSeqNb', lambda: random.randint(1, 1000)))
        ET.SubElement(Stmt, 'CreDtTm').text = str(get_value(row, 'StmtCreDtTm', random_datetime))

        FrToDt = ET.SubElement(Stmt, 'FrToDt')
        ET.SubElement(FrToDt, 'FrDtTm').text = str(get_value(row, 'FrDtTm', random_datetime))
        ET.SubElement(FrToDt, 'ToDtTm').text = str(get_value(row, 'ToDtTm', random_datetime))

        Acct = ET.SubElement(Stmt, 'Acct')
        Id = ET.SubElement(Acct, 'Id')
        Othr = ET.SubElement(Id, 'Othr')
        ET.SubElement(Othr, 'Id').text = str(get_value(row, 'AcctId', fake.uuid4))
        Tp = ET.SubElement(Acct, 'Tp')
        ET.SubElement(Tp, 'Prtry').text = str(get_value(row, 'AcctPrtry', fake.word))
        ET.SubElement(Acct, 'Ccy').text = str(get_value(row, 'AcctCcy', random_currency))
        ET.SubElement(Acct, 'Nm').text = str(get_value(row, 'AcctNm', fake.name))

        Svcr = ET.SubElement(Acct, 'Svcr')
        FinInstnId = ET.SubElement(Svcr, 'FinInstnId')
        ET.SubElement(FinInstnId, 'BIC').text = str(get_value(row, 'BIC', fake.swift))
        ET.SubElement(FinInstnId, 'Nm').text = str(get_value(row, 'FinNm', fake.company))

        # Bal
        Bal = ET.SubElement(Stmt, 'Bal')
        Tp = ET.SubElement(Bal, 'Tp')
        CdOrPrtry = ET.SubElement(Tp, 'CdOrPrtry')
        ET.SubElement(CdOrPrtry, 'Cd').text = str(get_value(row, 'BalTpCd', fake.word))
        Amt = ET.SubElement(Bal, 'Amt', Ccy=str(get_value(row, 'BalAmtCcy', random_currency)))
        Amt.text = str(get_value(row, 'BalAmt', random_decimal))
        ET.SubElement(Bal, 'CdtDbtInd').text = str(get_value(row, 'BalCdtDbtInd', lambda: random.choice(['CRDT', 'DBIT'])))
        Dt = ET.SubElement(Bal, 'Dt')
        ET.SubElement(Dt, 'DtTm').text = str(get_value(row, 'BalDt', random_datetime))

        # TxsSummry
        TxsSummry = ET.SubElement(Stmt, 'TxsSummry')
        TtlNtries = ET.SubElement(TxsSummry, 'TtlNtries')
        ET.SubElement(TtlNtries, 'NbOfNtries').text = str(get_value(row, 'TtlNtriesNbOfNtries', lambda: random.randint(1, 10)))
        ET.SubElement(TtlNtries, 'Sum').text = str(get_value(row, 'TtlNtriesSum', random_decimal))
        ET.SubElement(TtlNtries, 'TtlNetNtryAmt').text = str(get_value(row, 'TtlNtriesTtlNetNtryAmt', random_decimal))
        ET.SubElement(TtlNtries, 'CdtDbtInd').text = str(get_value(row, 'TtlNtriesCdtDbtInd', lambda: random.choice(['CRDT', 'DBIT'])))

        TtlCdtNtries = ET.SubElement(TxsSummry, 'TtlCdtNtries')
        ET.SubElement(TtlCdtNtries, 'NbOfNtries').text = str(get_value(row, 'TtlCdtNtriesNbOfNtries', lambda: random.randint(1, 10)))
        ET.SubElement(TtlCdtNtries, 'Sum').text = str(get_value(row, 'TtlCdtNtriesSum', random_decimal))

        TtlDbtNtries = ET.SubElement(TxsSummry, 'TtlDbtNtries')
        ET.SubElement(TtlDbtNtries, 'NbOfNtries').text = str(get_value(row, 'TtlDbtNtriesNbOfNtries', lambda: random.randint(1, 10)))
        ET.SubElement(TtlDbtNtries, 'Sum').text = str(get_value(row, 'TtlDbtNtriesSum', random_decimal))

        # Ntry
        Ntry = ET.SubElement(Stmt, 'Ntry')
        ET.SubElement(Ntry, 'NtryRef').text = str(get_value(row, 'NtryRef', fake.uuid4))
        Amt = ET.SubElement(Ntry, 'Amt', Ccy=str(get_value(row, 'NtryAmtCcy', random_currency)))
        Amt.text = str(get_value(row, 'NtryAmt', random_decimal))
        ET.SubElement(Ntry, 'CdtDbtInd').text = str(get_value(row, 'NtryCdtDbtInd', lambda: random.choice(['CRDT', 'DBIT'])))
        ET.SubElement(Ntry, 'RvslInd').text = str(get_value(row, 'NtryRvslInd', lambda: random.choice(['true', 'false'])))
        ET.SubElement(Ntry, 'Sts').text = str(get_value(row, 'NtrySts', random_status))
        BookgDt = ET.SubElement(Ntry, 'BookgDt')
        ET.SubElement(BookgDt, 'DtTm').text = str(get_value(row, 'BookgDt', random_datetime))
        ValDt = ET.SubElement(Ntry, 'ValDt')
        ET.SubElement(ValDt, 'Dt').text = str(get_value(row, 'ValDt', random_date))

        indent(Document)
        tree = ET.ElementTree(Document)
        filename = os.path.join(OUTPUT_DIR, f'{scenario}.xml')
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        print(f'Generated: {filename}')

# Example usage:
generate_full_from_excel("camt053_full_template_with_data.xlsx")
