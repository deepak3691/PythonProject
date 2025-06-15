import os
import random
from faker import Faker
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()

# Output directory
OUTPUT_DIR = 'generated_camt053_001_02'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper functions
def random_decimal():
    return str(round(random.uniform(100, 10000), 2))

def random_currency():
    return random.choice(['USD', 'EUR', 'INR', 'GBP', 'JPY'])

def random_date():
    return (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")

def random_datetime():
    return (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%dT%H:%M:%S")

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

# Main generator function
def create_camt053_001_02_xml(file_number, entries_per_stmt=2):
    Document = ET.Element('Document', xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02")
    BkToCstmrStmt = ET.SubElement(Document, 'BkToCstmrStmt')

    # GrpHdr
    GrpHdr = ET.SubElement(BkToCstmrStmt, 'GrpHdr')
    ET.SubElement(GrpHdr, 'MsgId').text = fake.uuid4()
    ET.SubElement(GrpHdr, 'CreDtTm').text = random_datetime()

    if random.choice([True, False]):
        MsgRcpt = ET.SubElement(GrpHdr, 'MsgRcpt')
        ET.SubElement(MsgRcpt, 'Nm').text = fake.name()
        Id = ET.SubElement(MsgRcpt, 'Id')
        OrgId = ET.SubElement(Id, 'OrgId')
        Othr = ET.SubElement(OrgId, 'Othr')
        ET.SubElement(Othr, 'Id').text = fake.uuid4()

    # One or more statements
    for stmt_index in range(random.randint(1, 2)):
        Stmt = ET.SubElement(BkToCstmrStmt, 'Stmt')
        ET.SubElement(Stmt, 'Id').text = fake.uuid4()
        ET.SubElement(Stmt, 'ElctrncSeqNb').text = str(random.randint(1, 1000))
        ET.SubElement(Stmt, 'LglSeqNb').text = str(random.randint(1, 1000))
        ET.SubElement(Stmt, 'CreDtTm').text = random_datetime()

        if random.choice([True, False]):
            FrToDt = ET.SubElement(Stmt, 'FrToDt')
            ET.SubElement(FrToDt, 'FrDtTm').text = random_datetime()
            ET.SubElement(FrToDt, 'ToDtTm').text = random_datetime()

        Acct = ET.SubElement(Stmt, 'Acct')
        Id = ET.SubElement(Acct, 'Id')
        Othr = ET.SubElement(Id, 'Othr')
        ET.SubElement(Othr, 'Id').text = fake.uuid4()
        Tp = ET.SubElement(Acct, 'Tp')
        ET.SubElement(Tp, 'Prtry').text = fake.word()
        ET.SubElement(Acct, 'Ccy').text = random_currency()
        ET.SubElement(Acct, 'Nm').text = fake.name()

        Svcr = ET.SubElement(Acct, 'Svcr')
        FinInstnId = ET.SubElement(Svcr, 'FinInstnId')
        if random.choice([True, False]):
            ET.SubElement(FinInstnId, 'BIC').text = fake.swift()
        if random.choice([True, False]):
            ET.SubElement(FinInstnId, 'Nm').text = fake.company()

        for _ in range(random.randint(1, 2)):
            Bal = ET.SubElement(Stmt, 'Bal')
            Tp = ET.SubElement(Bal, 'Tp')
            CdOrPrtry = ET.SubElement(Tp, 'CdOrPrtry')
            ET.SubElement(CdOrPrtry, 'Cd').text = fake.word()
            Amt = ET.SubElement(Bal, 'Amt', Ccy=random_currency())
            Amt.text = random_decimal()
            ET.SubElement(Bal, 'CdtDbtInd').text = random.choice(['CRDT', 'DBIT'])
            Dt = ET.SubElement(Bal, 'Dt')
            ET.SubElement(Dt, 'DtTm').text = random_datetime()

        if random.choice([True, False]):
            TxsSummry = ET.SubElement(Stmt, 'TxsSummry')
            TtlNtries = ET.SubElement(TxsSummry, 'TtlNtries')
            ET.SubElement(TtlNtries, 'NbOfNtries').text = str(random.randint(1, 10))
            ET.SubElement(TtlNtries, 'Sum').text = random_decimal()
            ET.SubElement(TtlNtries, 'TtlNetNtryAmt').text = random_decimal()
            ET.SubElement(TtlNtries, 'CdtDbtInd').text = random.choice(['CRDT', 'DBIT'])

            if random.choice([True, False]):
                TtlCdtNtries = ET.SubElement(TxsSummry, 'TtlCdtNtries')
                ET.SubElement(TtlCdtNtries, 'NbOfNtries').text = str(random.randint(1, 10))
                ET.SubElement(TtlCdtNtries, 'Sum').text = random_decimal()

            if random.choice([True, False]):
                TtlDbtNtries = ET.SubElement(TxsSummry, 'TtlDbtNtries')
                ET.SubElement(TtlDbtNtries, 'NbOfNtries').text = str(random.randint(1, 10))
                ET.SubElement(TtlDbtNtries, 'Sum').text = random_decimal()

        for _ in range(entries_per_stmt):
            Ntry = ET.SubElement(Stmt, 'Ntry')
            ET.SubElement(Ntry, 'NtryRef').text = fake.uuid4()
            Amt = ET.SubElement(Ntry, 'Amt', Ccy=random_currency())
            Amt.text = random_decimal()
            ET.SubElement(Ntry, 'CdtDbtInd').text = random.choice(['CRDT', 'DBIT'])
            ET.SubElement(Ntry, 'RvslInd').text = random.choice(['true', 'false'])
            ET.SubElement(Ntry, 'Sts').text = random.choice(['BOOK', 'PDNG', 'RCVD'])
            BookgDt = ET.SubElement(Ntry, 'BookgDt')
            ET.SubElement(BookgDt, 'DtTm').text = random_datetime()
            ValDt = ET.SubElement(Ntry, 'ValDt')
            ET.SubElement(ValDt, 'Dt').text = random_date()

            # Placeholders for optional anyType fields
            if random.choice([True, False]):
                ET.SubElement(Ntry, 'BkTxCd')
            if random.choice([True, False]):
                ET.SubElement(Ntry, 'NtryDtls')

    indent(Document)
    tree = ET.ElementTree(Document)
    filename = os.path.join(OUTPUT_DIR, f'camt053_001_02_{file_number}.xml')
    tree.write(filename, encoding='utf-8', xml_declaration=True)
    print(f'Generated file: {filename}')

# Configurable run
NUMBER_OF_FILES = 1
ENTRIES_PER_FILE = 1

for i in range(1, NUMBER_OF_FILES + 1):
    create_camt053_001_02_xml(i, entries_per_stmt=ENTRIES_PER_FILE)
