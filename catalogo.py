CATALOGO = {
    "HP": ["ELITEBOOK 840 G7", "PROBOOK 440 G9", "ZBOOK FURY 16 G11", "ELITEBOOK 8 G1"],
    "DELL": ["LATITUDE 5430", "PRECISION 7550", "POWEREDGE R640"],
    "LENOVO": ["THINKPAD T14 G4", "THINKCENTRE M70Q G5"],
    "CISCO": ["CATALYST 9300", "ASA 5515", "FIREPOWER 2110"],
    "SAMSUNG": ["C24F390", "GALAXY TAB ACTIVE 4"],
    "LG": ["27UD59-B", "24MK430H"],
    "FORTINET": ["FORTIGATE 100F", "FORTIGATE 300E"],
    "VMWARE": ["VIRTUAL MACHINE"],
    "AMAZON": ["EC2 R5", "EC2 T3"],
    "GENERICO": ["SWITCH", "ROUTER", "SERVIDOR"]
}

def obtener_catalogo(tipo: str):
    if tipo == "marca":
        return list(CATALOGO.keys())
    elif tipo == "modelo":
        modelos = []
        for modelos_list in CATALOGO.values():
            modelos.extend(modelos_list)
        return modelos
    else:
        return []
