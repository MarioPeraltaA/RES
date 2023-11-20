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
The Electric Power and Energy Research Laboratory (EPERLab)
"""
import pandas as pd
import copy


class Technology():

    def __init__(self,
                 code: str,
                 region: str,
                 category: str):
        self.code = code
        self.region = region
        self.category = category

    def __repr__(self) -> str:
        r = self.region
        c = self.code
        cat = self.category
        return f"({cat}, {c}, {r})"


class Primary_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.out_fuels = []    # Primaries


class Supply_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str,
                 order: int):
        super().__init__(label, region, category)
        self.in_fuels = []
        self.out_fuels = []
        self.order = order


class Convertion_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.in_fuels = []
        self.out_fuels = []


class Demand_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.in_fuels = []


class Fuel():

    def __init__(self, code: str, energy: float):
        self.code = code
        self.energy_PJ = energy

    def __repr__(self) -> str:
        return f"{self.code}"


class Primary_Fuel(Fuel):

    def __init__(self, code: str, energy: float):
        super().__init__(code, energy)


class Second_Fuel(Fuel):

    def __init__(self, code: str, energy: float):
        super().__init__(code, energy)


class Third_Fuel(Fuel):

    def __init__(self, code: str, energy: float):
        super().__init__(code, energy)


class Supply_Fuel(Fuel):

    def __init__(self,
                 code: str,
                 energy: float,
                 order: int):
        super().__init__(code, energy)
        self.order = order


class EnergyMatrix():

    def __init__(self):
        self.matrix = {}      # Data
        self.techs = []
        self.fuels = []

    def read_data(self, path: str = "./data/matrix.xlsx") -> dict:
        """Read Energetic Balance Matrix data.

        It gives string format to commodities (fields)
        and sectors (register).

        """
        dict_df = pd.read_excel(path, sheet_name=None, header=4)
        # Set new columns header
        for matrix_df in dict_df.values():
            # Replace empty values in fields by "Sectors"
            matrix_df.rename(columns={"Unnamed: 0": "Sectors"}, inplace=True)
            # In register by "Unit"
            matrix_df["Sectors"] = matrix_df["Sectors"].fillna("Unit")
            # Remove white space in field
            matrix_df.columns = matrix_df.columns.str.strip()
            # Remove white space in register
            matrix_df["Sectors"] = matrix_df["Sectors"].str.strip()
            # Replace all np.NaN obj for 0.0 float type
            matrix_df.fillna(0.0, inplace=True)

        self.matrix = dict_df
        return dict_df

    def read_potential(self,
                       path: str = "./data/potential.xlsx") -> dict:
        """Read Potential Matrix data.

        It reads binary matrix:
            - ``1`` there is a likelihood the technology
              could describe the energy system under certain scenario.
            - ``0`` No chance whatsoever to somehow describe
              the energy system because of technical incompatibility.

        """
        dict_df = pd.read_excel(path, sheet_name=None, header=4)
        # Set new columns header
        for matrix_df in dict_df.values():
            # Replace empty values in fields by "Sectors"
            matrix_df.rename(columns={"Unnamed: 0": "Sectors"}, inplace=True)
            # In register by "Unit"
            matrix_df["Sectors"] = matrix_df["Sectors"].fillna("Unit")
            # Remove white space in field
            matrix_df.columns = matrix_df.columns.str.strip()
            # Remove white space in register
            matrix_df["Sectors"] = matrix_df["Sectors"].str.strip()
            # Replace all np.NaN obj for 0.0 float type
            matrix_df.fillna(0.0, inplace=True)

        self.matrix = dict_df
        return dict_df

    def add_prim_tech(self,
                      label,
                      region,
                      category) -> Primary_Tech:
        prim_tech = Primary_Tech(label, region, category)
        # Update system
        self.techs.append(prim_tech)
        return prim_tech

    def add_conv_tech(self,
                      label,
                      region,
                      category) -> Convertion_Tech:
        conv_tech = Convertion_Tech(label, region, category)
        self.techs.append(conv_tech)
        return conv_tech

    def add_demand_tech(self,
                        label,
                        region,
                        category) -> Demand_Tech:
        demand_tech = Demand_Tech(label, region, category)
        self.techs.append(demand_tech)
        return demand_tech

    def add_tech(self,
                 tech_code: str,
                 region: str,
                 category: str,
                 matrix_df: pd.DataFrame,
                 n: int) -> Technology:
        # Primary tech
        if category in {"SUP", "LOS001"}:
            tech = self.add_prim_tech(tech_code, region, category)
            # Add all output primary fuels to this same instance
            for field in matrix_df.columns:
                fuelID = set_fuel_labels(field)
                if not fuelID:
                    continue
                sector, fuel_code = fuelID
                if tech_code == "PRO" and sector in {"FUE002", "FUE003"}:
                    continue
                energy = matrix_df[field][n]
                if tech_code in {"EXP", "WAS"}:
                    energy = -energy    # Negative
                fuel = self.add_fuel(sector, fuel_code, energy)
                tech.out_fuels.append(fuel)

        # Convertion tech
        elif category in {"UPS001", "UPS002", "UPS003"}:
            tech = self.add_conv_tech(tech_code, region, category)
            for field in matrix_df.columns:
                fuelID = set_fuel_labels(field)
                if not fuelID:
                    continue
                sector, fuel_code = fuelID
                # Primary fuel as inputs only
                if category == "UPS001":
                    if sector == "FUE003":
                        continue
                    energy = matrix_df[field][n]
                    fuel = self.add_fuel(sector, fuel_code, energy)
                    # Input
                    if sector == "FUE001":
                        tech.in_fuels.append(fuel)
                    # Output
                    elif sector == "FUE002":
                        tech.out_fuels.append(fuel)

                elif category == "UPS002":
                    if sector == "FUE003":
                        continue
                    energy = matrix_df[field][n]
                    fuel = self.add_fuel(sector, fuel_code, energy)
                    tech.in_fuels.append(fuel)
                    if sector == "FUE002":
                        fuel = copy.deepcopy(fuel)
                        tech.out_fuels.append(fuel)

                elif category == "UPS003":
                    energy = matrix_df[field][n]
                    fuel = self.add_fuel(sector, fuel_code, energy)
                    if sector == "FUE003":
                        tech.out_fuels.append(fuel)
                    else:
                        tech.in_fuels.append(fuel)


        # Demand tech
        elif category in {"DEM", "LOS002"}:
            tech = self.add_demand_tech(tech_code, region, category)
            for field in matrix_df.columns:
                fuelID = set_fuel_labels(field)
                if not fuelID:
                    continue
                sector, fuel_code = fuelID
                energy = -matrix_df[field][n]   # Negative as input
                fuel = self.add_fuel(sector, fuel_code, energy)
                tech.in_fuels.append(fuel)

        return tech

    def add_prim_fuel(self, code, energy) -> Primary_Fuel:
        prim_fuel = Primary_Fuel(code, energy)
        self.fuels.append(prim_fuel)
        return prim_fuel

    def add_sec_fuel(self, code, energy) -> Second_Fuel:
        sec_fuel =  Second_Fuel(code, energy)
        self.fuels.append(sec_fuel)
        return sec_fuel

    def add_third_fuel(self, code, energy) -> Third_Fuel:
        third_fuel = Third_Fuel(code, energy)
        self.fuels.append(third_fuel)
        return third_fuel

    def add_fuel(self,
                 sector: str,
                 fuel_code: str,
                 energy: float) -> Fuel:
        # Primary fuel
        if sector == "FUE001":
            fuel = self.add_prim_fuel(fuel_code, energy)
        # Second fuel
        elif sector == "FUE002":
            fuel = self.add_sec_fuel(fuel_code, energy)
        # Third fuel
        elif sector == "FUE003":
            fuel = self.add_third_fuel(fuel_code, energy)
        return fuel

    def add_supply_tech(self):
        pass

    def add_supply_fuel(self):
        pass

    def split_flow(self) -> None:
        """UPS002 input and output fuels.

        """
        techs = self.techs
        conv_techs = [t for t in techs if t.category == "UPS002"]
        for c in conv_techs:
            for f in c.in_fuels:
                if f.energy_PJ > 0:
                    f.energy_PJ = 0
            for f in c.out_fuels:
                if f.energy_PJ < 0:
                    f.energy_PJ = 0

    def set_potential(self) -> list[Technology]:
        """Intances.

        Initial RES with space in memory for those
        technology that has some potential to describe
        somehow the energy system.

        """
        dict_df = self.read_potential()
        # Iterate over data
        for country, matrix_df in dict_df.items():
            region = country.split(" - ")[1]
            region = set_region(region)
            sectors = matrix_df["Sectors"]
            for n, tech in enumerate(sectors):
                techID = set_technology_labels(tech)
                if not techID:
                    continue
                category, tech_code = techID
                tech = self.add_tech(tech_code,
                                     region,
                                     category,
                                     matrix_df,
                                     n)
        # UPS002 flow
        self.split_flow()
        return self.techs


    def data_RES(self) -> list[Technology]:
        dict_df = self.read_data()
        # Iterate over data
        for country, matrix_df in dict_df.items():
            region = country.split(" - ")[1]
            region = set_region(region)
            sectors = matrix_df["Sectors"]
            for n, tech in enumerate(sectors):
                techID = set_technology_labels(tech)
                if not techID:
                    continue
                category, tech_code = techID
                tech = self.add_tech(tech_code,
                                     region,
                                     category,
                                     matrix_df,
                                     n)
        # UPS002 flow
        self.split_flow()
        return self.techs

    def build_RES(self, region: str) -> list[Technology]:
        # Allocate outpus of UPS{001, 002, 003}
        # Sign convention
        # Define supply nodes
        # Define supply fuels
        pass


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


def set_fuel_labels(name: str) -> tuple:
    """Set OSeMOSYS commodity naming convention.

    It replaces the name of commodity for three-letter label
    so that the OSeMOSYS code naming can be set up.

    """
    # Fuels
    # -----
    prim_fuel_labels = {
        "Sector": "FUE001",
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
    sec_fuel_labels = {
        "Sector": "FUE002",
        "GAS LICUADO DE PETRÓLEO": "LPG",
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
    third_fuel_labels = {
        "Sector": "FUE003",
        "ELECTRICIDAD": "ELC"
    }

    commodities = [prim_fuel_labels,
                   sec_fuel_labels,
                   third_fuel_labels]
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
    whose category will be ``LOS`` that stands for loss.

    """
    # Supply category
    # ---------------
    supply = {
        "Category": "SUP",
        "PRODUCCIÓN": "PRO",
        "IMPORTACIÓN": "IMP",
        "EXPORTACIÓN": "EXP"
    }

    # Transformation
    # --------------
    # Conversion technology
    sec_tech = {
        "Category": "UPS001",
        "REFINERÍAS": "REF",
        "CENTROS DE GAS": "GAS",
        "CARBONERA": "CHL",
        "DESTILERÍA": "DET"
    }
    third_tech = {
        "Category": "UPS002",
        "COQUERÍA Y ALTOS HORNOS": "BOI",
        "OTROS CENTROS": "UPSTEC"
    }
    fourth_tech = {
        "Category": "UPS003",
        "CENTRALES ELÉCTRICAS": "PWR",
        "AUTOPRODUCTORES": "SEL"
    }
    # Energy demand category
    # ----------------------
    demand = {
        "Category": "DEM",
        "TRANSPORTE": "TRA",
        "INDUSTRIAL": "IND",
        "RESIDENCIAL": "RES",
        "COMERCIAL, SERVICIOS, PÚBLICO": "COM",
        "AGRO, PESCA Y MINERÍA": "AGR",
        "CONSTRUCCIÓN Y OTROS": "CON",
        "CONSUMO NO ENERGÉTICO": "NEE"
    }

    # Loss technology
    # ----------------
    loss_tech01 = {
        "Category": "LOS001",
        "VARIACIÓN DE INVENTARIOS": "INV",
        "NO APROVECHADO": "WAS",
    }

    loss_tech02 = {
        "Category": "LOS002",
        "PÉRDIDAS": "LOS",
        "CONSUMO PROPIO": "OWN"
    }

    categories = [
        supply,
        sec_tech,
        third_tech,
        fourth_tech,
        demand,
        loss_tech01,
        loss_tech02
    ]

    for c in categories:
        if name in c:
            return (c["Category"], c[name])
        else:
            continue
    return False


if __name__ == "__main__":
    matrix = EnergyMatrix()
    matrix.RES_data("./data/matrix.xlsx")
