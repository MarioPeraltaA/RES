"""Data processor and shaper of Energy Matrix Balance.

This module integrates the Latin America and Caribbean
Energy Matrix Balance and sort out its data in a
OSeMOSYS model structure.

Note: According to the naming convention used by OSeMOSYS
a 3-letter country abbreviation will be adopted and added
at the tail of the code (label) as follows:

    [category][sector][fuel/commodity][###][region]

e.g. for "Crude oil extraction" kind of technology in
"Argentina" the generic convention label is: ``MINOILARG``

Author: Mario R. Peralta. A.
School of Electrical Engineering, University of Costa Rica.
The Electric Power and Energy Research Laboratory (EPERLab) 

"""
import pandas as pd


class Commodity():

    def __init__(self, code: str, energy: float):
        self.code = code
        self.energy_PJ = energy

    def __repr__(self) -> str:
        return f"{self.code}"


class In_Commodity(Commodity):
    def __init__(self, code: str, energy: float):
        super().__init__(code, energy)


class Out_Commodity(Commodity):
    def __init__(self, code: str, energy: float):
        super().__init__(code, energy)


class Technology():

    def __init__(self, code: str, output_commodity: Commodity):
        self.code = code
        self.output_commodity = output_commodity

    def __repr__(self) -> str:
        return f"{self.code}"


class Primary_Tech(Technology):

    def __init__(self, label, output_commodity):
        super().__init__(label, output_commodity)


class Secondary_Tech(Technology):

    def __init__(self,
                 label: str,
                 input_commodity: Commodity,
                 output_commodity: Commodity):
        super().__init__(label, output_commodity)
        self.input_commodity = input_commodity


class EnergyMatrix():

    def __init__(self):
        self.matrix = {}      # Data
        self.commodities = []
        self.technologies = []

    def read_data(self, path: str) -> dict:
        """Read Energetic Balance Matrix data.

        It gives string format to commodities (fields)
        and sectors (register).

        """
        dict_df = pd.read_excel(path, sheet_name=None)
        # Set new columns header
        for matrix_df in dict_df.values():
            matrix_df.columns = matrix_df.iloc[3]
            # Replace NaN values in fields by "Sectors"
            matrix_df.columns = matrix_df.columns.fillna("Sectors")
            # In register by "Unit"
            matrix_df["Sectors"] = matrix_df["Sectors"].fillna("Unit")
            # Remove white space in field
            matrix_df.columns = matrix_df.columns.str.strip()
            # Remove white space in register
            matrix_df["Sectors"] = matrix_df["Sectors"].str.strip()
            # Replace np.NaN obj for 0.0 float type
            matrix_df.fillna(0.0, inplace=True)

        self.matrix = dict_df
        return dict_df

    def add_in_commodity(self, code, energy) -> Commodity:
        comm = In_Commodity(code, energy)
        self.commodities.append(comm)
        return comm

    def add_out_commodity(self, code, energy) -> Commodity:
        comm = Out_Commodity(code, energy)
        self.commodities.append(comm)
        return comm

    def add_prim_tech(self, label, output_commodity) -> Technology:
        prim_tech = Primary_Tech(label, output_commodity)
        self.technologies.append(prim_tech)
        return prim_tech

    def add_sec_tech(self,
                     label,
                     input_commodity,
                     output_commodity) -> Technology:
        sec_tech = Secondary_Tech(label, input_commodity, output_commodity)
        self.technologies.append(sec_tech)
        return sec_tech

    def build_RES(self, path: str) -> None:
        dict_df = self.read_data(path=path)
        # Iterate over data
        for country, matrix_df in dict_df.items():
            # Regions
            name_region = country.strip().split(" - ")[1]
            label_region = set_region(name_region)
            # Commodities, Technology and its Codes
            for comm in matrix_df.columns:
                comm_label = set_commodity_labels(comm)
                if comm_label:
                    _, comm_code = comm_label
                    # Commodity code
                    comm_c = f"{comm_code}{label_region}"
                    for n, r in enumerate(matrix_df["Sectors"]):
                        t_label = set_technology_labels(r)
                        if t_label:
                            cat, tech_code = t_label
                            if (cat == "SUP" and type(tech_code) is list):
                                if comm_code == "ELC":
                                    tech_code = tech_code[1]    # PWR
                                else:
                                    tech_code = tech_code[0]    # MIN
                            # Technology code
                            tech_c = f"{tech_code}{comm_c}"
                            # Energy in PJ
                            energy = matrix_df[comm][n]
                            # Creat and add instances
                            if cat == "SUP":
                                C = self.add_out_commodity(comm_c, energy)
                                _ = self.add_prim_tech(tech_c, C)
                            elif cat == "WAS":
                                waste_tech = [w for w in self.technologies
                                                if (isinstance(w, Primary_Tech)
                                                    and w.code == tech_c)]
                                # Update instance
                                if waste_tech:
                                    w_t = waste_tech[0]
                                    w_t.output_commodity.energy_PJ += energy
                                # Creat instance
                                else:
                                    C = self.add_out_commodity(comm_c, energy)
                                    _ = self.add_prim_tech(tech_c, C)
                            else:
                                # Creat and add instance
                                Cin = self.add_in_commodity(comm_c, energy)
                                Cout = self.add_out_commodity(comm_c, -energy)
                                _ = self.add_sec_tech(tech_c, Cin, Cout)
                        else:
                            continue
                else:
                    continue


def set_region(country: str) -> str:
    """Set regions name up.

    Region
    ------
    regions = {
        "Argentina": "ARG",
        "Barbados": "BRB",
        "Belice": "BLZ",
        "Bolivia": "BOL",
        "Brasil": "BRA",
        "Chile": "CHL",
        "Colombia": "COL",
        "Costa Rica": "CRI",
        "Cuba": "CUB",
        "Ecuador": "ECU",
        "El Salvador": "SLV",
        "Grenada": "GRD",
        "Guatemala": "GTM",
        "Guyana": "GUY",
        "Haiti": "HTI",
        "Honduras": "HND",
        "Jamaica": "JAM",
        "México": "MEX",
        "Nicaragua": "NIC",
        "Panamá": "PAN",
        "Paraguay": "PRY",
        "Perú": "PER",
        "República Dominicana": "DOM",
        "Suriname": "SUR",
        "Trinidad & Tobago": "TTO",
        "Uruguay": "URY",
        "Venezuela": "VEN"
    }

    """
    region = {
        "Argentina": "ARG",
        "Barbados": "BRB",
        "Belice": "BLZ",
        "Bolivia": "BOL",
        "Brasil": "BRA",
        "Chile": "CHL",
        "Colombia": "COL",
        "Costa Rica": "CRI",
        "Cuba": "CUB",
        "Ecuador": "ECU",
        "El Salvador": "SLV",
        "Grenada": "GRD",
        "Guatemala": "GTM",
        "Guyana": "GUY",
        "Haiti": "HTI",
        "Honduras": "HND",
        "Jamaica": "JAM",
        "México": "MEX",
        "Nicaragua": "NIC",
        "Panamá": "PAN",
        "Paraguay": "PRY",
        "Perú": "PER",
        "República Dominicana": "DOM",
        "Suriname": "SUR",
        "Trinidad & Tobago": "TTO",
        "Uruguay": "URY",
        "Venezuela": "VEN"
    }
    if country in region:
        return region[country]
    else:
        return False


def set_commodity_labels(name: str) -> tuple:
    """Set OSeMOSYS commodity naming convention.

    It replaces the name of commodity for three-letter label
    so that the OSeMOSYS code naming can be set up.

    """
    # Commodity
    # ---------
    fuel_labels = {
        "Sector": "Fuel",
        "PETRÓLEO": "CRU",
        "GAS NATURAL": "NGS",
        "CARBÓN MINERAL": "COA001",
        "HIDROENERGÍA": "HYD",
        "GEOTERMIA": "GEO",
        "NUCLEAR": "NUC",
        "LEÑA": "WOO",
        "CAÑA DE AZÚCAR Y DERIVADOS": "SGC",
        "OTRAS PRIMARIAS": "OPR"
    }

    commodity_labels = {
        "Sector": "Commodity",
        "ELECTRICIDAD": "ELC",
        "GAS LICUADO DE PETRÓLEO": "OHC",    # Other hydrocarbons
        "GASOLINA/ALCOHOL": "GSL",
        "KEROSENE/JET FUEL": "KER",
        "DIÉSEL OIL": "DSL",
        "FUEL OIL": "HFO",
        "COQUE": "COK",
        "CARBÓN VEGETAL": "COA002",
        "GASES": "GAS",
        "OTRAS SECUNDARIAS": "OSE",
        "NO ENERGÉTICO": "NEN"
    }
    commodities = [fuel_labels, commodity_labels]
    for c in commodities:
        if name in c:
            return (c["Sector"], c[name])
        else:
            continue
    return False


def set_technology_labels(name: str) -> str:
    """Set OSeMOSYS technology naming convention.

    It replaces the name of sector or technology
    for three-letter label so that the OSeMOSYS
    code naming can be set up.

    Note: Final demand category would not be considered since is
    the sum of Energetic and Non-energetic demand.
    Note: These losses sectors will be considere the same
    sort of :py:class:`Primary_Tech` technology whose:

    {
        "VARIACIÓN DE INVENTARIOS",
        "NO APROVECHADO",
        "PÉRDIDAS",
        "CONSUMO PROPIO"
    }
    whose category will be WAS: waste, and commodity a
    :py:class:`Out_Commodity` kind.

    """
    # Supply category
    # ---------------
    supply = {
        "Category": "SUP",
        "PRODUCCIÓN": ["MIN", "PWR"],
        "IMPORTACIÓN": "IMP",
        "EXPORTACIÓN": "EXP"
    }

    # Transformation
    # --------------
    # Conversion technology
    conversion_tech = {
        "Category": "UPS",
        "REFINERÍAS": "UPSREF",
        "CENTRALES ELÉCTRICAS": "UPSPWR",
        "AUTOPRODUCTORES": "UPSSEL",
        "CENTROS DE GAS": "UPSGAS",
        "CARBONERA": "UPSCOA",
        "COQUERÍA Y ALTOS HORNOS": "UPSBOI",
        "DESTILERÍA" : "UPSDET",
        "OTROS CENTROS": "UPSTEC"
    }

    # Energy demand category
    # ----------------------
    demand = {
        "Category": "DEM",
        "TRANSPORTE": "DEMTRA",
        "INDUSTRIAL": "DEMIND",
        "RESIDENCIAL": "DEMRES",
        "COMERCIAL, SERVICIOS, PÚBLICO": "DEMCOM",
        "AGRO, PESCA Y MINERÍA": "DEMAGR",
        "CONSTRUCCIÓN Y OTROS": "DEMCON",
        "CONSUMO NO ENERGÉTICO": "DEMNEE"
    }

    # Waste technology
    # ----------------
    waste_tech = {
        "Category": "WAS",
        "VARIACIÓN DE INVENTARIOS": "WASTEC",
        "NO APROVECHADO": "WASTEC",
        "PÉRDIDAS": "WASTEC",
        "CONSUMO PROPIO": "WASTEC"
    }

    categories = [
        supply,
        conversion_tech,
        demand,
        waste_tech
    ]

    for c in categories:
        if name in c:
            return (c["Category"], c[name])
        else:
            continue
    return False


if __name__ == "__main__":
    matrix = EnergyMatrix()
    matrix.build_RES("./data/matrix.xlsx")
